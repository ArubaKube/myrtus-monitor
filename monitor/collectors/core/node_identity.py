"""The node_identity module contains the logic of the NodeIdentity collector."""

import os

from monitor.collectors.collector import Collector
from monitor.shared.errors import ConfigurationError


class NodeIdentityCollector(Collector):
    """Collector for the node identity.

    This collector is responsible for gathering the identity information of the node.
    """

    period = 3600

    @classmethod
    def get_name(cls) -> str:
        """Return the name of the collector."""
        return "node_identity"

    def __init__(self):
        """Initialize the NodeIdentityCollector."""
        self.node_name = os.environ.get("NODE_NAME")
        self.liqo_cluster_id = os.environ.get("LIQO_CLUSTER_ID")

        if not self.node_name or not self.liqo_cluster_id:
            raise ConfigurationError(
                "NODE_NAME and LIQO_CLUSTER_ID environment variables must be set to configure "
                "the node_identity collector.",
            )

    async def collect(self) -> dict[str, any]:
        """Collect data from the node identity source.

        Returns:
            dict[str, any]: The collected node identity data.
        """
        return {
            "nodeName": self.node_name,
            "liqoClusterId": self.liqo_cluster_id,
        }
