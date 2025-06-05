"""Package errors containing custom exceptions for the monitor service."""


class MonitorBaseError(Exception):
    """Base class for all monitor exceptions."""


class ConfigurationError(MonitorBaseError):
    """Exception raised for errors in the configuration."""


class CollectorInitializationError(MonitorBaseError):
    """Exception raised when a collector fails to initialize."""


class CollectorScrapingError(MonitorBaseError):
    """Exception raised when a collector fails to scrape data."""
