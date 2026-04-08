"""
FastAPI Scheduled Job
Recalculates onboarding completion % every 5 minutes
Option B — FastAPI Scheduled Job (as decided)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from app.db import supabase
import logging

logger = logging.getLogger(__name__)

def recalculate_all_properties():
    """
    Every 5 minutes:
    - Fetch all property IDs
    - Call recalculate_onboarding_status() for each
    - Updates property_onboarding_status table
    """
    try:
        props = supabase.table("properties").select("id, name").execute().data or []
        for prop in props:
            supabase.rpc(
                "recalculate_onboarding_status",
                {"p_property_id": prop["id"]}
            ).execute()
        logger.info(f"Recalculated onboarding status for {len(props)} properties")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")

def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        recalculate_all_properties,
        trigger="interval",
        minutes=5,
        id="recalculate_onboarding",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — recalculating every 5 minutes")
    return scheduler
