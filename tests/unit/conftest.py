import pytest

from tests.unit.utils.collectors import COLLECTORS


def set_available_collectors(monkeypatch, collectors):
    """Set the available collectors for testing."""
    monkeypatch.setattr(
        "monitor.collectors._COLLECTORS",
        collectors,
    )


@pytest.fixture
def populate_dummy_collectors(monkeypatch):
    set_available_collectors(monkeypatch, COLLECTORS)
