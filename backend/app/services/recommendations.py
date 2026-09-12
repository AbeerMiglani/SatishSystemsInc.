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
    result: SimulationResult, nodes: list[Node], edges: list[Edge]
) -> list[dict[str, object]]:
    if result.status != "completed":
        return []
    graph = build_graph(nodes, edges)
    wave_one = result.waves[1]["failed_node_ids"] if len(result.waves) > 1 else []
    candidates = list(dict.fromkeys(wave_one + result.initial_failures))
    for node in nodes:
        if node.node_type == "road_junction" and str(node.id) not in candidates:
            candidates.append(str(node.id))
    names = {str(node.id): node.display_name for node in nodes}
    recommendations = []
    for candidate in candidates[:10]:
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
    return recommendations
