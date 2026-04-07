from datetime import datetime
from beanie import Document


class TourStep(Document):
    tour_id: str
    title: str
    floor: int | None = None
    type: str | None = None
    feedback: str | None = None
    unit_id: str | None = None
    index: int | None = None
    id: str
    floorplan_id: str | None = None
    archived_at: datetime | None = None

    class Settings:
        name = "tour_steps"
