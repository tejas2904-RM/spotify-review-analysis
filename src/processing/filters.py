"""Spam and noise detection heuristics for Phase 2.

A review is flagged as spam / noise if it meets one or more of these criteria:
  - Too short after cleaning (< MIN_CHARS characters)
  - Entirely upper-case (shouting / automated)
  - Overwhelmingly emoji/punctuation with minimal alphabetic content
  - Repeating a single word or phrase excessively
  - Matches known promotional / bot boilerplate patterns
"""

from __future__ import annotations

import re
import unicodedata

MIN_CHARS = 15           # minimum meaningful review length
MIN_ALPHA_RATIO = 0.25   # at least 25% of chars must be alphabetic
MAX_WORD_REPEAT_RATIO = 0.6  # a single word can be at most 60% of all words

_PROMO_PATTERNS = re.compile(
    r"\b(click here|buy now|discount|promo code|limited offer|free trial"
    r"|subscribe now|visit our|check out our|follow us|dm us|link in bio"
    r"|download now|install now)\b",
    re.IGNORECASE,
)

_BOILERPLATE_PATTERNS = re.compile(
    r"^\s*(ok|okay|yes|no|nice|good|bad|ok+|k+|lol+|haha+|wow+|omg+)\s*[!.?]*\s*$",
    re.IGNORECASE,
)


def _alpha_ratio(text: str) -> float:
    if not text:
        return 0.0
    alpha = sum(1 for c in text if c.isalpha())
    return alpha / len(text)


def _dominant_word_ratio(text: str) -> float:
    """Return the fraction of tokens made up by the single most-repeated word."""
    words = text.lower().split()
    if not words:
        return 0.0
    counts: dict[str, int] = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return max(counts.values()) / len(words)


def is_spam(text: str) -> tuple[bool, str]:
    """Return (is_spam, reason). Reason is empty string when not spam."""
    stripped = text.strip()

    if len(stripped) < MIN_CHARS:
        return True, f"too_short ({len(stripped)} chars)"

    if _alpha_ratio(stripped) < MIN_ALPHA_RATIO:
        return True, f"low_alpha_ratio ({_alpha_ratio(stripped):.2f})"

    if stripped == stripped.upper() and len(stripped) > 30:
        return True, "all_caps"

    if _dominant_word_ratio(stripped) > MAX_WORD_REPEAT_RATIO and len(stripped.split()) > 5:
        return True, "repetitive_words"

    if _PROMO_PATTERNS.search(stripped):
        return True, "promotional_content"

    if _BOILERPLATE_PATTERNS.match(stripped):
        return True, "boilerplate"

    return False, ""
