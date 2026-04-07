from datetime import datetime
from typing import Any
from beanie import Document


class Booking(Document):
    id: str
    created_at: datetime
    floorplan_id: str
    start_time: datetime
    end_time: datetime
    profile_id: str | None = None
    string_profile_id: str | None = None
    broker_client_id: str | None = None
    pin: Any
    qr_code: Any
    attio_id: str | None = None
    funnel_id: int | None = None
    attio_tour_id: str | None = None
    phone: str | None = None
    name: str | None = None
    stratis_meta: Any | None = None
    completion_state: Any | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    status: str
    updated_at: datetime | None = None

    class Settings:
        name = "bookings"
