from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analytics import router as analytics_router
from app.api.routes_documents import router as documents_router
from app.api.routes_health import router as health_router
from app.api.routes_ingestion import router as ingestion_router
from app.api.routes_trends import router as trends_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_sources import router as sources_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title=settings.app_title)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(ingestion_router)
app.include_router(analytics_router)
app.include_router(trends_router)
app.include_router(dashboard_router)
app.include_router(sources_router)


@app.get("/")
def root():
    return {"message": settings.app_title}