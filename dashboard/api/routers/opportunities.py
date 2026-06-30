from fastapi import APIRouter
from src.storage.repository import get_insight

router = APIRouter()


@router.get("")
def get_opportunities():
    data = get_insight("product_opportunities") or {}
    return {
        "opportunities": data.get("opportunities", []),
        "total": len(data.get("opportunities", [])),
    }
