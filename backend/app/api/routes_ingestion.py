from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.analytics import IngestRequest
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])
service = IngestionService()


@router.post("/rss")
def ingest_rss(payload: IngestRequest, db: Session = Depends(get_db)):
    return service.ingest_rss_feed(db, payload.feed_url)