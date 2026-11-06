"""Tests for monitor.node.main — node type resolution logic."""

from unittest.mock import MagicMock, patch

import pytest
from kubernetes.config.config_exception import ConfigException

from monitor.node.main import (
    KUBEEDGE_NODE_TYPE,
    MYRTUS_LABEL_PREFIX,
    NODE_TYPE_LABEL,
    _get_myrtus_label_values,
    _resolve_node_type,
)


def _make_node(label_value: str | None):
    node = MagicMock()
    node.metadata.labels = {NODE_TYPE_LABEL: label_value} if label_value else {}
    return node


def _make_node_with_labels(labels: dict[str, str]):
    node = MagicMock()
    node.metadata.labels = labels
    return node


@patch("monitor.node.main.client.CoreV1Api")
@patch("monitor.node.main.k8s_config.load_incluster_config")
def test_label_overrides_fallback(mock_load, mock_api_cls):
    mock_api_cls.return_value.read_node.return_value = _make_node("fog")
    assert _resolve_node_type("my-node", "cloud") == "fog"


@patch("monitor.node.main.client.CoreV1Api")
@patch("monitor.node.main.k8s_config.load_incluster_config")
def test_myrtus_label_values_are_filtered_from_node_labels(mock_load, mock_api_cls):
    labels = {
        f"{MYRTUS_LABEL_PREFIX}node-type": "fog",
        f"{MYRTUS_LABEL_PREFIX}location": "turin",
        "kubernetes.io/hostname": "my-node",
    }
    mock_api_cls.return_value.read_node.return_value = _make_node_with_labels(labels)

    assert _get_myrtus_label_values("my-node") == ["fog", "turin"]


@patch("monitor.node.main.k8s_config.load_incluster_config", side_effect=Exception("not in cluster"))
def test_myrtus_label_values_are_empty_when_k8s_is_unavailable(mock_incluster):
    assert _get_myrtus_label_values("my-node") == []


@patch("monitor.node.main.client.CoreV1Api")
@patch("monitor.node.main.k8s_config.load_incluster_config")
def test_fallback_used_when_label_absent(mock_load, mock_api_cls):
    mock_api_cls.return_value.read_node.return_value = _make_node(None)
    assert _resolve_node_type("my-node", "cloud") == "cloud"


@patch("monitor.node.main.k8s_config.load_kube_config", side_effect=Exception("no kubeconfig"))
@patch("monitor.node.main.k8s_config.load_incluster_config", side_effect=Exception("not in cluster"))
def test_fallback_used_when_k8s_unavailable(mock_incluster, mock_kubeconfig):
    assert _resolve_node_type("my-node", "edge") == "edge"


@patch("monitor.node.main.client.CoreV1Api")
@patch("monitor.node.main.k8s_config.load_incluster_config")
def test_fallback_used_when_api_call_fails(mock_load, mock_api_cls):
    mock_api_cls.return_value.read_node.side_effect = Exception("api error")
    assert _resolve_node_type("my-node", "cloud") == "cloud"


@patch(
    "monitor.node.main.k8s_config.load_incluster_config",
    side_effect=ConfigException("Service host/port is set but empty."),
)
def test_kubeedge_fallback_used_when_enabled_and_config_unavailable(mock_load):
    assert _resolve_node_type("my-node", "cloud", kubeedge_fallback=True) == KUBEEDGE_NODE_TYPE


@patch(
    "monitor.node.main.k8s_config.load_incluster_config",
    side_effect=ConfigException("Service host/port is set but empty."),
)
def test_node_type_arg_used_when_kubeedge_fallback_disabled(mock_load):
    assert _resolve_node_type("my-node", "cloud", kubeedge_fallback=False) == "cloud"


@pytest.mark.parametrize(
    "message",
    [
        "Service host/port is not set.",
        "Service token file does not exist.",
        "Service certification file does not exist.",
        "Cert file exists but empty.",
    ],
)
def test_kubeedge_fallback_not_used_for_other_config_exceptions(message):
    with patch(
        "monitor.node.main.k8s_config.load_incluster_config",
        side_effect=ConfigException(message),
    ):
        assert _resolve_node_type("my-node", "cloud", kubeedge_fallback=True) == "cloud"
