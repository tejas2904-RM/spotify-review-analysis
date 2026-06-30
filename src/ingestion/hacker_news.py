"""Hacker News comment collector.

Uses the HN Algolia API to fetch the full item tree (story + all nested
comments) for each configured item ID.
"""

from __future__ import annotations

import logging
from datetime import datetime

import requests

from src.ingestion.models import RawReview
from src.ingestion.utils import retry

logger = logging.getLogger(__name__)

SOURCE = "hacker_news"
ALGOLIA_URL = "https://hn.algolia.com/api/v1/items/{item_id}"
HN_ITEM_URL = "https://news.ycombinator.com/item?id={item_id}"

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "spotify-review-engine/1.0"})


def _parse_dt(unix_ts: int | None) -> datetime | None:
    if unix_ts is None:
        return None
    try:
        return datetime.utcfromtimestamp(unix_ts)
    except (OSError, OverflowError, ValueError):
        return None


@retry(max_attempts=3, base_delay=2.0, exceptions=(requests.RequestException,))
def _fetch_item(item_id: int) -> dict:
    url = ALGOLIA_URL.format(item_id=item_id)
    response = _SESSION.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def _walk_tree(node: dict, root_id: int, parent_id: int | None = None) -> list[RawReview]:
    """Recursively collect comments from the Algolia item tree."""
    reviews: list[RawReview] = []
    node_type: str = node.get("type", "")
    text: str = (node.get("text") or "").strip()
    node_id = node.get("id")

    # Include comments (and optionally the story itself if it has body text)
    if node_type in ("comment", "story") and text and node_id:
        # Strip residual HTML tags that Algolia leaves in
        import re
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"\s+", " ", clean).strip()

        if clean:
            reviews.append(
                RawReview(
                    external_id=str(node_id),
                    source=SOURCE,
                    text=clean,
                    source_url=HN_ITEM_URL.format(item_id=root_id),
                    author=node.get("author"),
                    rating=None,
                    likes=node.get("points"),
                    created_at=_parse_dt(node.get("created_at_i")),
                    metadata={
                        "root_id": root_id,
                        "parent_id": parent_id,
                        "item_type": node_type,
                    },
                )
            )

    for child in node.get("children", []):
        reviews.extend(_walk_tree(child, root_id=root_id, parent_id=node_id))

    return reviews


def fetch(config: dict) -> list[RawReview]:
    """Fetch Hacker News items and their comment trees as per config dict.

    Expected config keys:
        item_ids (list[int|str]): HN item IDs
    """
    item_ids: list[int] = [int(i) for i in config.get("item_ids", [])]
    if not item_ids:
        logger.warning("No Hacker News item IDs configured. Skipping.")
        return []

    all_reviews: list[RawReview] = []

    for item_id in item_ids:
        logger.info("Fetching HN item %d…", item_id)
        try:
            tree = _fetch_item(item_id)
            parsed = _walk_tree(tree, root_id=item_id)
            logger.info("  → %d comments (incl. story)", len(parsed))
            all_reviews.extend(parsed)
        except Exception as exc:
            logger.error("Failed to fetch HN item %d: %s", item_id, exc)

    logger.info("Collected %d Hacker News comments total", len(all_reviews))
    return all_reviews
