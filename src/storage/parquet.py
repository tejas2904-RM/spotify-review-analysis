"""Parquet export/import for raw and clean review archives.

Provides cheap, columnar snapshots of each pipeline stage for
reproducibility and offline analysis. Files land in:
    data/raw/raw_reviews.parquet
    data/clean/clean_reviews.parquet
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from src.storage.db import get_session
from src.storage.models import CleanReview, RawReview

logger = logging.getLogger(__name__)

_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATA_DIR = Path(os.getenv("DATA_DIR", str(_ROOT / "data")))
RAW_PARQUET = DATA_DIR / "raw" / "raw_reviews.parquet"
CLEAN_PARQUET = DATA_DIR / "clean" / "clean_reviews.parquet"


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _raw_to_dict(r: RawReview) -> dict:
    return {
        "id": r.id,
        "external_id": r.external_id,
        "source": r.source,
        "source_url": r.source_url,
        "author": r.author,
        "text": r.text,
        "rating": r.rating,
        "likes": r.likes,
        "created_at": r.created_at,
        "ingested_at": r.ingested_at,
    }


def _clean_to_dict(c: CleanReview) -> dict:
    return {
        "id": c.id,
        "raw_review_id": c.raw_review_id,
        "source": c.source,
        "clean_text": c.clean_text,
        "language": c.language,
        "token_count": c.token_count,
        "is_spam": c.is_spam,
        "is_relevant": c.is_relevant,
        "relevance_score": c.relevance_score,
        "created_at": c.created_at,
        "processed_at": c.processed_at,
    }


def export_raw(path: Path | None = None) -> Path:
    """Export raw_reviews table to Parquet. Returns output path."""
    out = Path(path or RAW_PARQUET)
    out.parent.mkdir(parents=True, exist_ok=True)

    with get_session() as s:
        records = list(s.execute(select(RawReview)).scalars().all())

    df = pd.DataFrame([_raw_to_dict(r) for r in records])
    df.to_parquet(out, index=False, engine="pyarrow")
    logger.info("Exported %d raw reviews → %s", len(df), out)
    return out


def export_clean(path: Path | None = None) -> Path:
    """Export clean_reviews table to Parquet. Returns output path."""
    out = Path(path or CLEAN_PARQUET)
    out.parent.mkdir(parents=True, exist_ok=True)

    with get_session() as s:
        records = list(s.execute(select(CleanReview)).scalars().all())

    df = pd.DataFrame([_clean_to_dict(c) for c in records])
    df.to_parquet(out, index=False, engine="pyarrow")
    logger.info("Exported %d clean reviews → %s", len(df), out)
    return out


def export_all() -> dict[str, Path]:
    """Export both tables and return paths."""
    return {
        "raw": export_raw(),
        "clean": export_clean(),
    }


# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------

def load_raw_parquet(path: Path | None = None) -> pd.DataFrame:
    """Load raw_reviews Parquet into a DataFrame."""
    p = Path(path or RAW_PARQUET)
    if not p.exists():
        raise FileNotFoundError(f"Parquet file not found: {p}")
    df = pd.read_parquet(p, engine="pyarrow")
    logger.info("Loaded %d raw reviews from %s", len(df), p)
    return df


def load_clean_parquet(
    path: Path | None = None,
    relevant_only: bool = False,
    exclude_spam: bool = True,
) -> pd.DataFrame:
    """Load clean_reviews Parquet into a DataFrame with optional filters."""
    p = Path(path or CLEAN_PARQUET)
    if not p.exists():
        raise FileNotFoundError(f"Parquet file not found: {p}")
    df = pd.read_parquet(p, engine="pyarrow")
    if exclude_spam:
        df = df[df["is_spam"] == False]  # noqa: E712
    if relevant_only:
        df = df[df["is_relevant"] == True]  # noqa: E712
    logger.info(
        "Loaded %d clean reviews from %s (relevant_only=%s, exclude_spam=%s)",
        len(df), p, relevant_only, exclude_spam,
    )
    return df
