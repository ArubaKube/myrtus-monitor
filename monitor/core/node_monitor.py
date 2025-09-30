"""The node_monitor module defines the NodeMonitor class for node-level monitoring."""

import logging

from mirto import dkb
from mirto.namespaces import DEPLOYER_COMPUTES

from monitor.core import Monitor

logger = logging.getLogger(__name__)


class NodeMonitor(Monitor):
    """NodeMonitor is a specialized Monitor for node-level monitoring.

    It inherits from the Monitor class and can be extended with node-specific collectors.
    """

    def __init__(
        self,
        kb_enabled: bool,
        kb_endpoint: str,
        liqo_cluster_id: str,
        node_name: str,
        active_collectors: list[str] | None = None,
        exclude_collectors: list[str] | None = None,
        default_timeout: int = 60,
        default_period: int = 60,
    ):
        """Initialize the NodeMonitor with the given configuration.

        Args:
            kb_endpoint (str): The endpoint for the knowledge base service where metrics are pushed.
            liqo_cluster_id (str): The Liqo cluster ID where the node is running.
            node_name (str): the name of the node being monitored.
            active_collectors (list[str], optional): The list of the only active collectors.
                If empty all the active discovered collectors are started. Defaults to None.
            exclude_collectors (list[str], optional): The list of collectors to exclude from the
                available. Defaults to None.
            default_timeout (int, optional): The default scraping timeout. Defaults to 60.
            default_period (int, optional): The default scraping period. Defaults to 60.
        """
        super().__init__(
            kb_enabled=kb_enabled,
            kb_endpoint=kb_endpoint,
            active_collectors=active_collectors,
            # We don't want virtual_nodes collector to be included in the node monitor
            exclude_collectors=["virtual_nodes"] + (exclude_collectors or []),
            default_timeout=default_timeout,
            default_period=default_period,
        )

        self.liqo_cluster_id = liqo_cluster_id
        self.node_name = node_name

        self._metrics = {
            "node_name": node_name,
            "liqo_cluster_id": liqo_cluster_id,
            "type": "node",
        }

        # this is how it should be done but it's not working due to the current KDB's implementation
        # KDB is reading the value from the env variable KB_URL even if passed from outside
        dkb.KB_URL = self.kb_endpoint

    async def _send_metrics(self):
        logger.debug(self._metrics)

        if self.kb_enabled:
            logger.info("Sending metrics to DKB...")
            dkb.store_json(
                DEPLOYER_COMPUTES, f"{self.liqo_cluster_id}_{self.node_name}", self._metrics
            )
        else:
            logger.info("DKB integration disabled. No data has been sent.")
