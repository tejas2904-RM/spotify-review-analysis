"""SQLAlchemy ORM models for all pipeline stages."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RawReview(Base):
    """Immutable source-of-truth for every ingested record."""

    __tablename__ = "raw_reviews"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_source_external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(256), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    # JSON-serialised dict: app_version, parent_id, etc.
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    @property
    def extra(self) -> dict:
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}

    def __repr__(self) -> str:
        return f"<RawReview source={self.source!r} id={self.external_id!r}>"


class CleanReview(Base):
    """Cleaned and normalised record produced by Phase 2."""

    __tablename__ = "clean_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_review_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    clean_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<CleanReview raw_id={self.raw_review_id} lang={self.language!r}>"


class EnrichedReview(Base):
    """AI/NLP enrichment outputs produced by Phase 4."""

    __tablename__ = "enriched_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clean_review_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    themes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_feature_request: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feature_request_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pain_point: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_segment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enriched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    @property
    def themes(self) -> list[str]:
        if self.themes_json:
            return json.loads(self.themes_json)
        return []

    def __repr__(self) -> str:
        return f"<EnrichedReview clean_id={self.clean_review_id} sentiment={self.sentiment!r}>"


class Insight(Base):
    """Aggregated dashboard-ready metrics produced by Phase 5."""

    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    filters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    @property
    def value(self):
        return json.loads(self.value_json)

    def __repr__(self) -> str:
        return f"<Insight metric={self.metric!r}>"
