from fastapi import APIRouter
from src.storage.repository import get_insight

router = APIRouter()


@router.get("")
def get_segments():
    return {
        "distribution": get_insight("segment_distribution") or {},
        "sentiment_by_segment": get_insight("sentiment_by_segment") or {},
        "themes_by_segment": get_insight("themes_by_segment") or {},
        "pain_points_by_segment": get_insight("pain_points_by_segment") or {},
        "churn_signals": get_insight("churn_signals") or {},
    }
