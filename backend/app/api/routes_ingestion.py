from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.ingestion import IngestResponse, RSSIngestRequest
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/rss", response_model=IngestResponse)
def ingest_rss(payload: RSSIngestRequest, db: Session = Depends(get_db)):
    service = IngestionService(db)
    return service.ingest_rss(str(payload.feed_url))
