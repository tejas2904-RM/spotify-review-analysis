"""Database engine, session factory, and repository helpers."""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from src.storage.models import Base, RawReview

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = os.getenv("DB_URL", "sqlite:///data/reviews.db")
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _engine = create_engine(db_url, connect_args=connect_args, echo=False)
        Base.metadata.create_all(_engine)
        logger.info("Database initialised at %s", db_url)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def upsert_raw_reviews(reviews: list[dict]) -> int:
    """Insert records; skip duplicates on (source, external_id). Returns inserted count."""
    if not reviews:
        return 0

    inserted = 0
    with get_session() as session:
        for review in reviews:
            stmt = (
                sqlite_insert(RawReview)
                .values(**review)
                .on_conflict_do_nothing(index_elements=["source", "external_id"])
            )
            result = session.execute(stmt)
            inserted += result.rowcount

    logger.info("Upserted %d / %d raw reviews", inserted, len(reviews))
    return inserted


def get_all_raw_reviews(source: str | None = None) -> list[RawReview]:
    """Return all raw reviews, optionally filtered by source."""
    with get_session() as session:
        stmt = select(RawReview)
        if source:
            stmt = stmt.where(RawReview.source == source)
        return session.execute(stmt).scalars().all()


def get_unprocessed_raw_reviews() -> list[RawReview]:
    """Return raw reviews that have no corresponding clean_review yet."""
    from src.storage.models import CleanReview

    with get_session() as session:
        processed_ids = select(CleanReview.raw_review_id)
        stmt = select(RawReview).where(RawReview.id.not_in(processed_ids))
        return session.execute(stmt).scalars().all()
