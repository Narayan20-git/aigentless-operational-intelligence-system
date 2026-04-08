"""
Checklist Router
Endpoints:
  GET  /onboarding/{property_id}/checklist              → full checklist all sections
  GET  /onboarding/{property_id}/checklist/{section}    → single section checklist
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.db import supabase

router = APIRouter()

# Hardcoded required checklist items per section (Option A — Fixed Rules)
CHECKLIST_ITEMS = {
    "property_info": [
        {"key": "name",             "label": "Property name",          "required": True},
        {"key": "description",      "label": "Property description",   "required": True},
        {"key": "address",          "label": "Property address",       "required": True},
        {"key": "units",            "label": "Total units",            "required": True},
        {"key": "year_built",       "label": "Year built",             "required": True},
        {"key": "website",          "label": "Website URL",            "required": True},
        {"key": "amenities",        "label": "Amenities list",         "required": True},
        {"key": "go_live_date",     "label": "Go-live date",           "required": False},
        {"key": "parking",          "label": "Parking details",        "required": False},
        {"key": "virtual_tour_url", "label": "Virtual tour URL",       "required": False},
        {"key": "office_hours",     "label": "Office hours",           "required": False},
        {"key": "accessibility",    "label": "Accessibility features", "required": False},
    ],
    "units_floor_plans": [
        {"key": "units_added",      "label": "All units added",             "required": True},
        {"key": "bedrooms",         "label": "Bedroom/bathroom counts",     "required": True},
        {"key": "square_footage",   "label": "Square footage per unit",     "required": True},
        {"key": "floor_plans",      "label": "Floor plan PDFs uploaded",    "required": True},
        {"key": "pricing",          "label": "Unit pricing entered",        "required": True},
    ],
    "amenities": [
        {"key": "amenities_list",   "label": "Amenities list complete",         "required": True},
        {"key": "descriptions",     "label": "All amenity descriptions written","required": True},
        {"key": "photos",           "label": "Amenity photos uploaded",         "required": False},
    ],
    "media_photos": [
        {"key": "exterior",         "label": "Property exterior photos",    "required": True},
        {"key": "common_areas",     "label": "Lobby/common area photos",    "required": True},
        {"key": "unit_photos",      "label": "All unit photos uploaded",    "required": True},
        {"key": "virtual_tour",     "label": "Virtual tour link added",     "required": False},
    ],
    "content_faqs": [
        {"key": "general",          "label": "General leasing FAQ",                    "required": True},
        {"key": "pet_policy",       "label": "Pet policy FAQ",                         "required": True},
        {"key": "parking",          "label": "Parking FAQ",                            "required": True},
        {"key": "utilities",        "label": "Utility billing FAQ",                    "required": True},
        {"key": "maintenance",      "label": "Maintenance request process",            "required": True},
        {"key": "guest",            "label": "Guest policy",                           "required": True},
        {"key": "noise",            "label": "Noise policy",                           "required": True},
        {"key": "lease",            "label": "Lease renewal terms",                    "required": True},
        {"key": "move_in",          "label": "Move-in checklist",                      "required": True},
        {"key": "general_2",        "label": "Renter''s insurance requirements",       "required": True},
        {"key": "general_3",        "label": "Short-term rental policy",               "required": False},
        {"key": "lease_2",          "label": "Lease break policy",                     "required": False},
    ],
    "integrations": [
        {"key": "apartments_com",   "label": "Apartments.com connected",           "required": True},
        {"key": "zillow",           "label": "Zillow Rental Manager connected",    "required": True},
        {"key": "yardi",            "label": "Yardi Voyager / PMS synced",         "required": True},
        {"key": "rent_com",         "label": "Rent.com connected",                 "required": False},
        {"key": "appfolio",         "label": "AppFolio connected",                 "required": False},
    ],
}

@router.get("/onboarding/{property_id}/checklist")
async def get_full_checklist(property_id: str):
    """
    View Detailed Checklist button — returns all 6 sections
    with item-level completion status for the property.
    """
    # Verify property exists
    prop = supabase.table("properties") \
        .select("id, name") \
        .eq("id", property_id) \
        .single() \
        .execute()
    if not prop.data:
        raise HTTPException(status_code=404, detail="Property not found")

    checklist = {}
    for section in CHECKLIST_ITEMS.keys():
        checklist[section] = await _build_section_checklist(property_id, section)

    total_items     = sum(len(v["items"]) for v in checklist.values())
    completed_items = sum(
        sum(1 for i in v["items"] if i["completed"])
        for v in checklist.values()
    )

    return {
        "property_id":       property_id,
        "property_name":     prop.data["name"],
        "checklist":         checklist,
        "summary": {
            "total_items":     total_items,
            "completed_items": completed_items,
            "pending_items":   total_items - completed_items,
            "overall_pct":     round(completed_items / total_items * 100) if total_items else 0,
        }
    }

@router.get("/onboarding/{property_id}/checklist/{section}")
async def get_section_checklist(property_id: str, section: str):
    """Single section checklist — used when clicking on a specific section bar."""
    if section not in CHECKLIST_ITEMS:
        raise HTTPException(status_code=400, detail=f"Invalid section: {section}")

    prop = supabase.table("properties") \
        .select("id, name") \
        .eq("id", property_id) \
        .single() \
        .execute()
    if not prop.data:
        raise HTTPException(status_code=404, detail="Property not found")

    return {
        "property_id":   property_id,
        "property_name": prop.data["name"],
        "section":       section,
        "checklist":     await _build_section_checklist(property_id, section),
    }

async def _build_section_checklist(property_id: str, section: str) -> dict:
    """Build checklist items for a single section by checking actual data."""
    items_template = CHECKLIST_ITEMS[section]
    completed_keys = await _get_completed_keys(property_id, section)
    items = []
    for item in items_template:
        items.append({
            "key":       item["key"],
            "label":     item["label"],
            "required":  item["required"],
            "completed": item["key"] in completed_keys,
        })
    completed = sum(1 for i in items if i["completed"])
    return {
        "items":          items,
        "completed":      completed,
        "total":          len(items),
        "completion_pct": round(completed / len(items) * 100) if items else 0,
    }

async def _get_completed_keys(property_id: str, section: str) -> set:
    """Check actual DB data to determine which checklist items are done."""
    completed = set()

    if section == "property_info":
        prop = supabase.table("properties") \
            .select("name,description,address,units,year_built,website,amenities,go_live_date,parking") \
            .eq("id", property_id).single().execute().data or {}
        if prop.get("name"):            completed.add("name")
        if prop.get("description"):     completed.add("description")
        if prop.get("address"):         completed.add("address")
        if prop.get("units"):           completed.add("units")
        if prop.get("year_built"):      completed.add("year_built")
        if prop.get("website"):         completed.add("website")
        if prop.get("amenities"):       completed.add("amenities")
        if prop.get("go_live_date"):    completed.add("go_live_date")
        if prop.get("parking"):         completed.add("parking")

    elif section == "units_floor_plans":
        units = supabase.table("units") \
            .select("id,monthly_rent") \
            .eq("property_id", property_id).execute().data or []
        fps   = supabase.table("floorplans") \
            .select("id,square_footage") \
            .eq("property_id", property_id).execute().data or []
        if units:                          completed.add("units_added")
        if any(u.get("monthly_rent") for u in units): completed.add("pricing")
        if fps:                            completed.add("floor_plans")
        if any(f.get("square_footage") for f in fps): completed.add("square_footage")
        if fps:                            completed.add("bedrooms")

    elif section == "amenities":
        amenities = supabase.table("property_amenities") \
            .select("name,description") \
            .eq("property_id", property_id).execute().data or []
        if amenities:                            completed.add("amenities_list")
        if all(a.get("description") for a in amenities): completed.add("descriptions")

    elif section == "media_photos":
        prop_imgs = supabase.table("property_images") \
            .select("id,image_path") \
            .eq("property_id", property_id).execute().data or []
        unit_imgs = supabase.table("unit_images") \
            .select("id").execute().data or []
        if any("exterior" in img.get("image_path","") for img in prop_imgs): completed.add("exterior")
        if any("lobby" in img.get("image_path","") for img in prop_imgs):    completed.add("common_areas")
        if unit_imgs:                            completed.add("unit_photos")

    elif section == "content_faqs":
        faqs = supabase.table("property_faqs") \
            .select("category,answer,is_published") \
            .eq("property_id", property_id) \
            .eq("is_published", True).execute().data or []
        published_cats = {f["category"] for f in faqs if f.get("answer")}
        category_map = {
            "general":     ["general", "general_2", "general_3"],
            "pet_policy":  ["pet_policy"],
            "parking":     ["parking"],
            "utilities":   ["utilities"],
            "maintenance": ["maintenance"],
            "guest":       ["guest"],
            "noise":       ["noise"],
            "lease":       ["lease", "lease_2"],
            "move_in":     ["move_in"],
        }
        for cat, keys in category_map.items():
            if cat in published_cats:
                completed.update(keys)

    elif section == "integrations":
        integrations = supabase.table("property_integration_status") \
            .select("integration_name,status") \
            .eq("property_id", property_id) \
            .eq("status", "connected").execute().data or []
        completed.update(i["integration_name"] for i in integrations)

    return completed
