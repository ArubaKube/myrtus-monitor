"""The config module contains the classes for application configuration."""

from dataclasses import dataclass

from monitor.shared.config import LogLevel


@dataclass
class NodeMonitorConfig:
    """Configuration for the monitor service."""

    # The name of the node being monitored.
    node_name: str
    # The Liqo cluster ID where the node is running.
    liqo_cluster_id: str
    # The endpoint for the knowledge base service where metrics are pushed.
    kb_endpoint: str
    # The default scraping timeout in seconds. When expired the collector is considered failed.
    default_timeout: int
    # The default scraping period in seconds. The collector is executed every period.
    default_period: int
    # Log level for the monitor service.
    log_level: LogLevel
    # The list of collectors to be used by the monitor service.
    active_collectors: list[str]
    # The list of collectors to be excluded from the monitor service.
    exclude_collectors: list[str]
