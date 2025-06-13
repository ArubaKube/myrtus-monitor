"""Module test_core_monitor contains the test suite for the NodeMonitor class."""

import pytest

from monitor.core.node_monitor import NodeMonitor


@pytest.fixture
def node_monitor_config():
    return {
        "kb_endpoint": "http://fake",
        "liqo_cluster_id": "cid",
        "node_name": "n1",
        "active_collectors": [],
        "exclude_collectors": [],
        "default_timeout": 60,
        "default_period": 60,
    }


def test_node_monitor_init(node_monitor_config):
    """Test that NodeMonitor parameters are correctly set."""
    nm = NodeMonitor(**node_monitor_config)
    assert nm.node_name == node_monitor_config["node_name"]
    assert nm.liqo_cluster_id == node_monitor_config["liqo_cluster_id"]
