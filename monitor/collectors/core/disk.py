"""The disk module contains the logic of the Disk collector."""

from typing import Any

import psutil

from monitor.collectors.collector import Collector
from monitor.shared.errors import CollectorScrapingError


class DiskCollectorError(CollectorScrapingError):
    """Exception raised for errors in the Disk collector."""


class DiskCollector(Collector):
    """Collector to collect disk usage information."""

    @classmethod
    def get_name(cls) -> str:
        """Return the name of the collector."""
        return "disk"

    def __init__(self) -> None:
        """Initialize the Disk collector."""

    async def collect(self) -> dict[str, Any]:
        """Collect current disk usage information.

        Returns:
            Dictionary containing disk information:
            - partitions: List of disk partitions with usage information:
                - device: Device name
                - mountpoint: Mount point
                - total: Total disk space in bytes
                - used: Used disk space in bytes
            - total: Total disk space in bytes (sum of all partitions)
            - used: Used disk space in bytes (sum of all partitions)
            - timestamp: Timestamp of the measurement

        Raises:
            DiskCollectorError: If there's an error collecting disk information
        """
        try:
            partitions_info = []
            total_space = 0
            used_space = 0

            # Get disk partition information
            partitions = psutil.disk_partitions(all=False)

            for partition in partitions:
                try:
                    # Skip special filesystems and read-only filesystems
                    if partition.fstype == "" or "loop" in partition.device:
                        continue

                    usage = psutil.disk_usage(partition.mountpoint)

                    # Add to totals
                    total_space += usage.total
                    used_space += usage.used

                    # Add partition details
                    partitions_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "total": usage.total,
                        "used": usage.used,
                    })
                except (PermissionError, FileNotFoundError):
                    # Skip partitions we can't access
                    continue

            return {
                "partitions": partitions_info,
                "total": total_space,
                "used": used_space,
                "timestamp": psutil.time.time(),
            }
        except Exception as e:
            raise DiskCollectorError(f"Failed to collect disk information: {e!s}") from e
