"""Test collectors discovery and selection."""

import pytest

from monitor.collectors import get_collectors
from monitor.shared.errors import ConfigurationError
from tests.unit.utils.collectors import COLLECTORS, AnotherCollector, ThirdCollector


@pytest.mark.collectors
@pytest.mark.collectors_discovery
def test_get_collectors_all(populate_dummy_collectors):
    """Test whether the collectors are correctly discovered and returned."""
    result = get_collectors()
    assert len(result) == len(COLLECTORS), "Expected all collectors to be returned"
    for collector in COLLECTORS:
        assert collector.get_name() in result, (
            f"Expected '{collector.get_name()}' collector to be included"
        )


@pytest.mark.collectors
@pytest.mark.collectors_discovery
def test_get_collectors_active(populate_dummy_collectors):
    """Test whether the selected collectors are returned."""
    result = get_collectors(selected_collectors=["dummy"])
    assert "dummy" in result, "Expected 'dummy' collector to be included"
    assert len(result) == 1, "Expected only one collector to be returned"


@pytest.mark.collectors
@pytest.mark.collectors_discovery
def test_get_collectors_exclude(populate_dummy_collectors):
    """Test whether the excluded collectors are not returned."""
    result = get_collectors(exclude=["dummy"])
    assert "dummy" not in result, "Expected 'dummy' collector to be excluded"
    assert len(result) == 2, "Expected only two collectors to be returned"
    assert AnotherCollector.get_name() in result, (
        f"Expected '{AnotherCollector.get_name()}' collector to be included"
    )
    assert ThirdCollector.get_name() in result, (
        f"Expected '{ThirdCollector.get_name()}' collector to be included"
    )


@pytest.mark.collectors
@pytest.mark.collectors_discovery
def test_get_collectors_invalid_collector_in_selection(populate_dummy_collectors):
    """Test whether an error is raised when an invalid collector is selected."""
    with pytest.raises(ConfigurationError):
        get_collectors(selected_collectors=["notfound"])


@pytest.mark.collectors
@pytest.mark.collectors_discovery
def test_get_collectors_invalid_collector_in_exclude(populate_dummy_collectors):
    """Test whether an error is raised when an invalid collector is excluded."""
    with pytest.raises(ConfigurationError):
        get_collectors(exclude=["notfound"])
