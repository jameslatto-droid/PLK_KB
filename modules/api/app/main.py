from fastapi import FastAPI
from app.config import settings
from app.routers import health, metadata, search, retrieval, analysis

app = FastAPI(title=settings.app_name)

app.include_router(health.router)
app.include_router(metadata.router)
app.include_router(search.router)
app.include_router(retrieval.router)
app.include_router(analysis.router)
