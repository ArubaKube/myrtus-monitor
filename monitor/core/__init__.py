"""This core module contains the core logic for the monitoring service."""

import asyncio
import logging
from abc import abstractmethod

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

        self._metrics = {}

        self._collectors: dict[str, Collector] = {}
        self._collection_ready_event = asyncio.Event()
        self._ready_collectors = 0

    async def init(self):
        """Discover the available collectors and initialize them."""
        logger.info("Initializing collectors...")
        available_collectors = collectors.get_collectors(
            selected_collectors=self.active_collectors,
            exclude=self.exclude_collectors,
        )

        for collector_name, new_collector in available_collectors.items():
            try:
                self._collectors[collector_name] = new_collector
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

        if len(self._collectors) == 0:
            raise ConfigurationError("No collectors to be initialized found.")
        logger.info("All collectors initialized successfully.")

    async def start(self):
        """Starts the monitoring service."""
        # Define a semaphore to control the collection readiness.
        tasks = [
            asyncio.create_task(self._run_collector(collector, collector_name))
            for collector_name, collector in self._collectors.items()
        ]
        # Append the metrics sender to the task list
        tasks.append(asyncio.create_task(self._run_sender()))
        logger.info("All collectors started.")
        await asyncio.gather(*tasks)

    async def _run_sender(self):
        # wait for all collectors to be ready before sending metrics
        await self._wait_for_collectors()
        while True:
            try:
                logger.info("Sending metrics to the knowledge base at %s", self.kb_endpoint)
                await self._send_metrics()
            except Exception:  # noqa: PERF203
                logger.exception("Failed to send metrics")
            finally:
                # Wait for a while before sending metrics again
                await asyncio.sleep(10)

    @abstractmethod
    async def _send_metrics(self):
        """Send the collected metrics to the knowledge base."""

    async def _run_collector(self, collector: Collector, collector_name: str):
        period = getattr(collector, "period", 0) or self.default_period
        timeout = getattr(collector, "scraping_timeout", 0) or self.default_timeout
        logger.info(
            "Starting collector '%s' with period=%s, timeout=%s",
            collector_name,
            period,
            timeout,
        )

        while True:
            try:
                res = await asyncio.wait_for(collector.collect(), timeout=timeout)
                self._metrics[collector_name] = res
                logger.debug('Collector "%s" collected successfully.', collector_name)
            except asyncio.TimeoutError:
                logger.error('Collector "%s" timed out after %d seconds.', collector_name, timeout)
            except Exception:
                logger.exception('Collector "%s" returned an exception', collector_name)
            finally:
                # Notify that all the collectors completes, it is possible to start pushing metrics.
                if self._ready_collectors < len(self._collectors):
                    self._ready_collectors += 1
                    if self._ready_collectors == len(self._collectors):
                        self._collection_ready_event.set()

            await asyncio.sleep(period)

    async def _wait_for_collectors(self):
        """Wait for all collectors to be ready."""
        logger.info("Waiting for all collectors to be ready...")
        await self._collection_ready_event.wait()
        logger.info("All collectors are ready, start sending metrics to the knowledge base...")
