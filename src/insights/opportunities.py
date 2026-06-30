"""LLM-generated product opportunity recommendations — Phase 5.

Synthesises the aggregated insights (top pain points, feature requests,
churn signals, theme sentiments) into a prioritised list of product
opportunities with supporting evidence.

Saved to insights table as metric `product_opportunities`.
"""

from __future__ import annotations

import json
import logging

from src.ai.llm import call, load_cache, save_cache
from src.storage.repository import save_insight

logger = logging.getLogger(__name__)

OPPORTUNITIES_SYSTEM = """\
You are a senior product strategist for Spotify's Growth & Discovery team.
You have been given aggregated analysis of user feedback from multiple sources
(Google Play reviews, YouTube comments, Spotify Community, Hacker News).

Based on the data provided, generate a prioritised list of product opportunities.
Each opportunity must be grounded in specific evidence from the data.

Respond with valid JSON only:
{
  "opportunities": [
    {
      "title": "short opportunity title",
      "priority": "high | medium | low",
      "problem_statement": "what users are experiencing (1-2 sentences)",
      "evidence": ["evidence point 1", "evidence point 2"],
      "recommendation": "specific actionable product change (2-3 sentences)",
      "affected_segments": ["casual", "power_user", "churn_risk"],
      "themes": ["discovery", "recommendations"]
    }
  ]
}

Prioritise by: (frequency of complaint) × (sentiment negativity) × (churn risk signal).
Generate 5-8 opportunities.
"""


def _build_context(
    sentiment: dict,
    top_themes: list[dict],
    pain_points: list[dict],
    feature_requests: list[dict],
    churn_signals: dict,
    theme_sentiment: dict,
) -> str:
    """Compress aggregated data into a concise LLM-digestible context block."""
    lines = ["=== AGGREGATED SPOTIFY USER FEEDBACK ANALYSIS ===\n"]

    # Sentiment overview
    ov = sentiment.get("overall", {})
    lines.append(f"TOTAL ENRICHED REVIEWS: {ov.get('total', 0)}")
    pct = ov.get("percentages", {})
    lines.append(
        f"SENTIMENT: {pct.get('positive', 0)}% positive | "
        f"{pct.get('neutral', 0)}% neutral | "
        f"{pct.get('negative', 0)}% negative"
    )

    # Top themes
    lines.append("\nTOP THEMES (by mention count):")
    for t in top_themes[:10]:
        ts = theme_sentiment.get(t["theme"], {})
        neg_rate = ts.get("negativity_rate", 0)
        lines.append(f"  - {t['theme']}: {t['count']} mentions ({neg_rate}% negative)")

    # Top pain points
    lines.append("\nTOP PAIN POINTS (weighted by negativity):")
    for p in pain_points[:10]:
        lines.append(
            f"  - [{p['weighted_score']} score, {p['mention_count']} mentions] "
            f"{p['pain_point']}"
        )

    # Feature requests
    lines.append("\nTOP FEATURE REQUESTS:")
    for fr in feature_requests[:8]:
        lines.append(f"  - [{fr['count']} mentions] {fr['feature_request']}")

    # Churn signals
    churn_count = churn_signals.get("count", 0)
    churn_pct = churn_signals.get("pct_of_total", 0)
    lines.append(
        f"\nCHURN-RISK USERS: {churn_count} ({churn_pct}% of enriched reviews)"
    )
    churn_themes = churn_signals.get("top_themes", {})
    if churn_themes:
        top_churn = list(churn_themes.items())[:5]
        lines.append(
            "Churn-risk top themes: " +
            ", ".join(f"{t}({c})" for t, c in top_churn)
        )

    return "\n".join(lines)


def compute_product_opportunities(
    sentiment: dict,
    top_themes: list[dict],
    pain_points: list[dict],
    feature_requests: list[dict],
    churn_signals: dict,
    theme_sentiment: dict,
) -> dict:
    """Generate prioritised product opportunities using Groq Llama 3.3 70B."""
    load_cache()
    context = _build_context(
        sentiment, top_themes, pain_points,
        feature_requests, churn_signals, theme_sentiment,
    )

    logger.info("Generating product opportunity recommendations …")
    try:
        result = call(
            system=OPPORTUNITIES_SYSTEM,
            user=context,
            max_tokens=2000,
            temperature=0.2,   # slight creativity for recommendations
        )
        opportunities = result if isinstance(result, dict) else {"opportunities": []}
    except Exception as exc:
        logger.error("Product opportunities LLM call failed: %s", exc)
        opportunities = {"opportunities": [], "error": str(exc)}

    save_cache()
    save_insight("product_opportunities", opportunities)
    logger.info(
        "Generated %d product opportunities.",
        len(opportunities.get("opportunities", [])),
    )
    return opportunities
