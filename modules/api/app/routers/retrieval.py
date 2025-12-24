from fastapi import APIRouter, HTTPException
from app.models import RetrievalRequest

router = APIRouter(prefix="/retrieve")


@router.post("/")
def retrieve(request: RetrievalRequest):
    raise HTTPException(
        status_code=501,
        detail="Retrieval not implemented"
    )
