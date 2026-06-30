"""Unit tests for Phase 1 ingestion components."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.models import RawReview


# ---------------------------------------------------------------------------
# RawReview dataclass
# ---------------------------------------------------------------------------

class TestRawReview:
    def test_valid_google_play(self):
        r = RawReview(
            external_id="abc123",
            source="google_play",
            text="Great app but recommendations stink",
            rating=3.0,
        )
        assert r.source == "google_play"
        assert r.rating == 3.0

    def test_valid_hacker_news(self):
        r = RawReview(
            external_id="99999",
            source="hacker_news",
            text="Spotify's algorithm has gotten worse",
        )
        assert r.source == "hacker_news"
        assert r.rating is None

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            RawReview(external_id="x", source="youtube", text="   ")

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown source"):
            RawReview(external_id="x", source="reddit", text="some text")

    def test_to_dict_keys(self):
        r = RawReview(
            external_id="id1",
            source="youtube",
            text="Discover Weekly used to be great",
            metadata={"video_id": "abc"},
        )
        d = r.to_dict()
        assert d["external_id"] == "id1"
        assert d["source"] == "youtube"
        assert json.loads(d["metadata_json"]) == {"video_id": "abc"}
        assert "ingested_at" in d

    def test_to_dict_no_metadata(self):
        r = RawReview(external_id="id2", source="google_play", text="good app")
        d = r.to_dict()
        assert d["metadata_json"] is None


# ---------------------------------------------------------------------------
# Utility: retry decorator
# ---------------------------------------------------------------------------

class TestRetryDecorator:
    def test_succeeds_first_try(self):
        from src.ingestion.utils import retry

        call_count = 0

        @retry(max_attempts=3, base_delay=0)
        def always_ok():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert always_ok() == "ok"
        assert call_count == 1

    def test_retries_on_failure_then_succeeds(self):
        from src.ingestion.utils import retry

        call_count = 0

        @retry(max_attempts=3, base_delay=0)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        assert fails_twice() == "ok"
        assert call_count == 3

    def test_raises_after_max_attempts(self):
        from src.ingestion.utils import retry

        @retry(max_attempts=2, base_delay=0)
        def always_fails():
            raise RuntimeError("always bad")

        with pytest.raises(RuntimeError, match="always bad"):
            always_fails()


# ---------------------------------------------------------------------------
# Hacker News collector
# ---------------------------------------------------------------------------

class TestHackerNewsCollector:
    def _make_tree(self):
        return {
            "id": 41109882,
            "type": "story",
            "text": "Spotify recommendations are <b>getting worse</b>",
            "author": "testuser",
            "created_at_i": 1700000000,
            "points": 42,
            "children": [
                {
                    "id": 999,
                    "type": "comment",
                    "text": "I agree, Discover Weekly is broken",
                    "author": "commenter1",
                    "created_at_i": 1700001000,
                    "points": None,
                    "children": [],
                },
                {
                    "id": 1000,
                    "type": "comment",
                    "text": "Mine still works fine",
                    "author": "commenter2",
                    "created_at_i": 1700002000,
                    "points": 5,
                    "children": [
                        {
                            "id": 1001,
                            "type": "comment",
                            "text": "Lucky you",
                            "author": "commenter3",
                            "created_at_i": 1700003000,
                            "points": 1,
                            "children": [],
                        }
                    ],
                },
            ],
        }

    @patch("src.ingestion.hacker_news._fetch_item")
    def test_fetch_returns_reviews(self, mock_fetch):
        mock_fetch.return_value = self._make_tree()
        from src.ingestion.hacker_news import fetch

        config = {"item_ids": [41109882]}
        reviews = fetch(config)

        assert len(reviews) == 4  # story + 3 comments
        sources = {r.source for r in reviews}
        assert sources == {"hacker_news"}

    @patch("src.ingestion.hacker_news._fetch_item")
    def test_html_stripped_from_text(self, mock_fetch):
        mock_fetch.return_value = self._make_tree()
        from src.ingestion.hacker_news import fetch

        reviews = fetch({"item_ids": [41109882]})
        story = next(r for r in reviews if r.external_id == "41109882")
        assert "<b>" not in story.text
        assert "getting worse" in story.text

    def test_empty_config_returns_empty(self):
        from src.ingestion.hacker_news import fetch

        assert fetch({}) == []


# ---------------------------------------------------------------------------
# Google Play collector
# ---------------------------------------------------------------------------

class TestGooglePlayCollector:
    def _fake_review(self, i: int) -> dict:
        return {
            "reviewId": f"review_{i}",
            "userName": f"User{i}",
            "content": f"Review content number {i} about music discovery",
            "score": (i % 5) + 1,
            "thumbsUpCount": i * 3,
            "at": datetime(2024, 1, i % 28 + 1),
            "appVersion": "8.9.12",
        }

    @patch("src.ingestion.google_play._fetch_page")
    def test_fetch_maps_fields(self, mock_page):
        mock_page.return_value = [self._fake_review(1)]
        from src.ingestion.google_play import fetch

        reviews = fetch({"app_id": "com.spotify.music", "lang": "en", "country": "in", "count": 10})
        assert len(reviews) == 1
        r = reviews[0]
        assert r.source == "google_play"
        assert r.rating == 2.0
        assert r.metadata["app_version"] == "8.9.12"

    @patch("src.ingestion.google_play._fetch_page")
    def test_empty_content_skipped(self, mock_page):
        mock_page.return_value = [{"reviewId": "x", "content": "", "score": 3}]
        from src.ingestion.google_play import fetch

        reviews = fetch({"app_id": "com.spotify.music"})
        assert reviews == []


# ---------------------------------------------------------------------------
# load_sources_config
# ---------------------------------------------------------------------------

class TestLoadSourcesConfig:
    def test_loads_yaml(self, tmp_path):
        cfg_file = tmp_path / "sources.yaml"
        cfg_file.write_text("youtube:\n  video_ids: [abc]\n")
        from src.ingestion.utils import load_sources_config

        cfg = load_sources_config(str(cfg_file))
        assert cfg["youtube"]["video_ids"] == ["abc"]
