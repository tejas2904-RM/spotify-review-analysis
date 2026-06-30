from fastapi import APIRouter
from sqlalchemy import select
from src.storage.db import get_session
from src.storage.models import Insight
import json

router = APIRouter()

THEMES = [
    "discovery", "recommendations", "algorithm", "repetition", "playlist",
    "wrapped", "social", "pricing", "ads", "ui_ux", "offline", "podcasts",
    "competitor_comparison", "feature_request", "churn_risk", "mood_listening",
    "shuffle", "radio", "artist_discovery", "genre_exploration",
]
SOURCES = ["google_play", "youtube", "hacker_news", "spotify_community"]


@router.get("")
def get_summaries():
    theme_summaries = {}
    source_summaries = {}

    with get_session() as s:
        rows = list(s.execute(select(Insight)).scalars().all())

    for row in rows:
        if row.metric.startswith("summary_theme_"):
            theme = row.metric.replace("summary_theme_", "")
            try:
                theme_summaries[theme] = json.loads(row.value_json)
            except Exception:
                pass
        elif row.metric.startswith("summary_source_"):
            source = row.metric.replace("summary_source_", "")
            try:
                source_summaries[source] = json.loads(row.value_json)
            except Exception:
                pass

    return {
        "theme_summaries": theme_summaries,
        "source_summaries": source_summaries,
    }
