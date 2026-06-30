from fastapi import APIRouter
from src.storage.repository import get_insight

router = APIRouter()


@router.get("")
def get_sentiment():
    return {
        "overall": get_insight("sentiment_overall") or {},
        "by_source": get_insight("sentiment_by_source") or {},
        "over_time": get_insight("sentiment_over_time") or {},
        "by_segment": get_insight("sentiment_by_segment") or {},
    }
