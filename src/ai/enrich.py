"""Per-review AI enrichment pipeline — Phase 4.

Processes every relevant, non-spam clean review through Groq Llama 3.3 70B
to extract sentiment, themes, feature requests, pain points, user segment,
and emotion. Results are persisted to the `enriched_reviews` table.

Mini-batching (5 reviews per LLM call) keeps throughput near the 30 RPM
free-tier limit (~12 min for 1,800 reviews) while staying well within TPM.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from src.ai.llm import call, load_cache, save_cache
from src.ai.prompts import ENRICH_SYSTEM, ENRICH_USER_TEMPLATE
from src.storage.repository import bulk_insert_enriched, get_unenriched_relevant

logger = logging.getLogger(__name__)

BATCH_SIZE = 5          # reviews per LLM call
SAVE_EVERY = 25         # flush DB + cache every N enriched records

_VALID_SENTIMENTS = {"positive", "neutral", "negative"}
_VALID_SEGMENTS = {"casual", "power_user", "new_user", "churn_risk", "unknown"}
_VALID_EMOTIONS = {
    "frustration", "delight", "confusion",
    "disappointment", "satisfaction", "neutral", "mixed",
}
_VALID_THEMES = {
    "discovery", "recommendations", "algorithm", "repetition", "playlist",
    "wrapped", "social", "pricing", "ads", "ui_ux", "offline", "podcasts",
    "competitor_comparison", "feature_request", "churn_risk", "mood_listening",
    "shuffle", "radio", "artist_discovery", "genre_exploration",
}


def _format_batch(reviews) -> str:
    lines = []
    for i, r in enumerate(reviews, 1):
        # Truncate to 600 chars to keep prompt within TPM budget
        text = r.clean_text[:600].replace("\n", " ")
        lines.append(f"[{i}] {text}")
    return "\n\n".join(lines)


def _sanitise(result: dict, review) -> dict:
    """Validate and clean one LLM result dict into an enriched_review record."""
    themes_raw = result.get("themes", [])
    themes = [t for t in (themes_raw if isinstance(themes_raw, list) else []) if t in _VALID_THEMES]

    sentiment = result.get("sentiment", "neutral")
    if sentiment not in _VALID_SENTIMENTS:
        sentiment = "neutral"

    try:
        score = float(result.get("sentiment_score", 0.5))
        score = max(0.0, min(1.0, score))
    except (TypeError, ValueError):
        score = 0.5

    segment = result.get("user_segment", "unknown")
    if segment not in _VALID_SEGMENTS:
        segment = "unknown"

    emotion = result.get("emotion", "neutral")
    if emotion not in _VALID_EMOTIONS:
        emotion = "neutral"

    feat_text = result.get("feature_request_text")
    if feat_text and len(feat_text) > 500:
        feat_text = feat_text[:500]

    pain = result.get("pain_point")
    if pain and len(pain) > 500:
        pain = pain[:500]

    return {
        "clean_review_id": review.id,
        "source": review.source,
        "sentiment": sentiment,
        "sentiment_score": score,
        "themes_json": json.dumps(themes),
        "is_feature_request": bool(result.get("is_feature_request", False)),
        "feature_request_text": feat_text or None,
        "pain_point": pain or None,
        "user_segment": segment,
        "emotion": emotion,
        "enriched_at": datetime.utcnow(),
    }


def run_enrichment(
    sources: list[str] | None = None,
    batch_size: int = BATCH_SIZE,
) -> int:
    """Enrich all unenriched relevant reviews with Groq Llama 3.3 70B.

    Args:
        sources:    Optional list of sources to restrict processing.
        batch_size: Number of reviews per LLM call (default 5).

    Returns:
        Total number of reviews successfully enriched.
    """
    load_cache()
    reviews = get_unenriched_relevant(sources=sources)

    if not reviews:
        logger.info("No reviews to enrich — all up to date.")
        return 0

    logger.info("Enriching %d reviews in batches of %d …", len(reviews), batch_size)

    pending: list[dict] = []
    total_enriched = 0
    total_batches = (len(reviews) + batch_size - 1) // batch_size

    for batch_idx, i in enumerate(range(0, len(reviews), batch_size), 1):
        batch = reviews[i : i + batch_size]
        user_prompt = ENRICH_USER_TEMPLATE.format(
            n=len(batch),
            reviews=_format_batch(batch),
        )

        try:
            raw = call(system=ENRICH_SYSTEM, user=user_prompt, max_tokens=1500, retries=6)
            results_list = raw.get("results", [])

            if not isinstance(results_list, list):
                logger.warning("Batch %d: unexpected response shape — skipping.", batch_idx)
                continue

            for j, review in enumerate(batch):
                if j < len(results_list):
                    pending.append(_sanitise(results_list[j], review))
                else:
                    logger.warning("Batch %d: no result for review index %d.", batch_idx, j)

        except Exception as exc:
            logger.error("Batch %d/%d failed: %s", batch_idx, total_batches, exc)
            continue

        # Flush to DB periodically
        if len(pending) >= SAVE_EVERY:
            inserted = bulk_insert_enriched(pending)
            total_enriched += inserted
            pending = []
            save_cache()
            logger.info(
                "Progress: %d/%d reviews enriched (batch %d/%d).",
                total_enriched, len(reviews), batch_idx, total_batches,
            )

    # Final flush
    if pending:
        total_enriched += bulk_insert_enriched(pending)
        save_cache()

    logger.info("Enrichment complete. Total enriched: %d.", total_enriched)
    return total_enriched
