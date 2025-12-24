from fastapi import APIRouter, HTTPException
from app.models import AnalysisRequest

router = APIRouter(prefix="/analysis")


@router.post("/")
def analyse(request: AnalysisRequest):
    raise HTTPException(
        status_code=501,
        detail="Analysis not implemented"
    )
