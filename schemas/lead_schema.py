from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LeadCreate(BaseModel):
    name: str
    status: str
    priority: str
    property: str
    unit: str
    tour_time: datetime
    last_contact_hours: int = Field(ge=0)
    tags: list[str] = []


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    priority: str
    property: str
    unit: str
    tour_time: datetime
    last_contact_hours: int
    tags: list[str]


class LeadSummaryCard(BaseModel):
    id: str
    name: str
    status: str
    priority: str
    property: str
    unit: str
    tour_time: str
    last_contact: str
    tags: list[str]


class LeadsSummaryResponse(BaseModel):
    total: int
    hot: int
    warm: int
    cold: int
    data: list[LeadSummaryCard]
