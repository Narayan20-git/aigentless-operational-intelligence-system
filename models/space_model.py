from datetime import date, datetime
from beanie import Document


class Space(Document):
    id: str
    unit_id: str
    is_affordable: bool | None = None
    has_pricing: bool | None = None
    make_ready_date: date | None = None
    availability_status: str
    available_date: date | None = None
    marketing_unit_number: str | None = None
    entrata_space_id: str | None = None
    min_rent: float | None = None
    max_rent: float | None = None
    min_deposit: float | None = None
    max_deposit: float | None = None
    occupancy_type: str | None = None
    exclusion_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    rentable: bool | None = None
    tourable: bool | None = None

    class Settings:
        name = "spaces"
