import pytest
from monitor.shared.utils import cexit
from monitor.shared.errors import (
    MonitorBaseError,
    ConfigurationError,
    CollectorInitializationError,
)


def test_monitor_base_error():
    assert issubclass(MonitorBaseError, Exception)
    assert issubclass(ConfigurationError, MonitorBaseError)
    assert issubclass(CollectorInitializationError, MonitorBaseError)
