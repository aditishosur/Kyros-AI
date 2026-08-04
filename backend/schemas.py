from datetime import datetime

from pydantic import BaseModel, Field


class APIBase(BaseModel):
    name: str
    endpoint: str
    method: str = "GET"
    owner: str = "Platform"
    description: str = ""
    status: str = "Healthy"


class APICreate(APIBase):
    pass


class APIUpdate(BaseModel):
    name: str | None = None
    endpoint: str | None = None
    method: str | None = None
    owner: str | None = None
    description: str | None = None
    status: str | None = None


class APIOut(APIBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SimulationIn(BaseModel):
    api_id: int
    traffic_change: float = Field(0, ge=-80, le=300)
    capacity_change: float = Field(0, ge=-80, le=300)
    db_latency_change: float = Field(0, ge=-80, le=300)


class SimulationOut(BaseModel):
    api_id: int
    current: dict
    simulated: dict
    impact: dict
    recommendation: str
    label: str = "SIMULATED/PREDICTED"

