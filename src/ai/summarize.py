"""LLM-generated summaries per theme and per source — Phase 4.

For each discovered theme (from enriched_reviews.themes_json) and each
data source, samples up to 20 representative reviews and asks Groq Llama
3.3 70B to produce an analytical summary with key issues and
product recommendations.

Summaries are persisted to the `insights` table:
  metric = "summary_theme_{theme}"   (e.g. "summary_theme_discovery")
  metric = "summary_source_{source}" (e.g. "summary_source_google_play")
"""

from __future__ import annotations

import json
import logging
import random
from collections import defaultdict

from sqlalchemy import select

from src.ai.llm import call, load_cache, save_cache
from src.ai.prompts import SUMMARIZE_SYSTEM, SUMMARIZE_USER_TEMPLATE
from src.storage.db import get_session
from src.storage.models import CleanReview, EnrichedReview
from src.storage.repository import save_insight

logger = logging.getLogger(__name__)

MAX_REVIEWS_PER_SUMMARY = 20
MIN_REVIEWS_FOR_SUMMARY = 5


def _fetch_data() -> tuple[dict[int, str], list[EnrichedReview]]:
    """Return (clean_id → clean_text map, all enriched review objects)."""
    with get_session() as s:
        clean_rows = list(
            s.execute(
                select(CleanReview).where(CleanReview.is_relevant == True)  # noqa: E712
            ).scalars().all()
        )
        enriched_rows = list(s.execute(select(EnrichedReview)).scalars().all())
    clean_map = {r.id: r.clean_text for r in clean_rows}
    return clean_map, enriched_rows


def _call_summary(label: str, texts: list[str]) -> dict:
    sample = random.sample(texts, min(MAX_REVIEWS_PER_SUMMARY, len(texts)))
    review_block = "\n".join(f"- {t[:300]}" for t in sample)
    user_prompt = SUMMARIZE_USER_TEMPLATE.format(
        label=label,
        n=len(sample),
        reviews=review_block,
    )
    try:
        result = call(SUMMARIZE_SYSTEM, user_prompt, max_tokens=900)
        # Ensure expected keys exist
        return {
            "summary": result.get("summary", ""),
            "key_issues": result.get("key_issues", []),
            "recommendations": result.get("recommendations", []),
            "review_count": len(texts),
        }
    except Exception as exc:
        logger.error("Summary failed for '%s': %s", label, exc)
        return {"summary": "", "key_issues": [], "recommendations": [], "review_count": len(texts)}


def run_summarization() -> int:
    """Generate and persist per-theme and per-source summaries.

    Returns:
        Number of summaries saved to the insights table.
    """
    load_cache()
    clean_map, enriched_rows = _fetch_data()

    theme_texts: dict[str, list[str]] = defaultdict(list)
    source_texts: dict[str, list[str]] = defaultdict(list)

    for er in enriched_rows:
        text = clean_map.get(er.clean_review_id, "")
        if not text:
            continue
        # Top 2 themes per review
        themes = json.loads(er.themes_json) if er.themes_json else []
        for t in themes[:2]:
            theme_texts[t].append(text)
        source_texts[er.source].append(text)

    count = 0

    # Theme summaries
    for theme, texts in sorted(theme_texts.items(), key=lambda x: -len(x[1])):
        if len(texts) < MIN_REVIEWS_FOR_SUMMARY:
            logger.debug("Skipping theme '%s' — only %d reviews.", theme, len(texts))
            continue
        label = theme.replace("_", " ").title()
        logger.info("Summarising theme: %s (%d reviews) …", label, len(texts))
        summary = _call_summary(label, texts)
        save_insight(f"summary_theme_{theme}", summary)
        count += 1

    # Source summaries
    for source, texts in sorted(source_texts.items(), key=lambda x: -len(x[1])):
        if len(texts) < MIN_REVIEWS_FOR_SUMMARY:
            logger.debug("Skipping source '%s' — only %d reviews.", source, len(texts))
            continue
        label = source.replace("_", " ").title()
        logger.info("Summarising source: %s (%d reviews) …", label, len(texts))
        summary = _call_summary(label, texts)
        save_insight(f"summary_source_{source}", summary)
        count += 1

    save_cache()
    logger.info("Summarization complete. %d summaries saved.", count)
    return count
