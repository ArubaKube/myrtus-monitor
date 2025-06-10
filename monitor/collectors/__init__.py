"""The collectors module contains the available collectors for the monitoring service."""

from monitor.collectors.collector import Collector
from monitor.collectors.core.cpu import CPUCollector
from monitor.collectors.core.disk import DiskCollector
from monitor.collectors.core.memory import MemoryCollector
from monitor.collectors.core.swap import SwapCollector
from monitor.collectors.internal.virtual_nodes import VirtualNodesCollector
from monitor.shared.errors import ConfigurationError

_COLLECTORS = [
    CPUCollector,
    DiskCollector,
    MemoryCollector,
    SwapCollector,
    VirtualNodesCollector,
]


def get_declarative_collectors(
    selected_collectors: list[str] | None = None,  # noqa: ARG001 # Temporary ignore for the linter
    exclude: list[str] | None = None,  # noqa: ARG001 # Temporary ignore for the linter
) -> dict[str, Collector]:
    """Get the available declarative collectors.

    If not filters are provided, all the available collectors are returned.

    Args:
        selected_collectors (list[str], optional): Return only the provided collectors.
            Defaults to None.
        exclude (list[str], optional): Exclude the given collectors. Defaults to None.

    Returns:
        dict[str, Collector]: A dictionary of collector names and instance.
    """
    # TODO: implement the declarative collectors logic.
    return {}


def get_programmatic_collectors(
    selected_collectors: list[str] | None = None,
    exclude: list[str] | None = None,
) -> dict[str, Collector]:
    """Get the available programmatic collectors.

    If not filters are provided, all the available collectors are returned.

    Args:
        selected_collectors (list[str], optional): Return only the provided collectors.
            Defaults to None.
        exclude (list[str], optional): Exclude the given collectors. Defaults to None.

    Returns:
        dict[str, Collector]: A dictionary of collector names and instance.
    """
    # filter the collectors based on the provided filter and exclude lists.
    exclude_list = exclude or []
    if selected_collectors is not None and len(selected_collectors) > 0:
        return {
            collector.get_name(): collector()
            for collector in _COLLECTORS
            if collector.get_name() in selected_collectors
            and collector.get_name() not in exclude_list
        }

    return {
        collector.get_name(): collector()
        for collector in _COLLECTORS
        if collector not in exclude_list
    }


def get_collectors(
    selected_collectors: list[str] | None = None,
    exclude: list[str] | None = None,
) -> dict[str, Collector]:
    """Get the available programmatic collectors.

    If not filters are provided, all the available collectors are returned.

    Args:
        selected_collectors (list[str], optional): Return only the provided collectors.
            Defaults to None.
        exclude (list[str], optional): Exclude the given collectors. Defaults to None.

    Returns:
        dict[str, type[Collector]]: A dictionary of collector names and its instance.
    """
    # Check if the provided selected_collectors and exclude lists contain valid collector names.
    # TODO: get also the names of the declarative collectors.
    collector_names = [collector.get_name() for collector in _COLLECTORS]
    for f_type, f_list in {
        "active_collectors": selected_collectors,
        "excluded_collectors": exclude,
    }.items():
        for f in f_list or []:
            if f not in collector_names:
                raise ConfigurationError(f'Unknown collector "{f}" in collector {f_type} list')

    programmatic_collectors = get_programmatic_collectors(
        selected_collectors=selected_collectors,
        exclude=exclude,
    )
    declarative_collectors = get_declarative_collectors(
        selected_collectors=selected_collectors,
        exclude=exclude,
    )

    return programmatic_collectors | declarative_collectors
