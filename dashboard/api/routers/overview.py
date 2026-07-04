from fastapi import APIRouter
from sqlalchemy import select, func
from src.storage.repository import get_insight, db_summary
from src.storage.db import get_session
from src.storage.models import CleanReview, EnrichedReview

router = APIRouter()


def _get_counts():
    with get_session() as s:
        relevant = s.execute(
            select(func.count(CleanReview.id))
            .where(CleanReview.is_relevant == True)   # noqa: E712
            .where(CleanReview.is_spam == False)       # noqa: E712
        ).scalar() or 0
        enriched = s.execute(select(func.count(EnrichedReview.id))).scalar() or 0

        # Per-source relevant counts
        rows = s.execute(
            select(CleanReview.source, func.count(CleanReview.id))
            .where(CleanReview.is_relevant == True)    # noqa: E712
            .where(CleanReview.is_spam == False)       # noqa: E712
            .group_by(CleanReview.source)
        ).all()
        by_source = {row[0]: row[1] for row in rows}
        by_source["total"] = relevant
    return relevant, enriched, by_source


@router.get("")
def get_overview():
    sentiment = get_insight("sentiment_overall") or {}
    themes = get_insight("top_themes") or []
    segments = get_insight("segment_distribution") or {}
    churn = get_insight("churn_signals") or {}
    opportunities = get_insight("product_opportunities") or {}
    by_source_insight = get_insight("sentiment_by_source") or {}

    relevant_total, enriched_count, source_breakdown = _get_counts()

    # Fallback: when DB is empty (e.g. Render ephemeral env), read counts from
    # the pre-computed sentiment insight that was seeded from the snapshot.
    if relevant_total == 0 and sentiment:
        relevant_total = sentiment.get("total", 0)
        enriched_count = relevant_total  # all reviews were enriched

    if not source_breakdown or source_breakdown.get("total", 0) == 0:
        source_breakdown = {
            src: info["total"]
            for src, info in by_source_insight.items()
            if isinstance(info, dict) and "total" in info
        }
        source_breakdown["total"] = relevant_total

    pct = sentiment.get("percentages", {})
    counts = sentiment.get("counts", {})
    enrichment_pct = round(enriched_count / relevant_total * 100) if relevant_total else 0

    return {
        "kpis": {
            "total_reviews_analysed": relevant_total,
            "enriched_reviews": enriched_count,
            "enrichment_pct": enrichment_pct,
            "enrichment_complete": enriched_count >= relevant_total,
            "positive_pct": pct.get("positive", 0),
            "negative_pct": pct.get("negative", 0),
            "neutral_pct": pct.get("neutral", 0),
            "avg_sentiment_score": sentiment.get("avg_score"),
            "churn_risk_count": churn.get("count", 0),
            "churn_risk_pct": churn.get("pct_of_total", 0),
            "product_opportunities": len(opportunities.get("opportunities", [])),
        },
        "source_breakdown": source_breakdown,
        "top_themes": themes[:8],
        "sentiment_counts": counts,
        "segment_distribution": segments,
        "insights_ready": bool(sentiment),
    }
