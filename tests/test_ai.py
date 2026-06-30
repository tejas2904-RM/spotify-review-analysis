"""Unit tests for Phase 4 AI modules.

All Groq API calls are mocked — no real API key needed to run these tests.
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# llm.py — cache, rate-limit, call wrapper
# ---------------------------------------------------------------------------

class TestLLMCache:
    def test_load_empty_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.ai.llm.CACHE_FILE", tmp_path / "cache.json")
        import src.ai.llm as llm
        llm._cache = {}
        llm.load_cache()
        assert llm._cache == {}

    def test_save_and_reload_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.ai.llm.CACHE_FILE", tmp_path / "cache.json")
        import src.ai.llm as llm
        llm._cache = {"abc123": {"sentiment": "positive"}}
        llm.save_cache()
        llm._cache = {}
        llm.load_cache()
        assert "abc123" in llm._cache
        assert llm._cache["abc123"]["sentiment"] == "positive"

    def test_cache_key_deterministic(self):
        from src.ai.llm import _cache_key
        k1 = _cache_key("system prompt", "user prompt")
        k2 = _cache_key("system prompt", "user prompt")
        assert k1 == k2

    def test_cache_key_differs_on_different_input(self):
        from src.ai.llm import _cache_key
        k1 = _cache_key("system", "prompt A")
        k2 = _cache_key("system", "prompt B")
        assert k1 != k2

    def test_call_returns_cached_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.ai.llm.CACHE_FILE", tmp_path / "cache.json")
        import src.ai.llm as llm
        llm._cache = {}
        key = llm._cache_key("sys", "usr")
        llm._cache[key] = {"sentiment": "cached"}
        result = llm.call("sys", "usr")
        assert result["sentiment"] == "cached"

    def test_call_hits_api_on_cache_miss(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.ai.llm.CACHE_FILE", tmp_path / "cache.json")
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        import src.ai.llm as llm
        llm._cache = {}
        llm._client = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({"sentiment": "positive"})
        mock_client.chat.completions.create.return_value = mock_response

        with patch("src.ai.llm._get_client", return_value=mock_client):
            result = llm.call("sys", "new user prompt")

        assert result["sentiment"] == "positive"


# ---------------------------------------------------------------------------
# prompts.py — structural checks
# ---------------------------------------------------------------------------

class TestPrompts:
    def test_prompt_version_is_set(self):
        from src.ai.prompts import PROMPT_VERSION
        assert PROMPT_VERSION.startswith("v")

    def test_enrich_system_contains_key_fields(self):
        from src.ai.prompts import ENRICH_SYSTEM
        for field in ("sentiment", "themes", "user_segment", "emotion", "pain_point"):
            assert field in ENRICH_SYSTEM

    def test_enrich_user_template_formats(self):
        from src.ai.prompts import ENRICH_USER_TEMPLATE
        formatted = ENRICH_USER_TEMPLATE.format(n=3, reviews="[1] test [2] test [3] test")
        assert "3" in formatted
        assert "test" in formatted

    def test_summarize_user_template_formats(self):
        from src.ai.prompts import SUMMARIZE_USER_TEMPLATE
        formatted = SUMMARIZE_USER_TEMPLATE.format(label="Discovery", n=5, reviews="- review")
        assert "Discovery" in formatted
        assert "review" in formatted


# ---------------------------------------------------------------------------
# enrich.py — sanitise / parse logic
# ---------------------------------------------------------------------------

class TestEnrichSanitise:
    """Test the _sanitise helper directly without any DB or API calls."""

    def _make_review(self, cid=1, source="google_play"):
        r = MagicMock()
        r.id = cid
        r.source = source
        r.clean_text = "Great discovery features but repetitive recommendations."
        return r

    def test_valid_result_passes_through(self):
        from src.ai.enrich import _sanitise
        result = {
            "sentiment": "negative",
            "sentiment_score": 0.2,
            "themes": ["discovery", "recommendations"],
            "is_feature_request": True,
            "feature_request_text": "Add more variety",
            "pain_point": "Too repetitive",
            "user_segment": "power_user",
            "emotion": "frustration",
        }
        record = _sanitise(result, self._make_review())
        assert record["sentiment"] == "negative"
        assert record["sentiment_score"] == pytest.approx(0.2)
        assert "discovery" in json.loads(record["themes_json"])
        assert record["is_feature_request"] is True
        assert record["user_segment"] == "power_user"
        assert record["emotion"] == "frustration"

    def test_invalid_sentiment_defaults_to_neutral(self):
        from src.ai.enrich import _sanitise
        record = _sanitise({"sentiment": "great"}, self._make_review())
        assert record["sentiment"] == "neutral"

    def test_invalid_segment_defaults_to_unknown(self):
        from src.ai.enrich import _sanitise
        record = _sanitise({"user_segment": "elite"}, self._make_review())
        assert record["user_segment"] == "unknown"

    def test_invalid_emotion_defaults_to_neutral(self):
        from src.ai.enrich import _sanitise
        record = _sanitise({"emotion": "angry"}, self._make_review())
        assert record["emotion"] == "neutral"

    def test_score_clamped_to_0_1(self):
        from src.ai.enrich import _sanitise
        record = _sanitise({"sentiment_score": 99.0}, self._make_review())
        assert record["sentiment_score"] == pytest.approx(1.0)
        record2 = _sanitise({"sentiment_score": -5.0}, self._make_review())
        assert record2["sentiment_score"] == pytest.approx(0.0)

    def test_unknown_themes_filtered_out(self):
        from src.ai.enrich import _sanitise
        result = {"themes": ["discovery", "not_a_real_theme", "algorithm"]}
        record = _sanitise(result, self._make_review())
        themes = json.loads(record["themes_json"])
        assert "not_a_real_theme" not in themes
        assert "discovery" in themes

    def test_clean_review_id_set_correctly(self):
        from src.ai.enrich import _sanitise
        review = self._make_review(cid=42, source="youtube")
        record = _sanitise({}, review)
        assert record["clean_review_id"] == 42
        assert record["source"] == "youtube"


# ---------------------------------------------------------------------------
# summarize.py — helper functions
# ---------------------------------------------------------------------------

class TestSummarize:
    def test_call_summary_returns_expected_keys(self):
        from src.ai.summarize import _call_summary

        mock_result = {
            "summary": "Users struggle with discovery.",
            "key_issues": ["filter bubble", "repetition"],
            "recommendations": ["diversify recommendations"],
        }

        with patch("src.ai.summarize.call", return_value=mock_result):
            result = _call_summary("Discovery", ["review1", "review2", "review3", "review4", "review5"])

        assert "summary" in result
        assert "key_issues" in result
        assert "recommendations" in result
        assert result["review_count"] == 5

    def test_call_summary_handles_api_failure(self):
        from src.ai.summarize import _call_summary

        with patch("src.ai.summarize.call", side_effect=RuntimeError("API down")):
            result = _call_summary("Discovery", ["r1", "r2", "r3", "r4", "r5"])

        assert result["summary"] == ""
        assert result["key_issues"] == []


# ---------------------------------------------------------------------------
# cluster.py — helper functions
# ---------------------------------------------------------------------------

class TestCluster:
    def test_label_cluster_returns_dict(self):
        from src.ai.cluster import _label_cluster

        mock_result = {"label": "Music Discovery", "description": "Users want better discovery."}
        with patch("src.ai.cluster.call", return_value=mock_result):
            result = _label_cluster(["review 1", "review 2"])

        assert result["label"] == "Music Discovery"
        assert "description" in result

    def test_label_cluster_handles_failure(self):
        from src.ai.cluster import _label_cluster

        with patch("src.ai.cluster.call", side_effect=RuntimeError("API error")):
            result = _label_cluster(["review 1"])

        assert result["label"] == "Unknown Theme"

    def test_run_clustering_empty_collection(self, tmp_path, monkeypatch):
        """Should return {} when no embeddings are stored."""
        monkeypatch.setattr("src.storage.vector.CHROMA_DIR", str(tmp_path / "chroma"))
        import src.storage.vector as v
        v._client = None
        v._collection = None

        from src.ai.cluster import run_clustering
        result = run_clustering()
        assert result == {}
