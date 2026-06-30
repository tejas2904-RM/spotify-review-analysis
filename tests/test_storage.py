"""Unit tests for Phase 3 storage components."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# repository.py
# ---------------------------------------------------------------------------

class TestRepository:
    """Tests for repository helpers using an in-memory SQLite DB."""

    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path, monkeypatch):
        """Point DB_URL to a temp SQLite file for each test."""
        db_file = tmp_path / "test.db"
        monkeypatch.setenv("DB_URL", f"sqlite:///{db_file}")
        # Reset the engine singleton so it picks up the new URL
        import src.storage.db as db_mod
        db_mod._engine = None
        db_mod._SessionLocal = None
        from src.storage.db import get_engine
        get_engine()  # initialise tables

    def _insert_clean(self, source="google_play", is_relevant=True, is_spam=False, text="test review about discovery"):
        from src.storage.db import get_session
        from src.storage.models import CleanReview
        with get_session() as s:
            cr = CleanReview(
                raw_review_id=1,
                source=source,
                clean_text=text,
                language="en",
                token_count=5,
                is_spam=is_spam,
                is_relevant=is_relevant,
                relevance_score=2.0,
                created_at=datetime.utcnow(),
            )
            s.add(cr)
            s.flush()
            return cr.id

    def test_get_relevant_clean_returns_relevant(self):
        from src.storage.repository import get_relevant_clean
        self._insert_clean(is_relevant=True)
        self._insert_clean(is_relevant=False)
        results = get_relevant_clean()
        assert len(results) == 1
        assert results[0].is_relevant is True

    def test_get_relevant_clean_excludes_spam(self):
        from src.storage.repository import get_relevant_clean
        self._insert_clean(is_relevant=True, is_spam=False)
        self._insert_clean(is_relevant=True, is_spam=True)
        results = get_relevant_clean(include_spam=False)
        assert len(results) == 1

    def test_get_relevant_clean_source_filter(self):
        from src.storage.repository import get_relevant_clean
        self._insert_clean(source="google_play")
        self._insert_clean(source="youtube")
        results = get_relevant_clean(sources=["youtube"])
        assert len(results) == 1
        assert results[0].source == "youtube"

    def test_save_and_get_insight(self):
        from src.storage.repository import get_insight, save_insight
        save_insight("sentiment_dist", {"positive": 60, "negative": 40})
        result = get_insight("sentiment_dist")
        assert result["positive"] == 60
        assert result["negative"] == 40

    def test_get_insight_not_found(self):
        from src.storage.repository import get_insight
        assert get_insight("nonexistent_metric") is None

    def test_save_insight_upserts(self):
        from src.storage.repository import get_insight, save_insight
        save_insight("test_metric", {"v": 1})
        save_insight("test_metric", {"v": 2})  # should overwrite
        result = get_insight("test_metric")
        assert result["v"] == 2

    def test_bulk_insert_enriched(self):
        from src.storage.repository import bulk_insert_enriched, count_enriched
        cid = self._insert_clean()
        records = [{
            "clean_review_id": cid,
            "source": "google_play",
            "sentiment": "positive",
            "sentiment_score": 0.85,
            "themes_json": json.dumps(["discovery", "recommendations"]),
            "is_feature_request": False,
            "user_segment": "casual",
        }]
        inserted = bulk_insert_enriched(records)
        assert inserted == 1
        assert count_enriched() == 1

    def test_db_summary_structure(self):
        from src.storage.repository import db_summary
        summary = db_summary()
        assert "raw" in summary
        assert "clean" in summary
        assert "enriched" in summary
        assert "insights" in summary
        assert "total" in summary["raw"]


# ---------------------------------------------------------------------------
# parquet.py
# ---------------------------------------------------------------------------

class TestParquet:
    def test_export_and_load_clean(self, tmp_path, monkeypatch):
        db_file = tmp_path / "test.db"
        monkeypatch.setenv("DB_URL", f"sqlite:///{db_file}")
        import src.storage.db as db_mod
        db_mod._engine = None
        db_mod._SessionLocal = None
        from src.storage.db import get_engine, get_session
        get_engine()

        from src.storage.models import CleanReview
        with get_session() as s:
            s.add(CleanReview(
                raw_review_id=1, source="youtube",
                clean_text="Great Discover Weekly", language="en",
                token_count=3, is_spam=False, is_relevant=True,
                relevance_score=3.5, created_at=datetime.utcnow(),
            ))

        out = tmp_path / "clean.parquet"
        from src.storage.parquet import export_clean, load_clean_parquet
        export_clean(out)
        df = load_clean_parquet(out, relevant_only=True)
        assert len(df) == 1
        assert df.iloc[0]["source"] == "youtube"

    def test_load_nonexistent_parquet_raises(self, tmp_path):
        from src.storage.parquet import load_clean_parquet
        with pytest.raises(FileNotFoundError):
            load_clean_parquet(tmp_path / "missing.parquet")


# ---------------------------------------------------------------------------
# vector.py — light mocked tests (no real GPU/model needed)
# ---------------------------------------------------------------------------

class TestVectorStore:
    def test_collection_stats_structure(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.storage.vector.CHROMA_DIR", str(tmp_path / "chroma"))
        import src.storage.vector as v
        v._client = None
        v._collection = None
        stats = v.collection_stats()
        assert "total_embeddings" in stats
        assert stats["total_embeddings"] == 0

    def test_embed_and_store_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.storage.vector.CHROMA_DIR", str(tmp_path / "chroma"))
        import src.storage.vector as v
        v._client = None
        v._collection = None
        count = v.embed_and_store([])
        assert count == 0

    def test_search_returns_list(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.storage.vector.CHROMA_DIR", str(tmp_path / "chroma"))
        import src.storage.vector as v
        v._client = None
        v._collection = None

        mock_embedder = MagicMock()
        mock_embedder.encode.return_value = [[0.1] * 384]
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Test review text"]],
            "metadatas": [[{"source": "youtube"}]],
            "distances": [[0.12]],
            "ids": [["42"]],
        }
        v._embedder = mock_embedder
        v._collection = mock_collection

        results = v.search("music discovery", n_results=1)
        assert isinstance(results, list)
        assert results[0]["text"] == "Test review text"
        assert results[0]["distance"] == 0.12
