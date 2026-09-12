import json
import logging
from datetime import UTC, datetime

import networkx as nx
from celery import shared_task
from sqlalchemy.orm import Session

from app.db.postgres import SessionLocal
from app.db.redis import get_redis_client
from app.models.network import Edge, Node, Scenario, SimulationResult
from app.simulation.cascade import run_cascade
from app.simulation.population import calculate_population_impact, calculate_population_impact_details

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_simulation_task(
    self, 
    simulation_id: str, 
    network_id: str, 
    initial_failures: list[str],
    scenario_id: str | None = None
):
    """
    Background Celery task to run the cascade simulation.
    If scenario_id is provided, applies network modifications first.
    Publishes wave events to Redis for WebSocket streaming.
    """
    db: Session = SessionLocal()
    try:
        sim = db.query(SimulationResult).filter(SimulationResult.id == simulation_id).first()
        if not sim:
            return
        
        sim.status = "running"
        db.commit()
        
        # 1. Fetch network topology
        nodes = db.query(Node).filter(Node.network_id == network_id).all()
        edges = db.query(Edge).filter(Edge.network_id == network_id).all()
        
        # 2. Build in-memory NetworkX DiGraph
        G = nx.DiGraph()
        for n in nodes:
            G.add_node(
                str(n.id), 
                capacity=n.capacity, 
                current_load=n.current_load, 
                failure_threshold=n.failure_threshold,
                population_served=n.population_served,
                population_zone_id=n.population_zone_id,
                node_type=n.node_type,
                status=n.status,
            )
            
        for e in edges:
            src = str(e.source_id)
            tgt = str(e.target_id)
            G.add_edge(src, tgt, weight=e.weight, capacity=e.capacity, edge_type=e.edge_type)
            if e.is_bidirectional:
                G.add_edge(tgt, src, weight=e.weight, capacity=e.capacity, edge_type=e.edge_type)
                
        # 3. Apply Scenario Modifications if present
        scenario = None
        if scenario_id:
            scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
            if not scenario or str(scenario.network_id) != network_id:
                raise ValueError("scenario does not belong to the simulation network")
            if scenario.modifications:
                for mod in scenario.modifications:
                    if mod.get("type") == "add_edge":
                        src = mod["source"]
                        tgt = mod["target"]
                        if src not in G or tgt not in G or src == tgt:
                            raise ValueError("scenario references invalid graph endpoints")
                        weight = mod["weight"]
                        capacity = mod["capacity"]
                        edge_type = mod["edge_type"]
                        is_bidirectional = mod["is_bidirectional"]

                        G.add_edge(src, tgt, weight=weight, capacity=capacity, edge_type=edge_type)
                        if is_bidirectional:
                            G.add_edge(tgt, src, weight=weight, capacity=capacity, edge_type=edge_type)
                    elif mod.get("type") == "upgrade_node":
                        node_id = mod["node_id"]
                        if node_id not in G:
                            raise ValueError("scenario references an invalid upgrade node")
                        node = G.nodes[node_id]
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
                    else:
                        raise ValueError("unsupported scenario modification")
                            
        # Callback to publish waves to Redis
        def on_wave(wave_data):
            # Publish to Redis channel specific to this simulation
            get_redis_client().publish(f"sim_{simulation_id}", json.dumps(wave_data))

        # 4. Run cascade engine
        waves, eff_before, eff_after, _pop_affected = run_cascade(
            G, 
            initial_failures, 
            on_wave_completed=on_wave
        )

        # 5. Save results to Postgres
        cumulative_failed_ids: set[str] = set()
        total_hospitals = sum(
            1 for node_data in G.nodes.values() if node_data.get("node_type") == "hospital"
        )
        enriched_waves = []
        for wave_index, wave in enumerate(waves):
            cumulative_failed_ids.update(wave["failed_node_ids"])
            failed_hospitals = sum(
                1
                for node_id in cumulative_failed_ids
                if G.nodes.get(node_id, {}).get("node_type") == "hospital"
            )
            enriched_waves.append(
                {
                    **wave,
                    "simulated_minute": wave_index * 5,
                    "cumulative_failed_count": len(cumulative_failed_ids),
                    "population_affected_estimate": calculate_population_impact(
                        cumulative_failed_ids, G
                    ),
                    "hospital_count_operational": max(0, total_hospitals - failed_hospitals),
                    "hospital_count_failed": failed_hospitals,
                }
            )

        total_failed = sum(len(w['failed_node_ids']) for w in waves)
        population_affected = calculate_population_impact(cumulative_failed_ids, G)
        
        sim.waves = enriched_waves
        sim.total_failed = total_failed
        sim.population_affected_estimate = population_affected
        population_details = calculate_population_impact_details(cumulative_failed_ids, G)
        for field, value in population_details.items():
            setattr(sim, field, value)
        sim.global_efficiency_before = eff_before
        sim.global_efficiency_after = eff_after
        sim.status = "completed"
        sim.completed_at = datetime.now(UTC)
        
        # If part of a scenario, link the result back to the scenario
        if scenario_id and scenario:
            scenario.cached_result_id = sim.id
            
        db.commit()
        
        # Publish completion event
        get_redis_client().publish(f"sim_{simulation_id}", json.dumps({"status": "completed"}))
        
    except Exception:
        logger.exception("simulation %s failed", simulation_id)
        sim = db.query(SimulationResult).filter(SimulationResult.id == simulation_id).first()
        if sim:
            sim.status = "failed"
            sim.error_message = "Simulation execution failed. Consult server logs with the simulation ID."
            db.commit()
        get_redis_client().publish(f"sim_{simulation_id}", json.dumps({"status": "failed"}))
        raise
    finally:
        db.close()
