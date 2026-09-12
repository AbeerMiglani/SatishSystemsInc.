from __future__ import annotations

from pydantic import BaseModel, ConfigDict, UUID4


class WaveSchema(BaseModel):
    wave: int
    simulated_minute: int | None = None
    failed_node_ids: list[UUID4]
    cumulative_failed_count: int | None = None
    population_affected_estimate: int | None = None
    hospital_count_operational: int | None = None
    hospital_count_failed: int | None = None

    model_config = ConfigDict(extra="ignore")
