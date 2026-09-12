from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict


class NodeBase(BaseModel):
    id: UUID4
    name: str
    display_name: str
    name_source: str = "synthetic"
    data_quality: str = "estimated"
    node_type: str
    lat: float
    lng: float
    capacity: float
    current_load: float
    failure_threshold: float
    population_served: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class EdgeBase(BaseModel):
    id: UUID4
    source_id: UUID4
    target_id: UUID4
    edge_type: str
    weight: float
    capacity: float
    is_bidirectional: bool

    model_config = ConfigDict(from_attributes=True)


class NetworkBase(BaseModel):
    id: UUID4
    name: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CentralityScore(BaseModel):
    node_id: UUID4
    display_name: str | None = None
    metric: str = "betweenness"
    score: float
    rank: int
