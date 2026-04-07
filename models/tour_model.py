from datetime import datetime
from beanie import Document


class Tour(Document):
    id: str
    created_at: datetime
    description: str
    title: str
    property_id: str | None = None
    estimated_minutes: int
    audio_sync_status: str
    visible: bool
    locked_for_sync: bool
    tour_concession: str | None = None
    archived_at: datetime | None = None

    class Settings:
        name = "tours"
