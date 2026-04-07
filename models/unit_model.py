from datetime import datetime
from beanie import Document


class Unit(Document):
    id: str
    created_at: datetime
    property_id: str
    description: str
    unit: str
    floor: str | None = None
    monthly_rent: int | None = None
    move_in_date: datetime | None = None
    active: bool
    floorplan_id: str | None = None
    view: str
    lease_months: int | None = None
    net_effective_rent: int | None = None
    concession: str | None = None
    application_url: str | None = None
    num_of_image_views: int
    yardi_id: str | None = None
    device_id: str | None = None
    ada_accesible: bool | None = None
    pets_allowed: bool | None = None
    realpage_id: str | None = None
    display_order: int | None = None
    entrata_unit_id: str | None = None
    rentable: bool
    rentable_override: bool | None = None
    tourable: bool
    tourable_override: bool | None = None
    engrain_unit_id: str | None = None
    engrain_unit_number: str | None = None
    building_number: str | None = None

    class Settings:
        name = "units"
