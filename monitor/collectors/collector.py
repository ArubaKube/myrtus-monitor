"""The collector module defines the base class for collectors."""

from abc import abstractmethod


class Collector:
    """Base class for collectors.

    Collectors are responsible for gathering data from various sources.
    """

    # Leave this at 0 to keep the default period as defined in the configuration.
    period = 0
    # Leave this at 0 to keep the default timeout as defined in the configuration.
    scaping_timeout = 0

    def __init__(self):
        """Initialize the collector."""

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Return the name of the collector.

        Returns:
            str: the name of the collector.
        """

    async def init(self):
        """Initialize the collector.

        This method can be overridden by subclasses to perform any necessary setup.
        """

    @abstractmethod
    async def collect(self) -> dict[str, any]:
        """Collect data from the source.

        This method should be implemented by subclasses.
        """
