import logging
import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_TLS_QUERY_KEYS_STRIP = frozenset(
    {
        "tlsallowinvalidcertificates",
        "tlsallowinvalidhostnames",
        "tlsdisableocspendpointcheck",
        "tlsinsecure",
    }
)


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _apply_tls_patch() -> None:
    if not (
        _env_flag("MONGO_TLS_RELAXED")
        or _env_flag("MONGO_TLS_TLS12_ONLY")
        or _env_flag("MONGO_TLS_SECLEVEL_1")
    ):
        return
    import ssl

    import pymongo.client_options as co
    import pymongo.ssl_support as ss

    _orig = ss.get_ssl_context

    def _patched(
        certfile,
        passphrase,
        ca_certs,
        crlfile,
        allow_invalid_certificates,
        allow_invalid_hostnames,
        disable_ocsp_endpoint_check,
        is_sync,
    ):
        ctx = _orig(
            certfile,
            passphrase,
            ca_certs,
            crlfile,
            allow_invalid_certificates,
            allow_invalid_hostnames,
            disable_ocsp_endpoint_check,
            is_sync,
        )
        if _env_flag("MONGO_TLS_RELAXED") or _env_flag("MONGO_TLS_TLS12_ONLY"):
            try:
                ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                ctx.maximum_version = ssl.TLSVersion.TLSv1_2
            except (AttributeError, ValueError):
                pass
        if _env_flag("MONGO_TLS_RELAXED") or _env_flag("MONGO_TLS_SECLEVEL_1"):
            try:
                ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
            except ssl.SSLError:
                pass
        if _env_flag("MONGO_TLS_RELAXED") and hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
            ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT  # type: ignore[attr-defined]
        return ctx

    ss.get_ssl_context = _patched
    co.get_ssl_context = _patched


_apply_tls_patch()

import certifi
from beanie import init_beanie
from pymongo import AsyncMongoClient

from models.booking_model import Booking
from models.booking_payment_model import BookingPayment
from models.city_model import City
from models.feedback_model import Feedback
from models.floorplan_model import Floorplan
from models.lead_model import Lead
from models.property_image_model import PropertyImage
from models.property_model import Property
from models.prospect_event_model import ProspectEvent
from models.prospect_model import Prospect
from models.space_model import Space
from models.tour_model import Tour
from models.tour_step_model import TourStep
from models.unit_image_model import UnitImage
from models.unit_model import Unit
from models.user_model import User

DEFAULT_MONGO_URL = "mongodb://localhost:27017"
DEFAULT_DB_NAME = "aigentless"

_client: AsyncMongoClient | None = None
_db_ready = False


def get_mongo_url() -> str:
    return os.getenv("MONGO_URL", DEFAULT_MONGO_URL).strip() or DEFAULT_MONGO_URL


def get_db_name() -> str:
    return os.getenv("DB_NAME", DEFAULT_DB_NAME).strip() or DEFAULT_DB_NAME


def _mongo_uses_tls(url: str) -> bool:
    u = url.lower()
    return "mongodb+srv://" in u or "tls=true" in u or "ssl=true" in u


def _mongo_url_stripped(raw: str, strip: bool) -> str:
    if not strip:
        return raw
    p = urlparse(raw)
    if not p.query:
        return raw
    pairs = [
        (k, v)
        for k, v in parse_qsl(p.query, keep_blank_values=True)
        if k.lower() not in _TLS_QUERY_KEYS_STRIP
    ]
    return urlunparse(p._replace(query=urlencode(pairs)))


def _client_kwargs(relaxed: bool, allow_invalid_only: bool) -> dict:
    raw = get_mongo_url()
    opts: dict = {
        "serverSelectionTimeoutMS": int(
            os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "10000")
        ),
    }
    if relaxed:
        logger.warning(
            "MONGO_TLS_RELAXED: weaker TLS (Atlas on restrictive networks / dev only)."
        )
        opts["tlsInsecure"] = True
    elif allow_invalid_only:
        opts["tlsAllowInvalidCertificates"] = True
    elif _mongo_uses_tls(raw):
        opts["tlsCAFile"] = certifi.where()
    if _env_flag("MONGO_TLS_DISABLE_OCSP") and not relaxed and not allow_invalid_only:
        opts["tlsDisableOCSPEndpointCheck"] = True
    return opts


def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        relaxed = _env_flag("MONGO_TLS_RELAXED")
        allow_invalid = not relaxed and _env_flag("MONGO_TLS_ALLOW_INVALID_CERTS")
        raw = get_mongo_url()
        url = _mongo_url_stripped(raw, relaxed or allow_invalid)
        _client = AsyncMongoClient(url, **_client_kwargs(relaxed, allow_invalid))
    return _client


def db_is_ready() -> bool:
    return _db_ready


async def init_db() -> None:
    global _db_ready
    client = get_client()
    db = client[get_db_name()]
    await init_beanie(
        database=db,
        document_models=[
            User,
            Lead,
            Booking,
            BookingPayment,
            City,
            Feedback,
            Floorplan,
            Property,
            PropertyImage,
            Prospect,
            ProspectEvent,
            Space,
            Tour,
            TourStep,
            Unit,
            UnitImage,
        ],
    )
    _db_ready = True


async def startup_database() -> bool:
    global _db_ready
    _db_ready = False
    if _env_flag("DB_OPTIONAL_STARTUP"):
        try:
            await init_db()
            return True
        except Exception:
            logger.exception(
                "MongoDB init failed (DB_OPTIONAL_STARTUP=true — API still runs). "
                "Try local: MONGO_URL=mongodb://127.0.0.1:27017 and docker compose up -d mongo."
            )
            await close_db()
            return False
    await init_db()
    return True


async def close_db() -> None:
    global _client, _db_ready
    _db_ready = False
    if _client is not None:
        try:
            await _client.close()
        except Exception:
            pass
        _client = None
