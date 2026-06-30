"""Pain point and feature request analytics — Phase 5.

Computes:
  - Ranked pain points by frequency (with source distribution)
  - Ranked feature requests by frequency
  - Pain point × sentiment severity scoring
  - Feature request clusters by theme
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict

from src.storage.models import EnrichedReview

logger = logging.getLogger(__name__)

# Minimum character length to count a pain point as valid
_MIN_PAIN_LEN = 10


def _normalise_pain(text: str) -> str:
    """Light normalisation for grouping similar pain points."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text[:200]  # cap length for display


def compute_ranked_pain_points(
    enriched: list[EnrichedReview],
    top_n: int = 30,
) -> list[dict]:
    """Rank pain points by frequency × negativity weight.

    Each unique pain point string is counted; negative-sentiment reviews
    carry double weight to surface the most impactful complaints.
    """
    pain_counts: Counter = Counter()
    pain_sources: dict[str, Counter] = defaultdict(Counter)
    pain_sentiments: dict[str, Counter] = defaultdict(Counter)

    for er in enriched:
        raw = er.pain_point
        if not raw or len(raw.strip()) < _MIN_PAIN_LEN:
            continue
        key = _normalise_pain(raw)
        weight = 2 if er.sentiment == "negative" else 1
        pain_counts[key] += weight
        pain_sources[key][er.source] += 1
        pain_sentiments[key][er.sentiment or "neutral"] += 1

    results = []
    for pain, score in pain_counts.most_common(top_n):
        total_mentions = sum(pain_sources[pain].values())
        sentiments = dict(pain_sentiments[pain])
        results.append({
            "pain_point": pain,
            "weighted_score": score,
            "mention_count": total_mentions,
            "sources": dict(pain_sources[pain]),
            "sentiment_breakdown": sentiments,
            "negativity_rate": round(
                sentiments.get("negative", 0) / total_mentions * 100, 1
            ) if total_mentions else 0,
        })
    return results


def compute_ranked_feature_requests(
    enriched: list[EnrichedReview],
    top_n: int = 20,
) -> list[dict]:
    """Rank feature requests by frequency, grouped by associated themes."""
    fr_counts: Counter = Counter()
    fr_themes: dict[str, Counter] = defaultdict(Counter)
    fr_sources: dict[str, Counter] = defaultdict(Counter)

    for er in enriched:
        if not er.is_feature_request:
            continue
        raw = er.feature_request_text
        if not raw or len(raw.strip()) < _MIN_PAIN_LEN:
            continue
        key = _normalise_pain(raw)
        fr_counts[key] += 1
        fr_sources[key][er.source] += 1
        if er.themes_json:
            try:
                for t in json.loads(er.themes_json)[:2]:
                    fr_themes[key][t] += 1
            except (json.JSONDecodeError, TypeError):
                pass

    results = []
    for req, count in fr_counts.most_common(top_n):
        results.append({
            "feature_request": req,
            "count": count,
            "sources": dict(fr_sources[req]),
            "top_themes": [t for t, _ in fr_themes[req].most_common(3)],
        })
    return results


def compute_pain_by_theme(enriched: list[EnrichedReview]) -> dict:
    """For each theme, list its most common pain points."""
    theme_pains: dict[str, Counter] = defaultdict(Counter)

    for er in enriched:
        raw = er.pain_point
        if not raw or len(raw.strip()) < _MIN_PAIN_LEN:
            continue
        themes = []
        if er.themes_json:
            try:
                themes = json.loads(er.themes_json)[:2]
            except (json.JSONDecodeError, TypeError):
                pass
        key = _normalise_pain(raw)
        for t in themes:
            theme_pains[t][key] += 1

    return {
        theme: [
            {"pain_point": p, "count": c}
            for p, c in counter.most_common(5)
        ]
        for theme, counter in sorted(theme_pains.items(), key=lambda x: -sum(x[1].values()))
    }


def run_pain_point_insights(enriched: list[EnrichedReview]) -> dict:
    """Compute and return all pain point / feature request insights."""
    return {
        "ranked_pain_points": compute_ranked_pain_points(enriched),
        "ranked_feature_requests": compute_ranked_feature_requests(enriched),
        "pain_by_theme": compute_pain_by_theme(enriched),
    }
