"""Module test_cluster_monitor contains the test suite for the ClusterMonitor class."""

import pytest

from monitor.core.cluster_monitor import ClusterMonitor


@pytest.fixture
def cluster_monitor_config():
    return {
        "kb_endpoint": "http://fake",
        "liqo_cluster_id": "cid",
        "default_timeout": 60,
        "default_period": 60,
    }


def test_cluster_monitor_init(cluster_monitor_config):
    """Test that ClusterMonitor parameters are correctly set."""
    nm = ClusterMonitor(**cluster_monitor_config)
    assert nm.liqo_cluster_id == cluster_monitor_config["liqo_cluster_id"], (
        "Unexpected liqo_cluster_id"
    )
