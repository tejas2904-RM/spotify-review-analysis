"""Sentiment distribution analytics — Phase 5.

Computes:
  - Overall sentiment distribution (positive / neutral / negative counts + %)
  - Sentiment distribution per source
  - Sentiment distribution over time (monthly buckets)
  - Average sentiment score per source
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select

from src.storage.db import get_session
from src.storage.models import CleanReview, EnrichedReview

logger = logging.getLogger(__name__)

_SENTIMENTS = ("positive", "neutral", "negative")


def _pct(count: int, total: int) -> float:
    return round(count / total * 100, 1) if total else 0.0


def compute_overall(enriched: list[EnrichedReview]) -> dict:
    """Overall sentiment counts, percentages, and average score."""
    counts: dict[str, int] = {s: 0 for s in _SENTIMENTS}
    scores: list[float] = []

    for er in enriched:
        s = er.sentiment or "neutral"
        if s in counts:
            counts[s] += 1
        if er.sentiment_score is not None:
            scores.append(er.sentiment_score)

    total = len(enriched)
    return {
        "total": total,
        "counts": counts,
        "percentages": {s: _pct(counts[s], total) for s in _SENTIMENTS},
        "avg_score": round(sum(scores) / len(scores), 4) if scores else None,
    }


def compute_by_source(enriched: list[EnrichedReview]) -> dict:
    """Sentiment distribution broken down per source."""
    by_source: dict[str, dict] = defaultdict(lambda: {s: 0 for s in _SENTIMENTS})
    score_by_source: dict[str, list[float]] = defaultdict(list)

    for er in enriched:
        src = er.source
        s = er.sentiment or "neutral"
        if s in by_source[src]:
            by_source[src][s] += 1
        if er.sentiment_score is not None:
            score_by_source[src].append(er.sentiment_score)

    result: dict[str, dict] = {}
    for src, counts in by_source.items():
        total = sum(counts.values())
        scores = score_by_source[src]
        result[src] = {
            "total": total,
            "counts": dict(counts),
            "percentages": {s: _pct(counts[s], total) for s in _SENTIMENTS},
            "avg_score": round(sum(scores) / len(scores), 4) if scores else None,
        }
    return result


def compute_over_time(
    enriched: list[EnrichedReview],
    clean_map: dict[int, datetime | None],
) -> dict:
    """Monthly sentiment buckets (YYYY-MM → counts)."""
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {s: 0 for s in _SENTIMENTS})

    for er in enriched:
        created = clean_map.get(er.clean_review_id)
        if not created:
            continue
        month = created.strftime("%Y-%m")
        s = er.sentiment or "neutral"
        if s in buckets[month]:
            buckets[month][s] += 1

    # Sort chronologically
    return dict(sorted(buckets.items()))


def run_sentiment_insights(
    enriched: list[EnrichedReview],
    clean_map: dict[int, datetime | None],
) -> dict:
    """Compute and return all sentiment insights as a single dict."""
    return {
        "overall": compute_overall(enriched),
        "by_source": compute_by_source(enriched),
        "over_time": compute_over_time(enriched, clean_map),
    }
