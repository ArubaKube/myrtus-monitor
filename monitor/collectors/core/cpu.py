"""The cpu module contains the logic of the CPU collector."""

import os

import psutil

from monitor.collectors.collector import Collector
from monitor.shared.errors import CollectorScrapingError, ConfigurationError


class CPUCollectorError(CollectorScrapingError):
    """Exception raised for errors in the CPU collector."""


class CPUCollector(Collector):
    """Collector to collect CPU utilization and total CPU count information."""

    @classmethod
    def get_name(cls) -> str:
        """Return the name of the collector."""
        return "cpu"

    def __init__(self) -> None:
        """Initialize the CPU collector."""
        self.interval = float(os.getenv("CPU_INTERVAL", "0.1"))

        if not isinstance(self.interval, (int, float)) or self.interval <= 0:
            raise ConfigurationError("Interval must be a positive number")

    async def collect(self) -> dict[str, any]:
        """Collect current CPU utilization and total CPU count.

        Returns:
            Dictionary containing CPU information:
            - used: CPU usage in millicpu units (1000 millicpu = 1 full CPU core)
            - total: Total number of CPUs/cores in the system (in millicpu units)
            - physical: Number of physical CPU cores (in millicpu units)
            - timestamp: Timestamp of the measurement

        Raises:
            CPUCollectorError: If there's an error collecting CPU information
        """
        try:
            # Get CPU utilization as a percentage (averaged over self.interval seconds)
            cpu_utilization = psutil.cpu_percent(interval=self.interval)

            # Get total number of physical and logical CPUs
            total_cpus = psutil.cpu_count(logical=True)
            physical_cpus = psutil.cpu_count(logical=False)

            # Calculate millicpu usage (where 1000 millicpu = 1 full CPU core)
            # Formula: (utilization percentage * total_cpus * 1000) / 100
            used = int((cpu_utilization * total_cpus * 1000) / 100)

            return {
                "used": used,
                "total": total_cpus * 1000,
                "physical": physical_cpus * 1000,
                "timestamp": psutil.time.time(),
            }
        except Exception as e:
            raise CPUCollectorError(f"Failed to collect CPU information: {e!s}") from e
