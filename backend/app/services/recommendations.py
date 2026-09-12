from __future__ import annotations

import networkx as nx

from app.models.network import Edge, Node, SimulationResult
from app.simulation.cascade import run_cascade
from app.simulation.population import calculate_population_impact


def build_graph(nodes: list[Node], edges: list[Edge]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for node in nodes:
        graph.add_node(
            str(node.id),
            capacity=node.capacity,
            current_load=node.current_load,
            failure_threshold=node.failure_threshold,
            population_served=node.population_served,
            population_zone_id=node.population_zone_id,
            node_type=node.node_type,
            status=node.status,
        )
    for edge in edges:
        source, target = str(edge.source_id), str(edge.target_id)
        attrs = {"weight": edge.weight, "capacity": edge.capacity, "edge_type": edge.edge_type}
        graph.add_edge(source, target, **attrs)
        if edge.is_bidirectional:
            graph.add_edge(target, source, **attrs)
    return graph


def apply_modifications(graph: nx.DiGraph, modifications: list[dict[str, object]]) -> None:
    for mod in modifications:
        mod_type = mod.get("type")
        if mod_type == "add_edge":
            source = str(mod["source"])
            target = str(mod["target"])
            attrs = {
                "weight": float(mod.get("weight", 1.0)),
                "capacity": float(mod.get("capacity", 100.0)),
                "edge_type": str(mod.get("edge_type", "depends_on")),
            }
            graph.add_edge(source, target, **attrs)
            if bool(mod.get("is_bidirectional", False)):
                graph.add_edge(target, source, **attrs)
        elif mod_type == "upgrade_node":
            node_id = str(mod["node_id"])
            if node_id not in graph:
                continue
            node = graph.nodes[node_id]
            base_capacity = float(node.get("capacity", 0.0))
            base_threshold = float(node.get("failure_threshold", 1.0))
            node["capacity"] = (
                float(mod["capacity"])
                if mod.get("capacity") is not None
                else base_capacity + float(mod.get("capacity_add", 0.0))
            ) * float(mod.get("capacity_multiplier", 1.0))
            node["failure_threshold"] = (
                float(mod["failure_threshold"])
                if mod.get("failure_threshold") is not None
                else base_threshold + float(mod.get("failure_threshold_add", 0.0))
            ) * float(mod.get("failure_threshold_multiplier", 1.0))


def evaluate_recommendation(
    graph: nx.DiGraph,
    initial_failures: list[str],
    candidate_id: str,
    baseline: SimulationResult,
) -> dict[str, object]:
    upgraded = graph.copy()
    node = upgraded.nodes[candidate_id]
    node["capacity"] = float(node.get("capacity", 0.0)) * 1.25
    node["failure_threshold"] = float(node.get("failure_threshold", 1.0)) * 1.15
    waves, _before, after, _population = run_cascade(upgraded, initial_failures)
    failed = {node_id for wave in waves for node_id in wave["failed_node_ids"]}
    population = calculate_population_impact(failed, upgraded)
    failures_prevented = max(0, int(baseline.total_failed) - len(failed))
    population_saved = max(0, int(baseline.population_affected_estimate) - population)
    efficiency_gain = max(0.0, float(after or 0.0) - float(baseline.global_efficiency_after or 0.0))
    return {
        "candidate_id": candidate_id,
        "candidate_display_name": candidate_id,
        "scenario_payload": {
            "type": "upgrade_node",
            "node_id": candidate_id,
            "capacity_multiplier": 1.25,
            "failure_threshold_multiplier": 1.15,
        },
        "failures_prevented": failures_prevented,
        "population_saved": population_saved,
        "efficiency_gain": efficiency_gain,
        "verified": True,
    }


def recommend_interventions(
    result: SimulationResult,
    nodes: list[Node],
    edges: list[Edge],
    scenario_modifications: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    if result.status != "completed":
        return []
    graph = build_graph(nodes, edges)
    if scenario_modifications:
        apply_modifications(graph, scenario_modifications)
    wave_one = result.waves[1]["failed_node_ids"] if len(result.waves) > 1 else []
    initial_failure_set = set(result.initial_failures)
    candidates = [
        candidate_id
        for candidate_id in dict.fromkeys(wave_one)
        if candidate_id not in initial_failure_set
    ]
    for node in nodes:
        node_id = str(node.id)
        if (
            node.node_type == "road_junction"
            and node_id not in candidates
            and node_id not in initial_failure_set
        ):
            candidates.append(node_id)
    names = {str(node.id): node.display_name for node in nodes}
    recommendations = []
    for candidate in candidates:
        if candidate not in graph:
            continue
        item = evaluate_recommendation(graph, result.initial_failures, candidate, result)
        item["candidate_display_name"] = names.get(candidate, candidate)
        recommendations.append(item)
    recommendations.sort(
        key=lambda item: (
            -int(item["failures_prevented"]),
            -int(item["population_saved"]),
            -float(item["efficiency_gain"]),
            str(item["candidate_id"]),
        )
    )
    return recommendations[:10]
