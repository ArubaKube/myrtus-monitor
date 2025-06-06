"""This module contains the implementation of the Node monitor service."""

import argparse
import asyncio
import logging
import sys

from pydantic import ValidationError

from monitor.core.node_monitor import NodeMonitor
from monitor.shared.config import LogLevel, NodeMonitorConfig
from monitor.shared.errors import MonitorBaseError
from monitor.shared.utils import cexit


def main():
    """Entrypoint for the Node monitor service."""
    args = _parse_args()
    try:
        config = NodeMonitorConfig(
            node_name=args.node_name,
            liqo_cluster_id=args.liqo_cluster_id,
            kb_endpoint=args.kb_endpoint,
            log_level=LogLevel[args.log_level],
            default_timeout=args.default_timeout,
            default_period=args.default_period,
            active_collectors=args.active_collectors,
            exclude_collectors=args.exclude_collectors,
        )

        # Configure logging based on the log level
        logging.basicConfig(
            level=config.log_level.value,
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
            liqo_cluster_id=config.liqo_cluster_id,
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
        description="Monitoring service, sends metrics to the resource registry.",
    )
    aparser = argparse.ArgumentParser(description="Monitor service configuration")

    aparser.add_argument(
        "-n",
        "--node-name",
        type=str,
        required=True,
        help="The name of the node being monitored.",
    )

    aparser.add_argument(
        "-c",
        "--liqo-cluster-id",
        type=str,
        required=True,
        help="The Liqo cluster ID where the node is running.",
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
