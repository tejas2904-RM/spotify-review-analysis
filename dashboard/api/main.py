"""FastAPI backend — Spotify Review Analysis Dashboard.

Local dev:
    uvicorn dashboard.api.main:app --reload --port 8000

Render (production):
    uvicorn dashboard.api.main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Startup: ensure required directories exist (critical on Render's fresh disk)
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    data_root = Path(os.getenv("DATA_DIR", "data"))
    for sub in ("raw", "clean", "enriched", "chroma"):
        (data_root / sub).mkdir(parents=True, exist_ok=True)
    logger.info("Data directories verified under %s", data_root.resolve())


def _init_db() -> None:
    """Create all ORM tables if they don't exist yet."""
    from src.storage.db import get_engine
    get_engine()


def _load_snapshot_if_empty() -> None:
    """Import pre-computed insights from snapshot JSON if the insights table is empty.

    This is the key mechanism for Render: the snapshot is committed to the repo,
    so the API serves real data on first deploy without running the pipeline.
    """
    from src.storage.repository import get_all_insights
    from scripts.init_render_db import import_snapshot  # noqa: F401

    if not get_all_insights():
        logger.info("Insights table is empty — importing from snapshot …")
        try:
            import_snapshot()
        except Exception as exc:
            logger.warning("Snapshot import skipped: %s", exc)
    else:
        logger.info("Insights table already populated — skipping snapshot import.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_dirs()
    _init_db()
    _load_snapshot_if_empty()
    yield


# ---------------------------------------------------------------------------
# CORS — allow localhost in dev + Vercel URL(s) in production
# ---------------------------------------------------------------------------

def _allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    extra = [o.strip() for o in raw.split(",") if o.strip()]
    defaults = ["http://localhost:3000", "http://127.0.0.1:3000"]
    return list(dict.fromkeys(defaults + extra))   # deduplicate, keep order


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

from dashboard.api.routers import (   # noqa: E402
    overview,
    sentiment,
    themes,
    pain_points,
    segments,
    summaries,
    opportunities,
)

app = FastAPI(
    title="Spotify Review Analysis API",
    description="Insights from 1,800+ Spotify user reviews across 4 sources.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router,      prefix="/api/overview",      tags=["Overview"])
app.include_router(sentiment.router,     prefix="/api/sentiment",     tags=["Sentiment"])
app.include_router(themes.router,        prefix="/api/themes",        tags=["Themes"])
app.include_router(pain_points.router,   prefix="/api/pain-points",   tags=["Pain Points"])
app.include_router(segments.router,      prefix="/api/segments",      tags=["Segments"])
app.include_router(summaries.router,     prefix="/api/summaries",     tags=["Summaries"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["Opportunities"])


@app.get("/api/health")
def health():
    from src.storage.repository import get_all_insights
    n = len(get_all_insights())
    return {
        "status": "ok",
        "service": "Spotify Review Analysis API",
        "insights_count": n,
        "data_dir": os.getenv("DATA_DIR", "data"),
    }
