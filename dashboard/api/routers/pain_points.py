from fastapi import APIRouter
from src.storage.repository import get_insight

router = APIRouter()


@router.get("")
def get_pain_points():
    return {
        "ranked_pain_points": get_insight("ranked_pain_points") or [],
        "ranked_feature_requests": get_insight("ranked_feature_requests") or [],
        "pain_by_theme": get_insight("pain_points_by_theme") or {},
    }
