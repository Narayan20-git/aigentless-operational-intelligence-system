from datetime import date, datetime
from typing import Any
from beanie import Document


class Property(Document):
    id: str
    created_at: datetime
    name: str
    description: str | None = None
    address: Any
    latitude: float | None = None
    longitude: float | None = None
    units: int | None = None
    floors: int | None = None
    neighborhood_id: str | None = None
    city_id: str | None = None
    utilities: Any
    amenities: list[Any]
    fees: list[Any]
    _num_images: int
    website: str
    attio_list_id: str | None = None
    concession: str
    attio_building_id: str | None = None
    payment_model: str
    timezone: str | None = None
    yardi_id: str | None = None
    yardi_voyager_server_id: str | None = None
    funnel_community_id: str | None = None
    neighborhood_description: str | None = None
    neighborhood_highlights: list[Any] | None = None
    realpage_pmcid: str | None = None
    realpage_siteid: str | None = None
    elise_id: str | None = None
    entrata_id: str | None = None
    entrata_subdomain: str | None = None
    neighborhood_name: str | None = None
    realpage_revenue_management_enabled: bool | None = None
    go_live_date: date | None = None
    realpage_knock_id: str | None = None
    tours_start_time: float | None = None
    tours_end_time: float | None = None
    pmc_id: str | None = None
    internal_only: bool
    min_from_campus: str | None = None
    parking: Any | None = None
    housing_type: str
    entrata_housing_type: str | None = None
    instagram: str | None = None
    year_built: int | None = None
    geo_highlights: list[Any] | None = None
    limit_analytics: bool
    credit_card_hold_enabled: bool | None = None
    credit_card_hold_amount: int | None = None
    pricing_term_strategy: str
    pricing_term_months: int | None = None
    requires_id_verification: bool | None = None
    gtm_head_script: str | None = None
    gtm_body_script: str | None = None
    hide_price: bool
    hide_fees: bool
    hide_parking_price: bool
    tours_type: str | None = None
    engrain_embed_id: str | None = None
    engrain_origin: str | None = None
    engrain_asset_id: str | None = None
    engrain_sightmap_id: str | None = None

    class Settings:
        name = "properties"
