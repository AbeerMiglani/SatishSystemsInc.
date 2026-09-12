import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.config import settings
from app.db.postgres import get_db
from app.models.network import Edge, Network, Node, Scenario, SimulationResult
from app.security import enforce_rate_limit, require_operator, require_viewer
from app.schemas.simulation import WaveSchema
from app.simulation.runner import run_simulation_task
from app.services.recommendations import recommend_interventions

router = APIRouter(
    prefix="/simulations",
    tags=["Simulations"],
    dependencies=[Depends(require_viewer), Depends(enforce_rate_limit)],
)
logger = logging.getLogger(__name__)


class SimulationCreate(BaseModel):
    network_id: UUID4
    initial_failures: list[UUID4] = Field(min_length=1, max_length=settings.max_initial_failures)
    scenario_id: UUID4 | None = None

    @field_validator("initial_failures")
    @classmethod
    def initial_failures_must_be_unique(cls, values: list[UUID4]) -> list[UUID4]:
        if len(set(values)) != len(values):
            raise ValueError("initial_failures must not contain duplicates")
        return values


class SimulationResponse(BaseModel):
    id: UUID4
    network_id: UUID4
    status: str
    initial_failures: list[UUID4]
    waves: list[WaveSchema]
    total_failed: int
    population_affected_estimate: int
    population_total: int = 65_000
    population_affected_percentage: float = 0.0
    population_overlap_unresolved: bool = True
    population_estimate_is_capped: bool = False
    population_impact_method: str = "legacy_node_exposure"
    global_efficiency_before: float | None = None
    global_efficiency_after: float | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=SimulationResponse)
def create_simulation(
    req: SimulationCreate,
    db: Session = Depends(get_db),
    _operator=Depends(require_operator),
):
    """Trigger a new cascading failure simulation."""
    net = db.query(Network).filter(Network.id == req.network_id).first()
    if not net:
        raise HTTPException(status_code=404, detail="Network not found")

    requested_ids = {str(node_id) for node_id in req.initial_failures}
    known_ids = {
        str(node_id)
        for (node_id,) in db.query(Node.id).filter(Node.network_id == req.network_id).all()
    }
    if requested_ids - known_ids:
        raise HTTPException(status_code=422, detail="initial_failures contains nodes outside this network")

    if req.scenario_id:
        scenario = (
            db.query(Scenario)
            .filter(Scenario.id == req.scenario_id, Scenario.network_id == req.network_id)
            .first()
        )
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found for this network")
        
    sim = SimulationResult(
        network_id=req.network_id,
        initial_failures=[str(uid) for uid in req.initial_failures],
        status="pending"
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    
    # Dispatch after the durable row exists. A dispatch failure is recorded so
    # callers never poll a permanently pending job.
    try:
        run_simulation_task.delay(
            simulation_id=str(sim.id),
            network_id=str(req.network_id),
            initial_failures=[str(uid) for uid in req.initial_failures],
            scenario_id=str(req.scenario_id) if req.scenario_id else None,
        )
    except Exception:
        logger.exception("failed to dispatch simulation %s", sim.id)
        sim.status = "failed"
        sim.error_message = "Simulation dispatch failed"
        db.commit()
        raise HTTPException(status_code=503, detail="Simulation queue unavailable")
    
    return sim


@router.get("/{sim_id}/recommendations")
def get_recommendations(sim_id: uuid.UUID, db: Session = Depends(get_db)):
    sim = db.query(SimulationResult).filter(SimulationResult.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim.status != "completed":
        raise HTTPException(status_code=400, detail="Recommendations require a completed simulation")
    nodes = db.query(Node).filter(Node.network_id == sim.network_id).all()
    edges = db.query(Edge).filter(Edge.network_id == sim.network_id).all()
    scenario = (
        db.query(Scenario)
        .filter(Scenario.cached_result_id == sim.id, Scenario.network_id == sim.network_id)
        .first()
    )
    recommendations = recommend_interventions(
        sim,
        nodes,
        edges,
        scenario_modifications=scenario.modifications if scenario else None,
    )
    return {"simulation_id": sim.id, "recommendations": recommendations}


@router.get("/{sim_id}", response_model=SimulationResponse)
def get_simulation(sim_id: uuid.UUID, db: Session = Depends(get_db)):
    """Fetch the status and results of a simulation."""
    sim = db.query(SimulationResult).filter(SimulationResult.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim
