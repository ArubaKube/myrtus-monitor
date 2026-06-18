"""This module contains the implementation of the Node monitor service."""

import argparse
import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from kubernetes import client, config as k8s_config
from kubernetes.config.config_exception import ConfigException
from pydantic import ValidationError

from monitor.core.node_monitor import NodeMonitor
from monitor.node.config import NodeMonitorConfig
from monitor.shared.config import LogLevel, NodeType
from monitor.shared.errors import MonitorBaseError
from monitor.shared.utils import cexit

NODE_TYPE_LABEL = "myrtus.io/node-type"
KUBEEDGE_NODE_TYPE = "edge"
# ConfigException is raised for several distinct reasons (missing token file, missing
# cert, no service env vars at all, ...). Only this specific message indicates the
# KubeEdge symptom: edgecore exposes empty KUBERNETES_SERVICE_HOST/PORT env vars
# because it doesn't sync the kubernetes Service from the control plane.
KUBEEDGE_CONFIG_EXCEPTION_MESSAGE = "Service host/port is set but empty."


def _resolve_node_type(
    node_name: str, fallback: str, kubeedge_fallback: bool = False, timeout: int = 10
) -> str:
    """Return the node type from the node's label, falling back to the CLI arg.

    Reads the myrtus.io/node-type label from the Kubernetes node object so that
    the type can be changed at runtime without a Helm redeploy.

    KubeEdge edge nodes cannot load the in-cluster K8s config (their edgecore
    doesn't sync the kubernetes Service env vars from the control plane), so when
    kubeedge_fallback is enabled, that specific failure resolves to "edge" instead
    of falling through to the --node-type arg.
    """
    logging.info("Resolving node type for node '%s' (fallback=%s)", node_name, fallback)

    def _fetch() -> str | None:
        logging.debug("Loading in-cluster K8s config...")
        configuration = client.Configuration()
        k8s_config.load_incluster_config(client_configuration=configuration)
        # kubernetes-client >=36 stores the token under api_key['authorization'] but
        # auth_settings() looks for api_key['BearerToken'] — remap so the header is sent.
        if bearer := configuration.api_key.get('authorization'):
            configuration.api_key['BearerToken'] = bearer
        logging.debug("In-cluster config loaded, reading node '%s'...", node_name)
        with client.ApiClient(configuration) as api:
            labels = client.CoreV1Api(api).read_node(node_name, _request_timeout=timeout).metadata.labels or {}
        logging.debug("Node labels: %s", labels)
        return labels.get(NODE_TYPE_LABEL)

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        label_value = executor.submit(_fetch).result(timeout=timeout)
        if label_value:
            logging.info("node_type resolved from node label '%s': %s", NODE_TYPE_LABEL, label_value)
            return label_value
        logging.debug("Label '%s' not set on node '%s', using --node-type fallback", NODE_TYPE_LABEL, node_name)
    except FuturesTimeoutError:
        logging.warning("K8s node label lookup timed out after %ds, falling back to --node-type arg", timeout)
    except ConfigException as exc:
        if kubeedge_fallback and KUBEEDGE_CONFIG_EXCEPTION_MESSAGE in str(exc):
            logging.warning(
                "In-cluster K8s config unavailable (%s), assuming KubeEdge node, using node_type=%s",
                exc,
                KUBEEDGE_NODE_TYPE,
            )
            return KUBEEDGE_NODE_TYPE
        logging.warning("Could not load in-cluster K8s config (%s), falling back to --node-type arg", exc)
    except Exception as exc:
        logging.warning("Could not read node labels from K8s API (%s), falling back to --node-type arg", exc)
    finally:
        executor.shutdown(wait=False)
    return fallback


def main():
    """Entrypoint for the Node monitor service."""
    args = _parse_args()
    logging.basicConfig(level=LogLevel[args.log_level].value, force=True)
    try:
        config = NodeMonitorConfig(
            node_name=args.node_name,
            node_type=NodeType[
                args.node_type
                if args.skip_node_type_inference
                else _resolve_node_type(args.node_name, args.node_type, args.enable_kubeedge_fallback)
            ],
            liqo_cluster_id=args.liqo_cluster_id,
            kb_enabled=not args.kb_disabled,
            kb_endpoint=args.kb_endpoint,
            log_level=LogLevel[args.log_level],
            default_timeout=args.default_timeout,
            default_period=args.default_period,
            active_collectors=args.active_collectors,
            exclude_collectors=args.exclude_collectors,
        )

        asyncio.run(run_monitor(config))

    except ValidationError as e:
        cexit(f"Invalid parameters: {e}")
    except KeyboardInterrupt:
        logging.info("Monitor service interrupted by user.")  # noqa: LOG015
        sys.exit(0)


async def run_monitor(config: NodeMonitorConfig):
    """Run the monitor service with the provided configuration.

    Args:
        config (NodeMonitorConfig): The configuration for the monitor service.
    """
    logger = logging.getLogger(__name__)
    try:
        monitor = NodeMonitor(
            node_name=config.node_name,
            node_type=config.node_type,
            liqo_cluster_id=config.liqo_cluster_id,
            kb_enabled=config.kb_enabled,
            kb_endpoint=config.kb_endpoint,
            active_collectors=config.active_collectors,
            exclude_collectors=config.exclude_collectors,
        )
        await monitor.init()
        await monitor.start()
    except MonitorBaseError as e:
        logger.error(e)
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected error occurred")
        sys.exit(1)


def _parse_args():
    aparser = argparse.ArgumentParser(
        description="Node monitoring service, sends metrics to the resource registry.",
    )

    aparser.add_argument(
        "-n",
        "--node-name",
        type=str,
        required=True,
        help="The name of the node being monitored.",
    )

    aparser.add_argument(
        "-y",
        "--node-type",
        type=str,
        required=True,
        choices=[t.name for t in NodeType],
        help="The type of the node being monitored (cloud, fog, edge).",
    )

    aparser.add_argument(
        "--skip-node-type-inference",
        action="store_true",
        help=f"Skip node type inference from the '{NODE_TYPE_LABEL}' node label "
             "and use --node-type directly.",
    )

    aparser.add_argument(
        "--enable-kubeedge-fallback",
        action="store_true",
        help="If the node-type label lookup fails because the in-cluster K8s "
             "config has an empty service host/port (the standard symptom of "
             f"a KubeEdge edge node), use node_type={KUBEEDGE_NODE_TYPE} instead "
             "of falling back to --node-type. Other label lookup failures "
             "(timeouts, RBAC errors, missing token/cert files) still fall "
             "back to --node-type as usual.",
    )

    aparser.add_argument(
        "-c",
        "--liqo-cluster-id",
        type=str,
        required=True,
        help="The Liqo cluster ID where the node is running.",
    )

    aparser.add_argument(
        "-k",
        "--kb-disabled",
        action="store_true",
        help="Disable the Knowledge base integration.",
    )

    aparser.add_argument(
        "-e",
        "--kb-endpoint",
        type=str,
        required=True,
        help="The endpoint for the knowledge base service where metrics are pushed.",
    )

    aparser.add_argument(
        "-l",
        "--log-level",
        type=str,
        choices=[level.name for level in LogLevel],
        default=LogLevel.INFO.name,
        help="Log level for the monitor service.",
    )

    aparser.add_argument(
        "-t",
        "--default-timeout",
        type=int,
        default=60,
        help="The default scraping timeout in seconds. "
        "When expired the collector is considered failed.",
    )

    aparser.add_argument(
        "-p",
        "--default-period",
        type=int,
        default=60,
        help="The default scraping period in seconds. If not differently specified by the "
        "collector. A collector is executed every defautl period.",
    )

    collector_group = aparser.add_mutually_exclusive_group()
    collector_group.add_argument(
        "-a",
        "--active-collectors",
        type=str,
        nargs="*",
        default=[],
        help="List of active collectors to be used by the monitor service. When this option is "
        "used only the collectors specified here will be used.",
    )

    collector_group.add_argument(
        "-x",
        "--exclude-collectors",
        type=str,
        nargs="*",
        default=[],
        help="List of collectors to be excluded from the monitor service. "
        "When this options is used all the collectors but the ones specified here will be used.",
    )

    return aparser.parse_args()


if __name__ == "__main__":
    main()
