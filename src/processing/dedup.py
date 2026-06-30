"""Deduplication utilities for Phase 2.

Two strategies:
  1. Exact dedup  — MD5 hash of normalised lowercase text.
  2. Near dedup   — rapidfuzz token_sort_ratio ≥ threshold (default 92).

Near-dedup is applied within each source separately to avoid
cross-source false positives (e.g. the same boilerplate reply
appearing on HN and Google Play would be coincidental, not a dupe).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

NEAR_DUP_THRESHOLD = 92   # 0-100 score; 92 keeps minor edits, drops copy-pastes


def make_hash(text: str) -> str:
    """MD5 hash of lowercased, whitespace-normalised text."""
    normalised = " ".join(text.lower().split())
    return hashlib.md5(normalised.encode("utf-8")).hexdigest()


@dataclass
class DedupeResult:
    kept: list[int]           # indices of records to keep
    dropped_exact: list[int]  # indices dropped by exact hash match
    dropped_near: list[int]   # indices dropped by near-duplicate match


def deduplicate(
    texts: list[str],
    threshold: int = NEAR_DUP_THRESHOLD,
) -> DedupeResult:
    """Return indices of unique records, dropping exact and near duplicates.

    Args:
        texts: List of cleaned text strings (order preserved).
        threshold: rapidfuzz similarity threshold (0-100).

    Returns:
        DedupeResult with kept, dropped_exact, dropped_near index lists.
    """
    kept: list[int] = []
    dropped_exact: list[int] = []
    dropped_near: list[int] = []

    seen_hashes: set[str] = set()
    kept_texts: list[str] = []

    for i, text in enumerate(texts):
        h = make_hash(text)

        # 1. Exact dedup
        if h in seen_hashes:
            dropped_exact.append(i)
            continue
        seen_hashes.add(h)

        # 2. Near-dedup — compare against already-kept texts
        # O(n²) but n is typically small per-source batch
        is_near_dup = False
        for kept_text in kept_texts:
            score = fuzz.token_sort_ratio(text.lower(), kept_text.lower())
            if score >= threshold:
                is_near_dup = True
                break

        if is_near_dup:
            dropped_near.append(i)
            continue

        kept.append(i)
        kept_texts.append(text)

    logger.debug(
        "Dedup: %d kept, %d exact dups, %d near dups (threshold=%d)",
        len(kept), len(dropped_exact), len(dropped_near), threshold,
    )
    return DedupeResult(kept=kept, dropped_exact=dropped_exact, dropped_near=dropped_near)
