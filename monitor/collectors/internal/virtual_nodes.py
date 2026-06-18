"""Package virtual_nodes contaings the logic of the virtual_nodes collector."""

import logging

from kubernetes import client, config as k8s_config

from monitor.collectors.collector import Collector

logger = logging.getLogger(__name__)


class VirtualNodesCollector(Collector):
    """VirtualNodesCollector is a specialized collector for monitoring virtual nodes."""

    def __init__(self):
        """Initialize the VirtualNodesCollector."""
        self._api_client: client.ApiClient | None = None

    @classmethod
    def get_name(cls) -> str:
        """Return the name of the collector."""
        return "virtual_nodes"

    async def init(self):
        """Initialize the collector by loading the Kubernetes configuration."""
        configuration = client.Configuration()
        k8s_config.load_incluster_config(client_configuration=configuration)
        # kubernetes-client >=36 stores the token under api_key['authorization'] but
        # auth_settings() looks for api_key['BearerToken'] — remap so the header is sent.
        if bearer := configuration.api_key.get("authorization"):
            configuration.api_key["BearerToken"] = bearer
        self._api_client = client.ApiClient(configuration)

    async def collect(self) -> dict[str, dict[str, str]]:
        """Collect the info about the Liqo virtual nodes in the cluster.

        Returns:
            dict[str, dict[str, str]]: info about the Liqo virtual nodes in the cluster.
        """
        v1 = client.CoreV1Api(self._api_client)
        nodes = v1.list_node(label_selector="liqo.io/type=virtual-node")
        return [
            {
                "node_name": node.metadata.name,
                "liqo_provider_id": node.metadata.labels.get("liqo.io/remote-cluster-id", ""),
            }
            for node in nodes.items
        ]
