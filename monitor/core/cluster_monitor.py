"""The node_monitor module defines the NodeMonitor class for node-level monitoring."""

import logging

from mirto import dkb
from mirto.namespaces import COMPUTE_NODES

from monitor.core import Monitor

logger = logging.getLogger(__name__)


class ClusterMonitor(Monitor):
    """ClusterMonitor is a specialized Monitor for cluster-level monitoring.

    It inherits from the Monitor class and can be extended with cluster-specific collectors.
    """

    def __init__(
        self,
        kb_enabled: bool,
        kb_endpoint: str,
        liqo_cluster_id: str,
        default_timeout: int = 60,
        default_period: int = 60,
    ):
        """Initialize the NodeMonitor with the given configuration.

        Args:
            kb_endpoint (str): The endpoint for the knowledge base service where metrics are pushed.
            liqo_cluster_id (str): The Liqo cluster ID where the node is running.
            default_timeout (int, optional): The default scraping timeout. Defaults to 60.
            default_period (int, optional): The default scraping period. Defaults to 60.
        """
        super().__init__(
            kb_enabled=kb_enabled,
            kb_endpoint=kb_endpoint,
            active_collectors=["virtual_nodes"],
            default_timeout=default_timeout,
            default_period=default_period,
        )

        self.liqo_cluster_id = liqo_cluster_id

        # this is how it should be done but it's not working due to the current KDB's implementation
        # KDB is reading the value from the env variable KB_URL even if passed from outside
        dkb.KB_URL = self.kb_endpoint

    async def _send_metrics(self):
        metrics = {
            f"{self.liqo_cluster_id}/{m['node_name']}": {
                "liqo_cluster_id": self.liqo_cluster_id,
                "type": "virtual",
                **m,
            }
            for m in self._metrics.get("virtual_nodes", [])
        }

        logger.debug(metrics)

        if self.kb_enabled:
            logger.info("Sending metrics to DKB...")
            dkb.store_json(COMPUTE_NODES, f"{self.liqo_cluster_id}", metrics)
        else:
            logger.info("DKB integration disabled. No data has been sent.")
