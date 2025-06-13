"""Module test_core_monitor contains the test suite for the Monitor class."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from monitor.collectors import Collector
from monitor.core import Monitor
from monitor.shared.errors import (
    CollectorInitializationError,
    ConfigurationError,
    MonitorBaseError,
)
from tests.unit.conftest import set_available_collectors
from tests.unit.utils.collectors import COLLECTORS


@pytest.fixture
def monitor_config():
    return {
        "kb_endpoint": "http://fake",
        "active_collectors": [],
        "exclude_collectors": [],
        "default_timeout": 60,
        "default_period": 60,
    }


@pytest.mark.monitor
def test_monitor_init_conflict_collectors(monitor_config):
    """Test that an error is raised when both active and exclude collectors are specified."""
    monitor_config["active_collectors"] = ["a"]
    monitor_config["exclude_collectors"] = ["b"]
    with pytest.raises(ConfigurationError):
        Monitor(**monitor_config)


@pytest.mark.monitor
def test_monitor_init(monitor_config):
    """Test that Monitor parameters are correctly set."""
    m = Monitor(**monitor_config)
    assert m.kb_endpoint == monitor_config["kb_endpoint"], "Unexpected kb_endpoint"
    assert m.active_collectors == monitor_config["active_collectors"], (
        "Unexpected active_collectors"
    )
    assert m.exclude_collectors == monitor_config["exclude_collectors"], (
        "Unexpected exclude_collectors"
    )
    assert m.default_timeout == monitor_config["default_timeout"], "Unexpected default_timeout"
    assert m.default_period == monitor_config["default_period"], "Unexpected default_period"


@pytest.mark.monitor
@pytest.mark.asyncio
async def test_monitor_init_collectors_success(populate_dummy_collectors, monitor_config):
    """Test that all available collectors are initialized successfully."""
    m = Monitor(**monitor_config)
    await m.init()
    assert {c.get_name() for c in COLLECTORS} == set(m._collectors.keys()), (
        "Not all collectors initialized"
    )


@pytest.mark.monitor
@pytest.mark.asyncio
async def test_monitor_init_collectors_none(monkeypatch, monitor_config):
    """Test that an error is raised when no collectors are available."""
    set_available_collectors(monkeypatch, [])
    m = Monitor(**monitor_config)
    with pytest.raises(ConfigurationError) as e:
        await m.init()
    assert "No collectors" in str(e.value), "Expected error about no collectors found"


@pytest.mark.monitor
@pytest.mark.asyncio
async def test_monitor_init_collector_error(monkeypatch, monitor_config):
    """Test that an error is raised if a collector fails to initialize."""

    class BadCollector(Collector):
        @classmethod
        def get_name(cls):
            return "bad"

        async def init(self):
            raise MonitorBaseError("fail")

        async def collect(self):
            return {}

    set_available_collectors(monkeypatch, [BadCollector])
    m = Monitor(**monitor_config)
    with pytest.raises(CollectorInitializationError):
        await m.init()


@pytest.mark.monitor
@pytest.mark.asyncio
async def test_monitor_run_collector_success(monkeypatch, monitor_config):
    """Test that a collector runs and stores its metrics successfully."""
    expected_data = {"ok": True}

    class FastCollector(Collector):
        @classmethod
        def get_name(cls):
            return "fast"

        async def collect(self):
            return expected_data

    m = Monitor(**monitor_config)
    m._collectors = {"fast": FastCollector()}
    m.default_period = 1

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(m._run_collector(m._collectors["fast"], "fast"), timeout=1)
    assert "fast" in m._metrics, "Expected collector metrics to be stored"
    assert m._metrics["fast"] == expected_data, "Expected collector metrics to match collected data"


@pytest.mark.monitor
@pytest.mark.asyncio
async def test_monitor_run_collector_timeout(monkeypatch, monitor_config):
    """Test that a collector timing out is handled gracefully."""

    class SlowCollector(Collector):
        @classmethod
        def get_name(cls):
            return "slow"

        async def init(self):
            pass

        async def collect(self):
            await asyncio.sleep(1)

    m = Monitor(**monitor_config)
    m._collectors = {"slow": SlowCollector()}
    m.default_period = 0.01
    m.default_timeout = 0.01

    async def sleep_patch(period):
        raise asyncio.CancelledError()

    monkeypatch.setattr(asyncio, "sleep", sleep_patch)
    with pytest.raises(asyncio.CancelledError):
        await m._run_collector(m._collectors["slow"], "slow")


@pytest.mark.monitor
@pytest.mark.asyncio
async def test_monitor_run_collector_success(monitor_config):
    """Test that the collector is called repeatedly and metrics are sent."""
    test_timeout = 2.5

    class MyCollector(Collector):
        def __init__(self):
            self.collect_called_counter = 0

        @classmethod
        def get_name(cls):
            return "my_collector"

        async def collect(self):
            self.collect_called_counter += 1
            return {"data": "test"}

    monitor_config["default_period"] = 1
    collector = MyCollector()
    m = Monitor(**monitor_config)
    m._collectors = {MyCollector.get_name(): collector}

    m._send_metrics = AsyncMock()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(m.start(), timeout=test_timeout)
    # Give some tollerance to the number of calls due to possible delays in the event loop
    assert collector.collect_called_counter in [2, 3], "Expected collector to be called twice"
    assert m._send_metrics.call_count in [2, 3], "Expected metrics to be sent twice"
