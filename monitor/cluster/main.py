"""This module contains the implementation of the Node monitor service."""

import argparse
import asyncio
import logging
import sys

from pydantic import ValidationError

from monitor.cluster.config import ClusterMonitorConfig
from monitor.core.cluster_monitor import ClusterMonitor
from monitor.shared.config import LogLevel
from monitor.shared.errors import MonitorBaseError
from monitor.shared.utils import cexit


def main():
    """Entrypoint for the cluster monitor service."""
    args = _parse_args()
    try:
        config = ClusterMonitorConfig(
            liqo_cluster_id=args.liqo_cluster_id,
            kb_endpoint=args.kb_endpoint,
            log_level=LogLevel[args.log_level],
            default_timeout=args.default_timeout,
            default_period=args.default_period,
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


async def run_monitor(config: ClusterMonitorConfig):
    """Run the monitor service with the provided configuration.

    Args:
        config (ClusterMonitorConfig): The configuration for the monitor service.
    """
    logger = logging.getLogger(__name__)
    try:
        monitor = ClusterMonitor(
            liqo_cluster_id=config.liqo_cluster_id,
            kb_endpoint=config.kb_endpoint,
            default_timeout=config.default_timeout,
            default_period=config.default_period,
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
        description="Cluster monitoring service, sends metrics to the resource registry.",
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

    return aparser.parse_args()


if __name__ == "__main__":
    main()
