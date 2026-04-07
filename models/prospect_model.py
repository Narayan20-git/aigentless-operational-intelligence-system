from datetime import datetime
from beanie import Document


class Prospect(Document):
    id: str
    created_at: datetime
    user_id: str | None = None
    email: str | None = None
    phone_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    applied: bool | None = None
    leased: bool | None = None
    ignore: bool | None = None
    ignore_dev: bool | None = None

    class Settings:
        name = "prospects"
