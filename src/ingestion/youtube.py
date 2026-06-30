"""YouTube comment collector.

Uses the YouTube Data API v3 `commentThreads` endpoint to fetch top-level
comments and replies for each configured video.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.ingestion.models import RawReview
from src.ingestion.utils import retry

logger = logging.getLogger(__name__)

SOURCE = "youtube"
VIDEO_URL = "https://www.youtube.com/watch?v={video_id}"


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _build_client():
    api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key:
        raise EnvironmentError("YOUTUBE_API_KEY is not set in the environment.")
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


@retry(max_attempts=3, base_delay=3.0, exceptions=(HttpError, Exception))
def _fetch_comment_threads(youtube, video_id: str, max_results: int) -> list[dict]:
    """Page through commentThreads for one video."""
    threads: list[dict] = []
    page_token: str | None = None

    while len(threads) < max_results:
        batch = min(100, max_results - len(threads))
        kwargs: dict = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": batch,
            "textFormat": "plainText",
            "order": "relevance",
        }
        if page_token:
            kwargs["pageToken"] = page_token

        response = youtube.commentThreads().list(**kwargs).execute()
        threads.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return threads


def _parse_threads(video_id: str, threads: list[dict]) -> list[RawReview]:
    reviews: list[RawReview] = []
    url = VIDEO_URL.format(video_id=video_id)

    for thread in threads:
        top = thread.get("snippet", {}).get("topLevelComment", {})
        snip = top.get("snippet", {})
        text: str = (snip.get("textDisplay") or "").strip()
        if not text:
            continue

        reviews.append(
            RawReview(
                external_id=top.get("id", ""),
                source=SOURCE,
                text=text,
                source_url=url,
                author=snip.get("authorDisplayName"),
                rating=None,
                likes=snip.get("likeCount"),
                created_at=_parse_dt(snip.get("publishedAt")),
                metadata={"video_id": video_id, "parent_id": None},
            )
        )

        # Inline replies
        for reply in thread.get("replies", {}).get("comments", []):
            rsnip = reply.get("snippet", {})
            rtext: str = (rsnip.get("textDisplay") or "").strip()
            if not rtext:
                continue
            reviews.append(
                RawReview(
                    external_id=reply.get("id", ""),
                    source=SOURCE,
                    text=rtext,
                    source_url=url,
                    author=rsnip.get("authorDisplayName"),
                    rating=None,
                    likes=rsnip.get("likeCount"),
                    created_at=_parse_dt(rsnip.get("publishedAt")),
                    metadata={"video_id": video_id, "parent_id": top.get("id")},
                )
            )

    return reviews


def fetch(config: dict) -> list[RawReview]:
    """Fetch YouTube comments as per config dict.

    Expected config keys:
        video_ids (list[str]): YouTube video IDs
        max_comments_per_video (int): default 500
    """
    video_ids: list[str] = config.get("video_ids", [])
    max_per_video: int = int(config.get("max_comments_per_video", 500))

    if not video_ids:
        logger.warning("No YouTube video IDs configured. Skipping.")
        return []

    youtube = _build_client()
    all_reviews: list[RawReview] = []

    for vid in video_ids:
        logger.info("Fetching comments for video %s (max %d)…", vid, max_per_video)
        try:
            threads = _fetch_comment_threads(youtube, vid, max_per_video)
            parsed = _parse_threads(vid, threads)
            logger.info("  → %d comments (incl. replies)", len(parsed))
            all_reviews.extend(parsed)
        except HttpError as exc:
            logger.error("YouTube API error for video %s: %s", vid, exc)

    logger.info("Collected %d YouTube comments total", len(all_reviews))
    return all_reviews
