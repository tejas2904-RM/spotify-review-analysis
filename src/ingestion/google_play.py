"""Google Play Store review collector.

Uses the `google-play-scraper` library to fetch app reviews and maps
them to the unified RawReview schema.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from src.ingestion.models import RawReview
from src.ingestion.utils import retry

logger = logging.getLogger(__name__)

SOURCE = "google_play"
STORE_URL = "https://play.google.com/store/apps/details?id={app_id}&hl={lang}"


def _make_id(app_id: str, review_id: str) -> str:
    raw = f"{app_id}:{review_id}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _parse_review(app_id: str, lang: str, raw: dict[str, Any]) -> RawReview | None:
    """Convert a google-play-scraper result dict to RawReview."""
    text: str = (raw.get("content") or "").strip()
    if not text:
        return None

    review_id = str(raw.get("reviewId") or _make_id(app_id, text[:64]))
    created_at: datetime | None = raw.get("at")

    metadata: dict[str, Any] = {}
    if raw.get("appVersion"):
        metadata["app_version"] = raw["appVersion"]

    return RawReview(
        external_id=review_id,
        source=SOURCE,
        text=text,
        source_url=STORE_URL.format(app_id=app_id, lang=lang),
        author=raw.get("userName"),
        rating=float(raw["score"]) if raw.get("score") is not None else None,
        likes=raw.get("thumbsUpCount"),
        created_at=created_at,
        metadata=metadata,
    )


@retry(max_attempts=3, base_delay=2.0, exceptions=(Exception,))
def _fetch_page(app_id: str, lang: str, country: str, count: int) -> list[dict]:
    from google_play_scraper import Sort, reviews

    result, _ = reviews(
        app_id,
        lang=lang,
        country=country,
        sort=Sort.NEWEST,
        count=count,
    )
    return result


def fetch(config: dict) -> list[RawReview]:
    """Fetch Google Play reviews as per config dict.

    Expected config keys:
        app_id (str): e.g. "com.spotify.music"
        lang (str): e.g. "en"
        country (str): e.g. "in"
        count (int): max reviews to fetch per batch (default 1000)
        days (int): only keep reviews from the last N days (default: all)
    """
    app_id: str = config["app_id"]
    lang: str = config.get("lang", "en")
    country: str = config.get("country", "us")
    count: int = int(config.get("count", 1000))
    days: int | None = config.get("days")

    cutoff: datetime | None = None
    if days:
        cutoff = datetime.utcnow() - timedelta(days=int(days))
        logger.info(
            "Fetching Google Play reviews for %s (last %d days, since %s)…",
            app_id, days, cutoff.date(),
        )
    else:
        logger.info("Fetching up to %d Google Play reviews for %s…", count, app_id)

    raw_list = _fetch_page(app_id, lang, country, count)

    reviews_out: list[RawReview] = []
    stopped_early = False
    for raw in raw_list:
        review = _parse_review(app_id, lang, raw)
        if not review:
            continue
        if cutoff and review.created_at and review.created_at < cutoff:
            # Reviews are sorted newest-first; once we pass the cutoff we can stop
            stopped_early = True
            break
        reviews_out.append(review)

    if stopped_early:
        logger.info(
            "Stopped at cutoff date. Collected %d Google Play reviews from the last %d days.",
            len(reviews_out), days,
        )
    else:
        logger.info("Collected %d Google Play reviews", len(reviews_out))

    return reviews_out
