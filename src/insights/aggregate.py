"""Phase 5 — Insights & Aggregation orchestrator.

Loads enriched + clean review data from the DB, runs all analytical
modules, generates product opportunities via LLM, and persists every
computed insight to the `insights` table.

Run via:
    python -m src.pipeline aggregate
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select

from src.storage.db import get_session
from src.storage.models import CleanReview, EnrichedReview
from src.storage.repository import save_insight

from src.insights.sentiment import run_sentiment_insights
from src.insights.themes import run_theme_insights
from src.insights.pain_points import run_pain_point_insights
from src.insights.segments import run_segment_insights
from src.insights.opportunities import compute_product_opportunities

logger = logging.getLogger(__name__)


def _load_data() -> tuple[list[EnrichedReview], dict[int, datetime | None]]:
    """Load all enriched reviews and a map of clean_review_id → created_at."""
    with get_session() as s:
        enriched = list(s.execute(select(EnrichedReview)).scalars().all())
        clean_rows = list(
            s.execute(
                select(CleanReview.id, CleanReview.created_at)
            ).all()
        )
    clean_map: dict[int, datetime | None] = {row.id: row.created_at for row in clean_rows}
    return enriched, clean_map


def run_aggregation() -> dict:
    """Run all Phase 5 aggregations.

    Returns a summary dict with counts of insights computed per category.
    """
    enriched, clean_map = _load_data()

    if not enriched:
        logger.warning(
            "No enriched reviews found — run `python -m src.pipeline enrich` first."
        )
        return {"enriched_count": 0}

    logger.info("Loaded %d enriched reviews for aggregation.", len(enriched))
    summary = {"enriched_count": len(enriched)}

    # ------------------------------------------------------------------
    # 1. Sentiment insights
    # ------------------------------------------------------------------
    logger.info("Computing sentiment insights …")
    sentiment_data = run_sentiment_insights(enriched, clean_map)
    save_insight("sentiment_overall", sentiment_data["overall"])
    save_insight("sentiment_by_source", sentiment_data["by_source"])
    save_insight("sentiment_over_time", sentiment_data["over_time"])
    summary["sentiment_metrics"] = 3
    logger.info(
        "  Overall: %d%% positive / %d%% neutral / %d%% negative",
        sentiment_data["overall"]["percentages"].get("positive", 0),
        sentiment_data["overall"]["percentages"].get("neutral", 0),
        sentiment_data["overall"]["percentages"].get("negative", 0),
    )

    # ------------------------------------------------------------------
    # 2. Theme insights
    # ------------------------------------------------------------------
    logger.info("Computing theme insights …")
    theme_data = run_theme_insights(enriched, clean_map)
    save_insight("top_themes", theme_data["top_themes"])
    save_insight("themes_by_source", theme_data["by_source"])
    save_insight("theme_sentiment_breakdown", theme_data["sentiment_breakdown"])
    save_insight("theme_cooccurrence", theme_data["cooccurrence"])
    save_insight("themes_over_time", theme_data["over_time"])
    summary["theme_metrics"] = 5
    top3 = [t["theme"] for t in theme_data["top_themes"][:3]]
    logger.info("  Top 3 themes: %s", ", ".join(top3))

    # ------------------------------------------------------------------
    # 3. Pain points & feature requests
    # ------------------------------------------------------------------
    logger.info("Computing pain point & feature request insights …")
    pain_data = run_pain_point_insights(enriched)
    save_insight("ranked_pain_points", pain_data["ranked_pain_points"])
    save_insight("ranked_feature_requests", pain_data["ranked_feature_requests"])
    save_insight("pain_points_by_theme", pain_data["pain_by_theme"])
    summary["pain_metrics"] = 3
    logger.info(
        "  %d distinct pain points / %d feature requests surfaced.",
        len(pain_data["ranked_pain_points"]),
        len(pain_data["ranked_feature_requests"]),
    )

    # ------------------------------------------------------------------
    # 4. User segment insights
    # ------------------------------------------------------------------
    logger.info("Computing user segment insights …")
    segment_data = run_segment_insights(enriched)
    save_insight("segment_distribution", segment_data["distribution"])
    save_insight("sentiment_by_segment", segment_data["sentiment_by_segment"])
    save_insight("themes_by_segment", segment_data["themes_by_segment"])
    save_insight("pain_points_by_segment", segment_data["pain_points_by_segment"])
    save_insight("churn_signals", segment_data["churn_signals"])
    summary["segment_metrics"] = 5
    churn_count = segment_data["churn_signals"].get("count", 0)
    churn_pct = segment_data["churn_signals"].get("pct_of_total", 0)
    logger.info("  Churn-risk users: %d (%.1f%% of enriched reviews)", churn_count, churn_pct)

    # ------------------------------------------------------------------
    # 5. Product opportunity recommendations (LLM)
    # ------------------------------------------------------------------
    logger.info("Generating LLM product opportunity recommendations …")
    opportunities = compute_product_opportunities(
        sentiment=sentiment_data,
        top_themes=theme_data["top_themes"],
        pain_points=pain_data["ranked_pain_points"],
        feature_requests=pain_data["ranked_feature_requests"],
        churn_signals=segment_data["churn_signals"],
        theme_sentiment=theme_data["sentiment_breakdown"],
    )
    n_opps = len(opportunities.get("opportunities", []))
    summary["product_opportunities"] = n_opps
    logger.info("  %d product opportunities generated.", n_opps)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total_insights = sum(
        v for k, v in summary.items()
        if k != "enriched_count" and isinstance(v, int)
    )
    summary["total_insights_saved"] = total_insights
    save_insight("aggregation_summary", summary)

    logger.info(
        "Aggregation complete. %d insight records saved to the insights table.",
        total_insights,
    )
    return summary


def print_summary(summary: dict) -> None:
    """Pretty-print the aggregation summary to stdout."""
    print("\n" + "=" * 55)
    print("  Phase 5 — Insights Aggregation Complete")
    print("=" * 55)
    print(f"  Enriched reviews processed : {summary.get('enriched_count', 0)}")
    print(f"  Sentiment metrics saved    : {summary.get('sentiment_metrics', 0)}")
    print(f"  Theme metrics saved        : {summary.get('theme_metrics', 0)}")
    print(f"  Pain point metrics saved   : {summary.get('pain_metrics', 0)}")
    print(f"  Segment metrics saved      : {summary.get('segment_metrics', 0)}")
    print(f"  Product opportunities      : {summary.get('product_opportunities', 0)}")
    print(f"  Total insight records      : {summary.get('total_insights_saved', 0)}")
    print("=" * 55 + "\n")
