from fastapi import APIRouter, HTTPException
from app.models import MetadataResponse

router = APIRouter(prefix="/metadata")


@router.get("/{document_id}", response_model=MetadataResponse)
def get_metadata(document_id: str):
    raise HTTPException(
        status_code=501,
        detail="Metadata retrieval not implemented"
    )
