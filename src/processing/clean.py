"""Phase 2 — Data Processing & Cleaning pipeline orchestrator.

Loads raw reviews that have not yet been cleaned, applies the full
cleaning pipeline, and writes results to the `clean_reviews` table.

Run via:
    python -m src.pipeline clean
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select

from src.processing.dedup import DedupeResult, deduplicate
from src.processing.filters import is_spam
from src.processing.text import clean_text, count_tokens
from src.storage.db import get_session
from src.storage.models import CleanReview, RawReview

logger = logging.getLogger(__name__)

# Language detection — graceful fallback if langdetect fails on short texts
try:
    from langdetect import detect as _ld_detect
    from langdetect import DetectorFactory
    DetectorFactory.seed = 42  # reproducible results

    def detect_language(text: str) -> str | None:
        try:
            return _ld_detect(text[:1000])
        except Exception:
            return None

except ImportError:
    logger.warning("langdetect not installed; language detection disabled.")

    def detect_language(text: str) -> str | None:  # type: ignore[misc]
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_unprocessed(session) -> list[RawReview]:
    """Return raw reviews that have no corresponding clean_review yet."""
    processed_ids_q = select(CleanReview.raw_review_id)
    stmt = select(RawReview).where(RawReview.id.not_in(processed_ids_q))
    return list(session.execute(stmt).scalars().all())


def _build_clean_review(raw: RawReview, cleaned: str, language: str | None, spam: bool) -> CleanReview:
    return CleanReview(
        raw_review_id=raw.id,
        source=raw.source,
        clean_text=cleaned,
        language=language,
        token_count=count_tokens(cleaned),
        is_spam=spam,
        created_at=raw.created_at,
        processed_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_cleaning() -> dict:
    """Execute the full Phase 2 cleaning pipeline.

    Returns a stats dict with counts for reporting.
    """
    stats: dict = {
        "total_raw": 0,
        "already_clean": 0,
        "empty_after_clean": 0,
        "spam": 0,
        "exact_dups": 0,
        "near_dups": 0,
        "inserted": 0,
        "by_source": defaultdict(lambda: {"processed": 0, "spam": 0, "dups": 0, "inserted": 0}),
    }

    with get_session() as session:
        raw_records = _load_unprocessed(session)
        stats["total_raw"] = len(raw_records)

        if not raw_records:
            logger.info("No unprocessed raw reviews found. Nothing to clean.")
            return stats

        logger.info("Loaded %d unprocessed raw reviews.", len(raw_records))

        # ---- Group by source for per-source near-dedup ----
        by_source: dict[str, list[RawReview]] = defaultdict(list)
        for r in raw_records:
            by_source[r.source].append(r)

        all_clean_reviews: list[CleanReview] = []

        for source, records in by_source.items():
            logger.info("--- Cleaning source: %s (%d records) ---", source, len(records))
            src_stats = stats["by_source"][source]
            src_stats["processed"] = len(records)

            # Step 1: clean text for each record
            cleaned_texts: list[str] = []
            valid_records: list[RawReview] = []

            for raw in records:
                cleaned = clean_text(raw.text)
                if not cleaned or len(cleaned.strip()) < 5:
                    stats["empty_after_clean"] += 1
                    logger.debug("Empty after clean: raw_id=%d", raw.id)
                    continue
                cleaned_texts.append(cleaned)
                valid_records.append(raw)

            # Step 2: dedup within source
            result: DedupeResult = deduplicate(cleaned_texts)
            stats["exact_dups"] += len(result.dropped_exact)
            stats["near_dups"] += len(result.dropped_near)
            src_stats["dups"] += len(result.dropped_exact) + len(result.dropped_near)
            logger.info(
                "  Dedup: %d kept, %d exact dups, %d near dups",
                len(result.kept), len(result.dropped_exact), len(result.dropped_near),
            )

            # Step 3: spam filter + language detect on kept records
            for idx in result.kept:
                raw = valid_records[idx]
                cleaned = cleaned_texts[idx]

                spam_flag, spam_reason = is_spam(cleaned)
                if spam_flag:
                    stats["spam"] += 1
                    src_stats["spam"] += 1
                    logger.debug("Spam (%s): raw_id=%d", spam_reason, raw.id)

                lang = detect_language(cleaned)
                cr = _build_clean_review(raw, cleaned, lang, spam_flag)
                all_clean_reviews.append(cr)
                src_stats["inserted"] += 1

        # Step 4: bulk insert
        if all_clean_reviews:
            session.add_all(all_clean_reviews)
            stats["inserted"] = len(all_clean_reviews)
            logger.info("Inserted %d clean reviews into clean_reviews table.", stats["inserted"])

    return stats


def print_stats(stats: dict) -> None:
    """Pretty-print cleaning stats."""
    logger.info("=" * 50)
    logger.info("Phase 2 Cleaning Summary")
    logger.info("=" * 50)
    logger.info("  Raw records processed : %d", stats["total_raw"])
    logger.info("  Empty after cleaning  : %d", stats["empty_after_clean"])
    logger.info("  Exact duplicates      : %d", stats["exact_dups"])
    logger.info("  Near duplicates       : %d", stats["near_dups"])
    logger.info("  Flagged as spam       : %d", stats["spam"])
    logger.info("  Inserted to DB        : %d", stats["inserted"])
    logger.info("-" * 50)
    for source, s in stats["by_source"].items():
        logger.info(
            "  [%s] processed=%d  spam=%d  dups=%d  inserted=%d",
            source, s["processed"], s["spam"], s["dups"], s["inserted"],
        )
    logger.info("=" * 50)
