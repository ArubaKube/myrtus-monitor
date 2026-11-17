"""Module test_core_monitor contains the test suite for the NodeMonitor class."""

import pytest

from monitor.core.node_monitor import NodeMonitor
from monitor.shared.config import NodeType


@pytest.fixture
def node_monitor_config():
    return {
        "kb_endpoint": "http://fake",
        "liqo_cluster_id": "cid",
        "node_name": "n1",
        "node_type": NodeType.cloud,
        "kb_enabled": False,
        "active_collectors": [],
        "exclude_collectors": [],
        "default_timeout": 60,
        "default_period": 60,
    }


def test_node_monitor_init(node_monitor_config):
    """Test that NodeMonitor parameters are correctly set."""
    labels = {"myrtus.io/node-type": "fog", "myrtus.io/location": "turin"}
    nm = NodeMonitor(labels=labels, **node_monitor_config)
    assert nm.node_name == node_monitor_config["node_name"]
    assert nm.liqo_cluster_id == node_monitor_config["liqo_cluster_id"]
    assert nm._metrics["labels"] == labels


def test_node_monitor_has_axis_dlpu_top_level_field(node_monitor_config):
    """Test that has_axis_dlpu is exposed as a top-level metric field and default is False."""
    defaults = NodeMonitor(**node_monitor_config)
    assert defaults.has_axis_dlpu is False
    assert defaults._metrics["has_axis_dlpu"] is False

    nm = NodeMonitor(has_axis_dlpu=True, **node_monitor_config)
    assert nm.has_axis_dlpu is True
    assert nm._metrics["has_axis_dlpu"] is True
