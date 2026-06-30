"""Centralised repository helpers for all pipeline stages.

All database read/write access should go through these functions so
business logic never constructs raw SQLAlchemy queries directly.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from src.storage.db import get_session
from src.storage.models import CleanReview, EnrichedReview, Insight, RawReview

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Raw reviews
# ---------------------------------------------------------------------------

def get_all_raw(source: str | None = None) -> list[RawReview]:
    with get_session() as s:
        stmt = select(RawReview)
        if source:
            stmt = stmt.where(RawReview.source == source)
        return list(s.execute(stmt).scalars().all())


def count_raw(source: str | None = None) -> int:
    from sqlalchemy import func
    with get_session() as s:
        stmt = select(func.count(RawReview.id))
        if source:
            stmt = stmt.where(RawReview.source == source)
        return s.execute(stmt).scalar() or 0


# ---------------------------------------------------------------------------
# Clean reviews
# ---------------------------------------------------------------------------

def get_relevant_clean(
    sources: list[str] | None = None,
    include_spam: bool = False,
    limit: int | None = None,
) -> list[CleanReview]:
    """Return relevant clean reviews, optionally filtered by source."""
    with get_session() as s:
        stmt = select(CleanReview).where(CleanReview.is_relevant == True)  # noqa: E712
        if not include_spam:
            stmt = stmt.where(CleanReview.is_spam == False)  # noqa: E712
        if sources:
            stmt = stmt.where(CleanReview.source.in_(sources))
        stmt = stmt.order_by(CleanReview.created_at.desc().nullslast())
        if limit:
            stmt = stmt.limit(limit)
        return list(s.execute(stmt).scalars().all())


def get_unenriched_relevant(sources: list[str] | None = None) -> list[CleanReview]:
    """Return relevant clean reviews that have no enriched_review yet."""
    with get_session() as s:
        enriched_ids = select(EnrichedReview.clean_review_id)
        stmt = (
            select(CleanReview)
            .where(CleanReview.is_relevant == True)  # noqa: E712
            .where(CleanReview.is_spam == False)  # noqa: E712
            .where(CleanReview.id.not_in(enriched_ids))
        )
        if sources:
            stmt = stmt.where(CleanReview.source.in_(sources))
        return list(s.execute(stmt).scalars().all())


def count_clean(
    source: str | None = None,
    relevant_only: bool = False,
    exclude_spam: bool = True,
) -> int:
    from sqlalchemy import func
    with get_session() as s:
        stmt = select(func.count(CleanReview.id))
        if source:
            stmt = stmt.where(CleanReview.source == source)
        if relevant_only:
            stmt = stmt.where(CleanReview.is_relevant == True)  # noqa: E712
        if exclude_spam:
            stmt = stmt.where(CleanReview.is_spam == False)  # noqa: E712
        return s.execute(stmt).scalar() or 0


# ---------------------------------------------------------------------------
# Enriched reviews
# ---------------------------------------------------------------------------

def bulk_insert_enriched(records: list[dict[str, Any]]) -> int:
    """Insert enriched review dicts into enriched_reviews. Returns inserted count."""
    if not records:
        return 0
    with get_session() as s:
        objs = [EnrichedReview(**r) for r in records]
        s.add_all(objs)
    logger.info("Inserted %d enriched reviews.", len(records))
    return len(records)


def get_enriched(source: str | None = None) -> list[EnrichedReview]:
    with get_session() as s:
        stmt = select(EnrichedReview)
        if source:
            stmt = stmt.where(EnrichedReview.source == source)
        return list(s.execute(stmt).scalars().all())


def count_enriched(source: str | None = None) -> int:
    from sqlalchemy import func
    with get_session() as s:
        stmt = select(func.count(EnrichedReview.id))
        if source:
            stmt = stmt.where(EnrichedReview.source == source)
        return s.execute(stmt).scalar() or 0


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

def save_insight(metric: str, value: Any, filters: dict | None = None) -> None:
    """Upsert a computed insight into the insights table."""
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    filters_json = json.dumps(filters or {}, sort_keys=True)
    value_json = json.dumps(value)

    with get_session() as s:
        # Try update first, then insert
        existing = s.execute(
            select(Insight)
            .where(Insight.metric == metric)
            .where(Insight.filters_json == filters_json)
        ).scalar_one_or_none()

        if existing:
            existing.value_json = value_json
            existing.computed_at = datetime.utcnow()
        else:
            s.add(Insight(
                metric=metric,
                filters_json=filters_json,
                value_json=value_json,
                computed_at=datetime.utcnow(),
            ))


def get_insight(metric: str, filters: dict | None = None) -> Any | None:
    """Retrieve a cached insight value, or None if not found."""
    filters_json = json.dumps(filters or {}, sort_keys=True)
    with get_session() as s:
        row = s.execute(
            select(Insight)
            .where(Insight.metric == metric)
            .where(Insight.filters_json == filters_json)
        ).scalar_one_or_none()
        return json.loads(row.value_json) if row else None


def get_all_insights() -> list[Insight]:
    with get_session() as s:
        return list(s.execute(select(Insight)).scalars().all())


# ---------------------------------------------------------------------------
# DB summary
# ---------------------------------------------------------------------------

def db_summary() -> dict[str, Any]:
    """Return a concise summary of record counts across all tables."""
    from sqlalchemy import func
    sources = ["google_play", "youtube", "hacker_news", "spotify_community"]
    summary: dict[str, Any] = {"raw": {}, "clean": {}, "enriched": {}, "insights": 0}

    with get_session() as s:
        for src in sources:
            summary["raw"][src] = s.execute(
                select(func.count(RawReview.id)).where(RawReview.source == src)
            ).scalar()
            summary["clean"][src] = s.execute(
                select(func.count(CleanReview.id)).where(CleanReview.source == src)
            ).scalar()
            summary["enriched"][src] = s.execute(
                select(func.count(EnrichedReview.id)).where(EnrichedReview.source == src)
            ).scalar()
        summary["insights"] = s.execute(select(func.count(Insight.id))).scalar()

    summary["raw"]["total"] = sum(summary["raw"].values())
    summary["clean"]["total"] = sum(summary["clean"].values())
    summary["enriched"]["total"] = sum(summary["enriched"].values())
    return summary
