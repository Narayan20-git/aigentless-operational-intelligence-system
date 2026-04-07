from datetime import datetime
from typing import Any
from beanie import Document


class Feedback(Document):
    id: int
    created_at: datetime
    profile_id: str | None = None
    raw_feedback: Any | None = None
    floorplan_id: str | None = None
    type: str | None = None
    booking_id: str | None = None

    class Settings:
        name = "feedback"
