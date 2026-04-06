from datetime import datetime, timezone

from models.lead_model import Lead
from schemas.lead_schema import (
    LeadCreate,
    LeadOut,
    LeadSummaryCard,
    LeadsSummaryResponse,
)

_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _norm_status(s: str) -> str:
    return s.strip().lower()


def format_tour_time(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    wd = _WEEKDAYS[dt.weekday()]
    h12 = dt.hour % 12
    if h12 == 0:
        h12 = 12
    ampm = "AM" if dt.hour < 12 else "PM"
    return f"{wd} {h12}:{dt.minute:02d} {ampm}"


def format_last_contact(hours: int) -> str:
    if hours <= 0:
        return "just now"
    if hours == 1:
        return "1 hour ago"
    return f"{hours} hours ago"


def _lead_to_out(lead: Lead) -> LeadOut:
    return LeadOut(
        id=str(lead.id),
        name=lead.name,
        status=lead.status,
        priority=lead.priority,
        property=lead.property,
        unit=lead.unit,
        tour_time=lead.tour_time,
        last_contact_hours=lead.last_contact_hours,
        tags=list(lead.tags),
    )


def _lead_to_card(lead: Lead) -> LeadSummaryCard:
    return LeadSummaryCard(
        id=str(lead.id),
        name=lead.name,
        status=lead.status,
        priority=lead.priority,
        property=lead.property,
        unit=lead.unit,
        tour_time=format_tour_time(lead.tour_time),
        last_contact=format_last_contact(lead.last_contact_hours),
        tags=list(lead.tags),
    )


async def create_lead(data: LeadCreate) -> LeadOut:
    lead = Lead(**data.model_dump())
    await lead.insert()
    return _lead_to_out(lead)


async def list_leads(status: str | None = None) -> list[LeadOut]:
    leads = await Lead.find_all().to_list()
    if status is not None and status.strip():
        key = _norm_status(status)
        leads = [l for l in leads if _norm_status(l.status) == key]
    return [_lead_to_out(l) for l in leads]


async def get_leads_summary() -> LeadsSummaryResponse:
    leads = await Lead.find_all().to_list()
    hot = warm = cold = 0
    for l in leads:
        s = _norm_status(l.status)
        if s == "hot":
            hot += 1
        elif s == "warm":
            warm += 1
        elif s == "cold":
            cold += 1
    return LeadsSummaryResponse(
        total=len(leads),
        hot=hot,
        warm=warm,
        cold=cold,
        data=[_lead_to_card(l) for l in leads],
    )
