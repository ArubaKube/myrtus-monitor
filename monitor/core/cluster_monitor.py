"""The node_monitor module defines the NodeMonitor class for node-level monitoring."""

import logging

from monitor.core import Monitor

logger = logging.getLogger(__name__)


class ClusterMonitor(Monitor):
    """ClusterMonitor is a specialized Monitor for cluster-level monitoring.

    It inherits from the Monitor class and can be extended with cluster-specific collectors.
    """

    def __init__(
        self,
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
            kb_endpoint=kb_endpoint,
            active_collectors=["virtual_nodes"],
            default_timeout=default_timeout,
            default_period=default_period,
        )

        self.liqo_cluster_id = liqo_cluster_id

    async def _send_metrics(self):
        # TODO: Implement the logic to send metrics to the knowledge base endpoint.
        metrics = {
            f"{self.liqo_cluster_id}/{m['node_name']}": {
                "liqo_cluster_id": self.liqo_cluster_id,
                "type": "virtual",
                **m,
            }
            for m in self._metrics.get("virtual_nodes", [])
        }

        logger.info(metrics)
