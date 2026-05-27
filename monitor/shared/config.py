"""The config module contains the classes for application configuration."""

from enum import Enum


class LogLevel(Enum):
    """Enum for log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class NodeType(Enum):
    """Enum for node types in the Liqo federation."""

    cloud = "cloud"
    fog = "fog"
    edge = "edge"
