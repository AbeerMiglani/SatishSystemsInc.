from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, UUID4, ConfigDict, Field, field_validator, model_validator
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.postgres import get_db
from app.config import settings
from app.models.network import Scenario, SimulationResult, Network, Node
from app.api.simulations import SimulationResponse
from app.security import enforce_rate_limit, require_operator, require_viewer

router = APIRouter(
    prefix="/scenarios",
    tags=["Scenarios"],
    dependencies=[Depends(require_viewer), Depends(enforce_rate_limit)],
)


class AddEdgeModification(BaseModel):
    type: Literal["add_edge"]
    source: UUID4
    target: UUID4
    edge_type: Literal["power_supply", "water_supply", "road_link", "depends_on"]
    weight: float = Field(default=1.0, ge=0, le=1_000_000)
    capacity: float = Field(default=100.0, gt=0, le=1_000_000)
    is_bidirectional: bool = False

    @model_validator(mode="after")
    def endpoints_must_differ(self) -> "AddEdgeModification":
        if self.source == self.target:
            raise ValueError("scenario edge endpoints must differ")
        return self

class ScenarioCreate(BaseModel):
    network_id: UUID4
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2_000)
    modifications: List[AddEdgeModification] = Field(
        min_length=1, max_length=settings.max_scenario_modifications
    )
    initial_failures: List[UUID4] = Field(min_length=1, max_length=settings.max_initial_failures)

    @field_validator("initial_failures")
    @classmethod
    def initial_failures_must_be_unique(cls, values: List[UUID4]) -> List[UUID4]:
        if len(set(values)) != len(values):
            raise ValueError("initial_failures must not contain duplicates")
        return values

class ScenarioResponse(BaseModel):
    id: UUID4
    network_id: UUID4
    name: str
    description: Optional[str]
    modifications: List[AddEdgeModification]
    initial_failures: List[UUID4]
    cached_result_id: Optional[UUID4]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CompareResponse(BaseModel):
    baseline_result: SimulationResponse
    scenario_result: SimulationResponse

@router.post("", response_model=ScenarioResponse)
def create_scenario(
    req: ScenarioCreate,
    db: Session = Depends(get_db),
    _operator=Depends(require_operator),
):
    """Create a new scenario with structural modifications."""
    network = db.query(Network).filter(Network.id == req.network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")

    known_ids = {
        str(node_id)
        for (node_id,) in db.query(Node.id).filter(Node.network_id == req.network_id).all()
    }
    referenced_ids = {str(node_id) for node_id in req.initial_failures}
    for modification in req.modifications:
        referenced_ids.update({str(modification.source), str(modification.target)})
    if referenced_ids - known_ids:
        raise HTTPException(status_code=422, detail="Scenario references nodes outside this network")

    scenario = Scenario(
        network_id=req.network_id,
        name=req.name,
        description=req.description,
        modifications=[modification.model_dump(mode="json") for modification in req.modifications],
        initial_failures=[str(uid) for uid in req.initial_failures]
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario

@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: uuid.UUID, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@router.get("/compare/{baseline_sim_id}/{scenario_id}", response_model=CompareResponse)
def compare_scenarios(baseline_sim_id: uuid.UUID, scenario_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Compare a baseline simulation with a scenario simulation.
    Ensures that the initial_failures match.
    """
    baseline_sim = db.query(SimulationResult).filter(SimulationResult.id == baseline_sim_id).first()
    if not baseline_sim:
        raise HTTPException(status_code=404, detail="Baseline simulation not found")
        
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    if set(baseline_sim.initial_failures) != set(scenario.initial_failures):
        raise HTTPException(
            status_code=400, 
            detail="Cannot compare: initial_failures do not match between baseline and scenario."
        )

    if baseline_sim.network_id != scenario.network_id:
        raise HTTPException(status_code=400, detail="Baseline and scenario belong to different networks")
        
    if not scenario.cached_result_id:
        raise HTTPException(status_code=400, detail="Scenario simulation has not been run or has not completed.")
        
    scenario_sim = db.query(SimulationResult).filter(SimulationResult.id == scenario.cached_result_id).first()
    if not scenario_sim:
        raise HTTPException(status_code=404, detail="Scenario simulation result not found")
    if scenario_sim.network_id != scenario.network_id:
        raise HTTPException(status_code=409, detail="Scenario cache references an invalid simulation")
        
    return CompareResponse(
        baseline_result=baseline_sim,
        scenario_result=scenario_sim
    )
