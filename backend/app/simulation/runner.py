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
                    if mod.get("type") != "add_edge":
                        raise ValueError("unsupported scenario modification")
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
                            
        # Callback to publish waves to Redis
        def on_wave(wave_data):
            # Publish to Redis channel specific to this simulation
            get_redis_client().publish(f"sim_{simulation_id}", json.dumps(wave_data))

        # 4. Run cascade engine
        waves, eff_before, eff_after, pop_affected = run_cascade(
            G, 
            initial_failures, 
            on_wave_completed=on_wave
        )
        
        # 5. Save results to Postgres
        total_failed = sum(len(w['failed_node_ids']) for w in waves)
        
        sim.waves = waves
        sim.total_failed = total_failed
        sim.population_affected_estimate = pop_affected
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
