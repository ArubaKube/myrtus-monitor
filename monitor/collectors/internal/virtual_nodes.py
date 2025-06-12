"""Package virtual_nodes contaings the logic of the virtual_nodes collector."""

from kubernetes import client, config

from monitor.collectors.collector import Collector


class VirtualNodesCollector(Collector):
    """VirtualNodesCollector is a specialized collector for monitoring virtual nodes."""

    def __init__(self):
        """Initialize the VirtualNodesCollector."""

    @classmethod
    def get_name(cls) -> str:
        """Return the name of the collector."""
        return "virtual_nodes"

    async def init(self):
        """Initialize the collector by loading the Kubernetes configuration."""
        config.load_config()

    async def collect(self) -> dict[str, dict[str, str]]:
        """Collect the info about the Liqo virtual nodes in the cluster.

        Returns:
            dict[str, dict[str, str]]: info about the Liqo virtual nodes in the cluster.
        """
        v1 = client.CoreV1Api()
        nodes = v1.list_node(label_selector="liqo.io/type=virtual-node")
        return [
            {
                "node_name": node.metadata.name,
                "liqo_provider_id": node.metadata.labels.get("liqo.io/remote-cluster-id", ""),
            }
            for node in nodes.items
        ]
