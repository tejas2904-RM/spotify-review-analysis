"""User segment analytics — Phase 5.

Computes:
  - Segment distribution (casual / power_user / new_user / churn_risk / unknown)
  - Per-segment sentiment breakdown
  - Per-segment top themes and pain points
  - Churn-risk signal analysis
"""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict

from src.storage.models import EnrichedReview

logger = logging.getLogger(__name__)

_SEGMENTS = ("casual", "power_user", "new_user", "churn_risk", "unknown")


def compute_segment_distribution(enriched: list[EnrichedReview]) -> dict:
    """Count and percentage of each user segment."""
    counts: Counter = Counter(er.user_segment or "unknown" for er in enriched)
    total = len(enriched)
    return {
        seg: {
            "count": counts.get(seg, 0),
            "pct": round(counts.get(seg, 0) / total * 100, 1) if total else 0,
        }
        for seg in _SEGMENTS
    }


def compute_segment_sentiment(enriched: list[EnrichedReview]) -> dict:
    """Sentiment breakdown for each segment."""
    seg_sentiment: dict[str, Counter] = defaultdict(Counter)
    seg_scores: dict[str, list[float]] = defaultdict(list)

    for er in enriched:
        seg = er.user_segment or "unknown"
        seg_sentiment[seg][er.sentiment or "neutral"] += 1
        if er.sentiment_score is not None:
            seg_scores[seg].append(er.sentiment_score)

    result: dict[str, dict] = {}
    for seg, counts in seg_sentiment.items():
        total = sum(counts.values())
        scores = seg_scores[seg]
        result[seg] = {
            "sentiment_counts": dict(counts),
            "negativity_rate": round(counts.get("negative", 0) / total * 100, 1) if total else 0,
            "avg_score": round(sum(scores) / len(scores), 4) if scores else None,
        }
    return result


def compute_segment_themes(enriched: list[EnrichedReview], top_n: int = 8) -> dict:
    """Top themes for each user segment."""
    seg_themes: dict[str, Counter] = defaultdict(Counter)

    for er in enriched:
        seg = er.user_segment or "unknown"
        if er.themes_json:
            try:
                for t in json.loads(er.themes_json):
                    seg_themes[seg][t] += 1
            except (json.JSONDecodeError, TypeError):
                pass

    return {
        seg: [
            {"theme": t, "count": c}
            for t, c in counter.most_common(top_n)
        ]
        for seg, counter in seg_themes.items()
    }


def compute_segment_pain_points(enriched: list[EnrichedReview], top_n: int = 5) -> dict:
    """Most common pain points per segment."""
    seg_pains: dict[str, Counter] = defaultdict(Counter)

    for er in enriched:
        if not er.pain_point or len(er.pain_point.strip()) < 10:
            continue
        seg = er.user_segment or "unknown"
        key = er.pain_point.lower().strip()[:180]
        seg_pains[seg][key] += 1

    return {
        seg: [
            {"pain_point": p, "count": c}
            for p, c in counter.most_common(top_n)
        ]
        for seg, counter in seg_pains.items()
    }


def compute_churn_signals(enriched: list[EnrichedReview]) -> dict:
    """Deep-dive on churn-risk segment: emotions, themes, sources, pain points."""
    churn = [er for er in enriched if er.user_segment == "churn_risk"]
    if not churn:
        return {"count": 0}

    emotions: Counter = Counter(er.emotion or "neutral" for er in churn)
    themes: Counter = Counter()
    sources: Counter = Counter(er.source for er in churn)

    for er in churn:
        if er.themes_json:
            try:
                themes.update(json.loads(er.themes_json))
            except (json.JSONDecodeError, TypeError):
                pass

    return {
        "count": len(churn),
        "pct_of_total": round(len(churn) / len(enriched) * 100, 1) if enriched else 0,
        "top_emotions": dict(emotions.most_common(5)),
        "top_themes": dict(themes.most_common(8)),
        "by_source": dict(sources),
    }


def run_segment_insights(enriched: list[EnrichedReview]) -> dict:
    """Compute and return all segment insights as a single dict."""
    return {
        "distribution": compute_segment_distribution(enriched),
        "sentiment_by_segment": compute_segment_sentiment(enriched),
        "themes_by_segment": compute_segment_themes(enriched),
        "pain_points_by_segment": compute_segment_pain_points(enriched),
        "churn_signals": compute_churn_signals(enriched),
    }
