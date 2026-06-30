"""Unit tests for Phase 5 insights modules.

All tests operate on synthetic EnrichedReview objects — no DB or API needed.
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers — build synthetic EnrichedReview objects
# ---------------------------------------------------------------------------

def _make_enriched(
    cid=1,
    source="google_play",
    sentiment="negative",
    score=0.2,
    themes=None,
    is_fr=False,
    fr_text=None,
    pain=None,
    segment="casual",
    emotion="frustration",
):
    er = MagicMock()
    er.clean_review_id = cid
    er.source = source
    er.sentiment = sentiment
    er.sentiment_score = score
    er.themes_json = json.dumps(themes or [])
    er.is_feature_request = is_fr
    er.feature_request_text = fr_text
    er.pain_point = pain
    er.user_segment = segment
    er.emotion = emotion
    er.enriched_at = datetime.utcnow()
    return er


# ---------------------------------------------------------------------------
# sentiment.py
# ---------------------------------------------------------------------------

class TestSentiment:
    def _sample(self):
        return [
            _make_enriched(1, sentiment="positive", score=0.9),
            _make_enriched(2, sentiment="negative", score=0.1),
            _make_enriched(3, sentiment="neutral",  score=0.5),
            _make_enriched(4, sentiment="negative", score=0.2),
        ]

    def test_overall_counts(self):
        from src.insights.sentiment import compute_overall
        result = compute_overall(self._sample())
        assert result["total"] == 4
        assert result["counts"]["positive"] == 1
        assert result["counts"]["negative"] == 2
        assert result["counts"]["neutral"] == 1

    def test_overall_percentages(self):
        from src.insights.sentiment import compute_overall
        result = compute_overall(self._sample())
        assert result["percentages"]["negative"] == 50.0

    def test_overall_avg_score(self):
        from src.insights.sentiment import compute_overall
        result = compute_overall(self._sample())
        assert result["avg_score"] == pytest.approx((0.9 + 0.1 + 0.5 + 0.2) / 4, abs=0.001)

    def test_by_source_splits_correctly(self):
        from src.insights.sentiment import compute_by_source
        reviews = [
            _make_enriched(1, source="google_play", sentiment="positive"),
            _make_enriched(2, source="youtube", sentiment="negative"),
            _make_enriched(3, source="youtube", sentiment="negative"),
        ]
        result = compute_by_source(reviews)
        assert result["youtube"]["counts"]["negative"] == 2
        assert result["google_play"]["counts"]["positive"] == 1

    def test_over_time_groups_by_month(self):
        from src.insights.sentiment import compute_over_time
        reviews = [
            _make_enriched(1, sentiment="positive"),
            _make_enriched(2, sentiment="negative"),
        ]
        clean_map = {
            1: datetime(2024, 3, 15),
            2: datetime(2024, 4, 5),
        }
        result = compute_over_time(reviews, clean_map)
        assert "2024-03" in result
        assert "2024-04" in result

    def test_empty_input_handled(self):
        from src.insights.sentiment import compute_overall
        result = compute_overall([])
        assert result["total"] == 0
        assert result["avg_score"] is None


# ---------------------------------------------------------------------------
# themes.py
# ---------------------------------------------------------------------------

class TestThemes:
    def _sample(self):
        return [
            _make_enriched(1, themes=["discovery", "recommendations"]),
            _make_enriched(2, themes=["discovery", "algorithm"]),
            _make_enriched(3, themes=["repetition", "recommendations"], sentiment="negative"),
            _make_enriched(4, themes=["discovery"], source="youtube"),
        ]

    def test_top_themes_ranked(self):
        from src.insights.themes import compute_top_themes
        result = compute_top_themes(self._sample())
        assert result[0]["theme"] == "discovery"   # 3 mentions
        assert result[0]["count"] == 3

    def test_themes_by_source(self):
        from src.insights.themes import compute_themes_by_source
        result = compute_themes_by_source(self._sample())
        assert "youtube" in result
        yt_themes = [t["theme"] for t in result["youtube"]]
        assert "discovery" in yt_themes

    def test_theme_sentiment_negativity_rate(self):
        from src.insights.themes import compute_theme_sentiment
        result = compute_theme_sentiment(self._sample())
        # "repetition" appears only in the negative review
        assert result["repetition"]["negativity_rate"] == 100.0

    def test_cooccurrence_finds_pairs(self):
        from src.insights.themes import compute_theme_cooccurrence
        result = compute_theme_cooccurrence(self._sample())
        pairs = [(r["theme_a"], r["theme_b"]) for r in result]
        assert ("discovery", "recommendations") in pairs

    def test_empty_themes_json_handled(self):
        from src.insights.themes import compute_top_themes
        er = MagicMock()
        er.themes_json = None
        er.sentiment = "neutral"
        er.source = "google_play"
        result = compute_top_themes([er])
        assert result == []


# ---------------------------------------------------------------------------
# pain_points.py
# ---------------------------------------------------------------------------

class TestPainPoints:
    def _sample(self):
        return [
            _make_enriched(1, pain="algorithm shows same songs repeatedly", sentiment="negative", themes=["repetition"]),
            _make_enriched(2, pain="discover weekly stopped being relevant", sentiment="negative", themes=["discovery"]),
            _make_enriched(3, pain="algorithm shows same songs repeatedly", sentiment="negative", themes=["repetition"]),
            _make_enriched(4, is_fr=True, fr_text="add more artist radio variety", themes=["radio"]),
            _make_enriched(5, is_fr=True, fr_text="add more artist radio variety", themes=["radio"]),
        ]

    def test_pain_points_ranked_by_weight(self):
        from src.insights.pain_points import compute_ranked_pain_points
        result = compute_ranked_pain_points(self._sample())
        assert result[0]["pain_point"] == "algorithm shows same songs repeatedly"
        assert result[0]["mention_count"] == 2

    def test_feature_requests_ranked(self):
        from src.insights.pain_points import compute_ranked_feature_requests
        result = compute_ranked_feature_requests(self._sample())
        assert result[0]["count"] == 2
        assert "radio" in result[0]["feature_request"]

    def test_short_pain_points_excluded(self):
        from src.insights.pain_points import compute_ranked_pain_points
        er = _make_enriched(1, pain="bad", sentiment="negative")
        result = compute_ranked_pain_points([er])
        assert result == []

    def test_pain_by_theme(self):
        from src.insights.pain_points import compute_pain_by_theme
        result = compute_pain_by_theme(self._sample())
        assert "repetition" in result
        assert len(result["repetition"]) >= 1


# ---------------------------------------------------------------------------
# segments.py
# ---------------------------------------------------------------------------

class TestSegments:
    def _sample(self):
        return [
            _make_enriched(1, segment="casual", sentiment="positive", themes=["discovery"]),
            _make_enriched(2, segment="power_user", sentiment="negative", themes=["recommendations", "algorithm"]),
            _make_enriched(3, segment="churn_risk", sentiment="negative", themes=["churn_risk"], emotion="frustration"),
            _make_enriched(4, segment="casual", sentiment="neutral", themes=["playlist"]),
            _make_enriched(5, segment="churn_risk", sentiment="negative", themes=["algorithm"], emotion="disappointment"),
        ]

    def test_distribution_counts(self):
        from src.insights.segments import compute_segment_distribution
        result = compute_segment_distribution(self._sample())
        assert result["casual"]["count"] == 2
        assert result["churn_risk"]["count"] == 2
        assert result["power_user"]["count"] == 1

    def test_distribution_percentages(self):
        from src.insights.segments import compute_segment_distribution
        result = compute_segment_distribution(self._sample())
        assert result["casual"]["pct"] == 40.0

    def test_churn_signals(self):
        from src.insights.segments import compute_churn_signals
        result = compute_churn_signals(self._sample())
        assert result["count"] == 2
        assert result["pct_of_total"] == 40.0
        assert "algorithm" in result["top_themes"]

    def test_segment_themes(self):
        from src.insights.segments import compute_segment_themes
        result = compute_segment_themes(self._sample())
        assert "power_user" in result
        pu_themes = [t["theme"] for t in result["power_user"]]
        assert "recommendations" in pu_themes or "algorithm" in pu_themes

    def test_no_churn_risk_handled(self):
        from src.insights.segments import compute_churn_signals
        reviews = [_make_enriched(1, segment="casual")]
        result = compute_churn_signals(reviews)
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# opportunities.py — mocked LLM
# ---------------------------------------------------------------------------

class TestOpportunities:
    def test_opportunities_structure(self):
        from src.insights.opportunities import compute_product_opportunities

        mock_result = {
            "opportunities": [
                {
                    "title": "Fix Discovery Algorithm",
                    "priority": "high",
                    "problem_statement": "Users feel stuck in a filter bubble.",
                    "evidence": ["70% of discovery reviews are negative"],
                    "recommendation": "Introduce serendipity score into recommendation model.",
                    "affected_segments": ["casual", "churn_risk"],
                    "themes": ["discovery", "algorithm"],
                }
            ]
        }

        with patch("src.insights.opportunities.call", return_value=mock_result), \
             patch("src.insights.opportunities.save_insight") as mock_save, \
             patch("src.insights.opportunities.load_cache"), \
             patch("src.insights.opportunities.save_cache"):
            result = compute_product_opportunities(
                sentiment={"overall": {"total": 100, "percentages": {"negative": 60}}},
                top_themes=[{"theme": "discovery", "count": 40}],
                pain_points=[{"pain_point": "same songs", "weighted_score": 80, "mention_count": 40}],
                feature_requests=[{"feature_request": "more variety", "count": 20}],
                churn_signals={"count": 30, "pct_of_total": 30, "top_themes": {}},
                theme_sentiment={"discovery": {"negativity_rate": 70}},
            )

        assert "opportunities" in result
        assert len(result["opportunities"]) == 1
        assert result["opportunities"][0]["priority"] == "high"
        mock_save.assert_called_once()
