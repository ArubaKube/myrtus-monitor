"""The memory module contains the logic of the Memory collector."""

from typing import Any

import psutil

from monitor.collectors.collector import Collector
from monitor.shared.errors import CollectorScrapingError


class MemoryCollectorError(CollectorScrapingError):
    """Exception raised for errors in the Memory collector."""


class MemoryCollector(Collector):
    """Collector to collect memory usage information."""

    @classmethod
    def get_name(cls) -> str:
        """Return the name of the collector."""
        return "memory"

    def __init__(self) -> None:
        """Initialize the Memory collector."""

    async def collect(self) -> dict[str, Any]:
        """Collect current memory utilization information.

        Returns:
            Dictionary containing memory information:
            - total: Total physical memory
            - used: Memory currently in use
            - timestamp: Timestamp of the measurement

        Raises:
            MemoryCollectorError: If there's an error collecting memory information
        """
        try:
            # Get virtual memory information
            memory = psutil.virtual_memory()

            return {
                "total": memory.total,
                "used": memory.used,
                "timestamp": psutil.time.time(),
            }
        except Exception as e:
            raise MemoryCollectorError(f"Failed to collect memory information: {e!s}") from e
