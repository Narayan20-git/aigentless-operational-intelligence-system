from datetime import datetime
from typing import Any
from beanie import Document


class Floorplan(Document):
    id: str
    created_at: datetime
    name: str
    description: str
    bedrooms: int
    bathrooms: int
    half_bathrooms: int | None = None
    square_footage: int | None = None
    pets_allowed: bool
    amenities: list[Any]
    tour_id: str | None = None
    property_id: str | None = None
    booking_availability: str
    _num_images: int
    address: Any | None = None
    half_bedrooms: int | None = None
    yardi_id: str | None = None
    is_convertible: bool
    realpage_id: str | None = None
    entrata_floorplan_id: str | None = None
    visible_override: bool | None = None
    engrain_floor_plan_id: str | None = None

    class Settings:
        name = "floorplans"
