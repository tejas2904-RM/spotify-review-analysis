"""Shared dataclass representing a single raw review from any source."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RawReview:
    """Unified schema for a raw feedback record from any ingestion source."""

    external_id: str
    source: str
    text: str
    source_url: str | None = None
    author: str | None = None
    rating: float | None = None
    likes: int | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a dict suitable for DB insertion."""
        return {
            "external_id": self.external_id,
            "source": self.source,
            "text": self.text,
            "source_url": self.source_url,
            "author": self.author,
            "rating": self.rating,
            "likes": self.likes,
            "created_at": self.created_at,
            "metadata_json": json.dumps(self.metadata) if self.metadata else None,
            "ingested_at": datetime.utcnow(),
        }

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("RawReview.text must be non-empty")
        if self.source not in {
            "google_play",
            "youtube",
            "spotify_community",
            "hacker_news",
        }:
            raise ValueError(f"Unknown source: {self.source!r}")
