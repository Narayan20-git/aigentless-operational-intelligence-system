from datetime import datetime
from typing import Any
from beanie import Document


class ProspectEvent(Document):
    id: str
    created_at: datetime
    property_id: str
    prospect_id: str
    cms_id: str
    event: str
    timestamp: datetime
    lead_source: str
    metadata: Any
    ext_event_id: str | None = None
    booking_id: str | None = None
    ignore: bool | None = None
    ignore_dev: bool | None = None

    class Settings:
        name = "prospect_events"
