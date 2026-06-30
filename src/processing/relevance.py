"""Relevance filtering for Phase 2 extended cleaning.

Scores each clean review against topic keyword groups covering:
  - Music discovery & Discover Weekly
  - Recommendation algorithm
  - Spotify Wrapped
  - Playlist & radio suggestions

A review is considered relevant if its total weighted score > 0.
The top-N most recent relevant reviews per source can then be selected.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword groups with weights
# Each entry: (compiled pattern, weight)
# Grouped by the 5 problem-statement themes.
# ---------------------------------------------------------------------------

_TOPIC_GROUPS: list[tuple[re.Pattern, float]] = [

    # ── Theme 1: Why users struggle to discover new music ──────────────────
    (re.compile(r"\bdiscover\s*weekly\b|\brelease\s*radar\b|\bdaily\s*mix\b", re.I), 3.0),
    (re.compile(r"\bdiscover(y|ing|ed)?\b|\bfind\s+new\b|\bnew\s+(music|songs?|artists?|bands?|tracks?)\b", re.I), 2.0),
    (re.compile(r"\bexplor(e|ing|ed)\b|\bnew\s+releases?\b|\bhidden\s+gems?\b|\bniche\b|\bobscure\b", re.I), 1.5),
    (re.compile(r"\bunderground\b|\bmainstream\b|\bsurface\b|\bcan'?t\s+find\b|\bnothing\s+new\b", re.I), 1.5),
    (re.compile(r"\bsame\s+old\b|\bbored\b|\bstale\b|\bgets?\s+old\b|\bmonotonous\b", re.I), 1.5),

    # ── Theme 2: Frustrations with recommendation system ───────────────────
    (re.compile(r"\balgorithm\b|\balgo\b|\balgorithmic\b", re.I), 3.0),
    (re.compile(r"\brecommend(ation|ed|s|ing)?\b|\bsuggestion(s)?\b|\bsuggested\b", re.I), 2.5),
    (re.compile(r"\bfor\s+you\b|\bpersonali[sz]ed?\b|\bcurated\b|\btailored\b", re.I), 2.0),
    (re.compile(r"\btaste\s*profile\b|\blistening\s+history\b|\bseed(s|ing)?\b|\bhistory\s+reset\b", re.I), 2.5),
    (re.compile(r"\boverplayed\b|\bstuck\b|\bloop(ing)?\b|\bnarrow\b|\bbroke[n]?\b", re.I), 1.5),
    (re.compile(r"\bused\s+to\s+be\b|\bgot\s+worse\b|\bruined\b|\bstopped\s+work\b|\bdegraded\b", re.I), 2.0),
    (re.compile(r"\bmix\b|\bradio\b|\bautoplay\b|\bblend\b|\bon\s+repeat\b|\btime\s+capsule\b", re.I), 1.0),

    # ── Theme 3: Listening behaviors that cause repetition ─────────────────
    (re.compile(r"\brepeat(s|ing|ed)?\b|\bsame\s+(songs?|music|tracks?|artists?)\b", re.I), 1.5),
    (re.compile(r"\bhabit\b|\bcomfort\s+zone\b|\bsafe\s+choice\b|\bfamiliar\b|\bgo-?to\b", re.I), 1.5),
    (re.compile(r"\bkeep\s+playing\b|\bcan'?t\s+stop\b|\baddicted\b|\bnever\s+leaves?\b", re.I), 1.0),
    (re.compile(r"\becho\s*chamber\b|\bfilter\s*bubble\b|\blocked\s+in\b|\btrapped\b", re.I), 2.0),
    (re.compile(r"\bdivers(e|ity)\b|\bvariet(y|ies)\b|\brange\b|\bbroad(er)?\b", re.I), 1.5),

    # ── Theme 4: User segments & churn signals ─────────────────────────────
    (re.compile(r"\bpremium\b|\bfree\s+tier\b|\bsubscri(be|ption|ber)\b", re.I), 1.0),
    (re.compile(r"\bswitch(ed|ing)?\b|\bmoved?\s+to\b|\bcancel(led|ing)?\b|\bchurn\b|\bleav(e|ing)\b", re.I), 2.0),
    (re.compile(r"\bapple\s+music\b|\byoutube\s+music\b|\btidal\b|\bamazon\s+music\b|\bdeezer\b", re.I), 2.5),
    (re.compile(r"\bcasual\b|\bpower\s+user\b|\bheavy\s+listener\b|\bstudent\b|\bfamily\s+plan\b", re.I), 1.0),

    # ── Theme 5: Unmet needs & feature requests ────────────────────────────
    (re.compile(r"\bwish\b|\bwould\s+love\b|\bplease\s+add\b|\bbring\s+back\b|\bfeature\s+request\b", re.I), 2.0),
    (re.compile(r"\bshould\s+(have|add|fix|allow|let)\b|\bneed\s+to\b|\bmust\s+(add|fix|improve)\b", re.I), 1.5),
    (re.compile(r"\bimprove\b|\bfix\b|\bmiss\s+the\b|\bused\s+to\s+have\b|\bwant\s+(a|to|more)\b", re.I), 1.0),
    (re.compile(r"\bfeature\b|\bupdate\b|\bchange\b|\ballow\s+us\b|\bgive\s+us\b|\blet\s+us\b", re.I), 0.8),

    # ── Spotify Wrapped & listening stats ──────────────────────────────────
    (re.compile(r"\bwrapped\b|\bspotify\s+wrapped\b|\byear\s+in\s+review\b|\bannual\s+(recap|review)\b", re.I), 3.0),
    (re.compile(r"\btop\s+(songs?|artists?|tracks?|genres?)\b|\bmost\s+played\b|\blistening\s+stats?\b", re.I), 1.5),
    (re.compile(r"\blistening\s+habits?\b|\bminutes?\s+listened\b|\bsummary\b|\byear(ly)?\s+stats?\b", re.I), 1.5),

    # ── General music taste & quality signals ───────────────────────────────
    (re.compile(r"\btaste\b|\bgenre\b|\bartist\b|\btrack\b|\bplaylist\b", re.I), 0.5),
    (re.compile(r"\bquality\b|\bcuration\b|\bexperience\b|\bengagement\b", re.I), 0.5),

    # ── Theme 6: Mood & context-based listening (→ repetition behavior) ────
    (re.compile(r"\bmood\b|\bvibe(s)?\b|\bworkout\b|\bchill\b|\bparty\b|\bstudy\b|\bfocus\b|\bsleep\b", re.I), 1.0),
    (re.compile(r"\bsad\s+music\b|\bhappy\s+music\b|\brelax\b|\benergy\b|\bbackground\b|\bdriving\b", re.I), 0.8),
    (re.compile(r"\bsession\b|\blistening\s+to\b|\bplaying\s+(music|songs?)\b|\bwhat\s+I\s+listen\b", re.I), 0.5),

    # ── Theme 7: Core Spotify feature interactions ─────────────────────────
    (re.compile(r"\bliked\s+songs?\b|\byour\s+library\b|\bsaved\b|\bfavorite(s)?\b|\bmy\s+library\b", re.I), 1.0),
    (re.compile(r"\bhome\s+(screen|page|tab)\b|\bbrowse\b|\bsearch\b|\bwhat'?s\s+new\b", re.I), 0.8),
    (re.compile(r"\bshuffle\b|\bskip(ping)?\b|\bqueue\b|\bnext\s+song\b|\bautoplay\b", re.I), 0.8),
    (re.compile(r"\boffline\b|\bdownload\b|\bcache\b|\bsync\b", re.I), 0.5),

    # ── Theme 8: User frustration & satisfaction signals ──────────────────
    (re.compile(r"\bfrustrat(ed|ing|ion)\b|\bannoy(ed|ing)\b|\bdisappoint(ed|ing)\b|\bdisgusted\b", re.I), 1.0),
    (re.compile(r"\bhate\b|\bterrible\b|\bawful\b|\bworst\b|\buninstall\b|\bdeleted?\b", re.I), 0.8),
    (re.compile(r"\blove\b|\bamazing\b|\bgreat\s+(app|music|feature)\b|\bperfect\b|\bexcellent\b", re.I), 0.5),

    # ── Theme 9: Comparative & competitive signals ─────────────────────────
    (re.compile(r"\bbetter\s+than\b|\bworse\s+than\b|\bcompared\s+to\b|\bunlike\b|\bvs\b", re.I), 0.8),
    (re.compile(r"\bused\s+to\s+(love|like|use|enjoy)\b|\bonce\s+was\b|\bback\s+when\b|\bremember\s+when\b", re.I), 1.5),

    # ── Theme 10: Engagement & retention signals ───────────────────────────
    (re.compile(r"\bevery\s+day\b|\bdaily\b|\ball\s+the\s+time\b|\bconstantly\b|\balways\b", re.I), 0.5),
    (re.compile(r"\bmonths?\b|\byears?\b|\blong\s+time\b|\bsince\s+(2|3|4|5|6|7|8|9|10)\b", re.I), 0.5),
    (re.compile(r"\bworth\s+(it|the|paying)\b|\bvalue\b|\bprice\b|\bpaying\s+for\b|\bsubscrib\b", re.I), 0.8),
]


@dataclass
class RelevanceResult:
    score: float
    matched_topics: list[str] = field(default_factory=list)


def score_review(text: str) -> RelevanceResult:
    """Score a single review text against all topic keyword groups.

    Returns a RelevanceResult with total score and matched topic names.
    """
    total = 0.0
    matched: list[str] = []

    for pattern, weight in _TOPIC_GROUPS:
        hits = pattern.findall(text)
        if hits:
            # Cap per-group contribution to avoid single-topic domination
            contribution = min(weight * len(hits), weight * 3)
            total += contribution
            matched.append(f"{pattern.pattern[:30]}(x{len(hits)})")

    return RelevanceResult(score=round(total, 2), matched_topics=matched)


def is_relevant(text: str, min_score: float = 1.0) -> bool:
    """Return True if the text scores above the minimum relevance threshold."""
    return score_review(text).score >= min_score


# ---------------------------------------------------------------------------
# Pipeline function
# ---------------------------------------------------------------------------

def tag_relevant_reviews(
    source: str = "google_play",
    top_n: int = 1000,
    min_score: float = 1.0,
) -> dict:
    """Score all non-spam clean reviews for a source, tag the top-N most
    recent ones as is_relevant=True.

    Args:
        source:    Source name to filter (default: 'google_play').
        top_n:     Maximum number of relevant reviews to tag.
        min_score: Minimum relevance score to be considered relevant.

    Returns:
        Stats dict.
    """
    from sqlalchemy import select, update

    from src.storage.db import get_session
    from src.storage.models import CleanReview

    stats = {
        "source": source,
        "total_checked": 0,
        "above_threshold": 0,
        "tagged_relevant": 0,
        "top_n": top_n,
        "min_score": min_score,
    }

    with get_session() as session:
        # Load non-spam clean reviews for this source, ordered newest first
        stmt = (
            select(CleanReview)
            .where(CleanReview.source == source)
            .where(CleanReview.is_spam == False)  # noqa: E712
            .order_by(CleanReview.created_at.desc().nullslast())
        )
        records = list(session.execute(stmt).scalars().all())
        stats["total_checked"] = len(records)
        logger.info("Scoring %d %s clean reviews for relevance…", len(records), source)

        # Score every review
        scored: list[tuple[CleanReview, float]] = []
        for cr in records:
            result = score_review(cr.clean_text)
            cr.relevance_score = result.score
            if result.score >= min_score:
                scored.append((cr, result.score))

        stats["above_threshold"] = len(scored)
        logger.info(
            "  %d / %d reviews scored above threshold (%.1f)",
            len(scored), len(records), min_score,
        )

        # Sort by (score desc, date desc) and take top_n
        scored.sort(key=lambda x: (x[1], x[0].created_at or 0), reverse=True)
        top = scored[:top_n]

        # Tag selected reviews
        relevant_ids = {cr.id for cr, _ in top}
        for cr in records:
            cr.is_relevant = cr.id in relevant_ids

        stats["tagged_relevant"] = len(relevant_ids)
        logger.info("Tagged %d reviews as relevant.", len(relevant_ids))

    return stats
