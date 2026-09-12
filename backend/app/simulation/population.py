from __future__ import annotations

from collections.abc import Iterable

import networkx as nx

STUDY_AREA_POPULATION_CAP = 65_000


def calculate_population_impact(
    failed_node_ids: Iterable[str],
    graph: nx.DiGraph,
    population_cap: int = STUDY_AREA_POPULATION_CAP,
) -> int:
    """Return a deterministic, capped estimate for uniquely failed nodes.

    The current synthetic dataset stores population exposure on nodes rather
    than spatial zones. Counting each failed node at most once prevents repeat
    counting when a caller supplies duplicate IDs; the cap prevents the
    estimate from exceeding the documented study-area population.
    """
    grouped: dict[str, int] = {}
    for node_id in set(failed_node_ids):
        if node_id not in graph:
            continue
        data = graph.nodes[node_id]
        zone_id = data.get("population_zone_id")
        key = str(zone_id) if zone_id else f"node:{node_id}"
        grouped[key] = max(grouped.get(key, 0), max(0, int(data.get("population_served", 0))))
    affected = sum(grouped.values())
    return min(affected, max(0, population_cap))


def calculate_population_impact_details(
    failed_node_ids: Iterable[str],
    graph: nx.DiGraph,
    population_cap: int = STUDY_AREA_POPULATION_CAP,
) -> dict[str, object]:
    """Return additive impact metadata for legacy node-exposure networks."""
    unique_failed = set(failed_node_ids)
    grouped: dict[str, int] = {}
    for node_id in unique_failed:
        if node_id not in graph:
            continue
        data = graph.nodes[node_id]
        zone_id = data.get("population_zone_id")
        key = str(zone_id) if zone_id else f"node:{node_id}"
        grouped[key] = max(grouped.get(key, 0), max(0, int(data.get("population_served", 0))))
    raw = sum(grouped.values())
    affected = min(raw, max(0, population_cap))
    return {
        "population_total": max(0, population_cap),
        "population_affected_estimate": affected,
        "population_affected_percentage": (affected / population_cap * 100) if population_cap else 0.0,
        "population_overlap_unresolved": True,
        "population_estimate_is_capped": raw > affected,
        "population_impact_method": "zone_grouped_node_exposure" if grouped else "legacy_node_exposure",
    }
