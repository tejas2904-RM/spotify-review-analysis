from fastapi import APIRouter
from src.storage.repository import get_insight

router = APIRouter()


@router.get("")
def get_themes():
    return {
        "top_themes": get_insight("top_themes") or [],
        "by_source": get_insight("themes_by_source") or {},
        "sentiment_breakdown": get_insight("theme_sentiment_breakdown") or {},
        "cooccurrence": get_insight("theme_cooccurrence") or [],
        "over_time": get_insight("themes_over_time") or {},
        "clusters": get_insight("theme_clusters") or {},
    }
