"""This core module contains the core logic for the monitoring service."""

import logging

from monitor import collectors
from monitor.collectors.collector import Collector
from monitor.shared.errors import CollectorInitializationError, ConfigurationError, MonitorBaseError

logger = logging.getLogger(__name__)


class Monitor:
    """The Monitor class serves as the entry point for the monitoring service.

    It initializes the collectors with the provided configuration and starts the monitoring process.
    """

    def __init__(
        self,
        kb_endpoint: str,
        active_collectors: list[str] | None = None,
        exclude_collectors: list[str] | None = None,
        default_timeout: int = 60,
        default_period: int = 60,
    ):
        """Initialize the Monitor with the given configuration.

        Args:
            kb_endpoint (str): The endpoint for the knowledge base service where metrics are pushed.
            active_collectors (list[str], optional): The list of the only active collectors.
                If empty all the active discovered collectors are started. Defaults to None.
            exclude_collectors (list[str], optional): The list of collectors to exclude from the
                available. Defaults to None.
            default_timeout (int, optional): The default scraping timeout. Defaults to 60.
            default_period (int, optional): The default scraping period. Defaults to 60.

        Raises:
            ConfigurationError: raised when invalid configuration is provided.
        """
        self.kb_endpoint = kb_endpoint
        self.active_collectors = active_collectors or []
        self.exclude_collectors = exclude_collectors or []
        self.default_timeout = default_timeout
        self.default_period = default_period

        if len(self.active_collectors) > 0 and len(self.exclude_collectors) > 0:
            raise ConfigurationError("Cannot specify both active and exclude collectors.")

        self.collectors: dict[str, Collector] = {}

    async def init(self):
        """Discover the available collectors and initialize them."""
        logger.info("Initializing collectors...")
        available_collectors = collectors.get_collectors(
            selected_collectors=self.active_collectors,
            exclude=self.exclude_collectors,
        )

        for collector_name, new_collector in available_collectors.items():
            try:
                self.collectors[collector_name] = new_collector
                await new_collector.init()
            except MonitorBaseError as e:
                err_msg = f"Failed to initialize collector {collector_name}: {e}"
                logger.error(err_msg)
                raise CollectorInitializationError("Unable to initialize collectors") from e
            except Exception as e:
                err_msg = f"Failed to initialize collector {collector_name}: {e}"
                logger.exception(err_msg)
                raise CollectorInitializationError("Unable to initialize collectors") from e

            logger.debug("Initialized collector %s", collector_name)

        if len(self.collectors) == 0:
            raise ConfigurationError("No collectors to be initialized found.")
        logger.info("All collectors initialized successfully.")

    async def start(self):
        """Starts the monitoring service."""
        # TODO: implement the monitoring logic.
