"""Theme frequency & trend analytics — Phase 5.

Computes:
  - Top themes ranked by review count
  - Theme distribution per source
  - Theme co-occurrence (which themes appear together most)
  - Theme × sentiment breakdown (e.g. "discovery" is 70% negative)
"""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations

from src.storage.models import EnrichedReview

logger = logging.getLogger(__name__)


def _get_themes(er: EnrichedReview) -> list[str]:
    if er.themes_json:
        try:
            return json.loads(er.themes_json)
        except (json.JSONDecodeError, TypeError):
            pass
    return []


def compute_top_themes(enriched: list[EnrichedReview], top_n: int = 20) -> list[dict]:
    """Rank themes by total mention count across all enriched reviews."""
    counter: Counter = Counter()
    for er in enriched:
        counter.update(_get_themes(er))
    total_reviews = len(enriched)
    return [
        {
            "theme": theme,
            "count": count,
            "pct_of_reviews": round(count / total_reviews * 100, 1) if total_reviews else 0,
        }
        for theme, count in counter.most_common(top_n)
    ]


def compute_themes_by_source(enriched: list[EnrichedReview]) -> dict:
    """For each source, rank its top themes."""
    source_counters: dict[str, Counter] = defaultdict(Counter)
    source_totals: dict[str, int] = Counter()

    for er in enriched:
        src = er.source
        source_counters[src].update(_get_themes(er))
        source_totals[src] += 1

    result: dict[str, list[dict]] = {}
    for src, counter in source_counters.items():
        total = source_totals[src]
        result[src] = [
            {
                "theme": theme,
                "count": count,
                "pct_of_source": round(count / total * 100, 1) if total else 0,
            }
            for theme, count in counter.most_common(10)
        ]
    return result


def compute_theme_sentiment(enriched: list[EnrichedReview]) -> dict:
    """For each theme, compute its sentiment breakdown."""
    theme_sentiments: dict[str, Counter] = defaultdict(Counter)

    for er in enriched:
        s = er.sentiment or "neutral"
        for theme in _get_themes(er):
            theme_sentiments[theme][s] += 1

    result: dict[str, dict] = {}
    for theme, counts in theme_sentiments.items():
        total = sum(counts.values())
        result[theme] = {
            "counts": dict(counts),
            "total": total,
            "dominant_sentiment": counts.most_common(1)[0][0] if counts else "neutral",
            "negativity_rate": round(counts.get("negative", 0) / total * 100, 1) if total else 0,
        }
    # Sort by total mentions descending
    return dict(sorted(result.items(), key=lambda x: -x[1]["total"]))


def compute_theme_cooccurrence(enriched: list[EnrichedReview], top_n: int = 15) -> list[dict]:
    """Find theme pairs that co-occur most frequently."""
    pair_counter: Counter = Counter()
    for er in enriched:
        themes = sorted(set(_get_themes(er)))
        for a, b in combinations(themes, 2):
            pair_counter[(a, b)] += 1
    return [
        {"theme_a": a, "theme_b": b, "count": count}
        for (a, b), count in pair_counter.most_common(top_n)
    ]


def compute_themes_over_time(
    enriched: list[EnrichedReview],
    clean_map: dict[int, datetime | None],
    top_themes: int = 5,
) -> dict:
    """Monthly trend lines for the top N themes (YYYY-MM → {theme: count})."""
    # Find top themes first
    counter: Counter = Counter()
    for er in enriched:
        counter.update(_get_themes(er))
    leading = [t for t, _ in counter.most_common(top_themes)]

    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {t: 0 for t in leading})
    for er in enriched:
        created = clean_map.get(er.clean_review_id)
        if not created:
            continue
        month = created.strftime("%Y-%m")
        for theme in _get_themes(er):
            if theme in buckets[month]:
                buckets[month][theme] += 1

    return dict(sorted(buckets.items()))


def run_theme_insights(
    enriched: list[EnrichedReview],
    clean_map: dict[int, datetime | None],
) -> dict:
    """Compute and return all theme insights as a single dict."""
    return {
        "top_themes": compute_top_themes(enriched),
        "by_source": compute_themes_by_source(enriched),
        "sentiment_breakdown": compute_theme_sentiment(enriched),
        "cooccurrence": compute_theme_cooccurrence(enriched),
        "over_time": compute_themes_over_time(enriched, clean_map),
    }
