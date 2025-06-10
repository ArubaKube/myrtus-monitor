"""The swap module contains the logic of the Swap collector."""

from typing import Any

import psutil

from monitor.collectors.collector import Collector
from monitor.shared.errors import CollectorScrapingError


class SwapCollectorError(CollectorScrapingError):
    """Exception raised for errors in the Swap collector."""


class SwapCollector(Collector):
    """Collector to collect swap memory usage information."""

    @classmethod
    def get_name(cls) -> str:
        """Return the name of the collector."""
        return "swap"

    def __init__(self) -> None:
        """Initialize the Swap collector."""

    async def collect(self) -> dict[str, Any]:
        """Collect current swap memory utilization information.

        Returns:
            Dictionary containing swap memory information:
            - total: Total swap memory
            - used: Swap memory currently in use
            - timestamp: Timestamp of the measurement

        Raises:
            SwapCollectorError: If there's an error collecting swap memory information
        """
        try:
            # Get swap memory information
            swap = psutil.swap_memory()

            return {
                "total": swap.total,
                "used": swap.used,
                "timestamp": psutil.time.time(),
            }
        except Exception as e:
            raise SwapCollectorError(f"Failed to collect swap memory information: {e!s}") from e
