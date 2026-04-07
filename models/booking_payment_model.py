from datetime import datetime
from beanie import Document


class BookingPayment(Document):
    id: str
    booking_id: str
    property_id: str
    payment_intent_id: str
    collateral_amount: int
    payment_status: str
    captured_amount: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    profile_id: str | None = None

    class Settings:
        name = "booking_payments"
