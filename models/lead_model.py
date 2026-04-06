from datetime import datetime
from typing import List

from beanie import Document


class Lead(Document):
    name: str
    status: str
    priority: str
    property: str
    unit: str
    tour_time: datetime
    last_contact_hours: int
    tags: List[str]

    class Settings:
        name = "leads"
