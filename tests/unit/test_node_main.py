"""Tests for monitor.node.main — node type resolution logic."""

from unittest.mock import MagicMock, patch

import pytest

from monitor.node.main import NODE_TYPE_LABEL, _resolve_node_type


def _make_node(label_value: str | None):
    node = MagicMock()
    node.metadata.labels = {NODE_TYPE_LABEL: label_value} if label_value else {}
    return node


@patch("monitor.node.main.client.CoreV1Api")
@patch("monitor.node.main.k8s_config.load_incluster_config")
def test_label_overrides_fallback(mock_load, mock_api_cls):
    mock_api_cls.return_value.read_node.return_value = _make_node("fog")
    assert _resolve_node_type("my-node", "cloud") == "fog"


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
