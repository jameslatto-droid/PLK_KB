from fastapi import APIRouter, HTTPException
from app.models import SearchRequest

router = APIRouter(prefix="/search")


@router.post("/")
def search(request: SearchRequest):
    raise HTTPException(
        status_code=501,
        detail="Search not implemented"
    )
