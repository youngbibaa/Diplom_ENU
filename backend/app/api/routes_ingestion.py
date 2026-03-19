from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.analytics import IngestRequest, IngestBulkRequest
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])
service = IngestionService()


@router.post("/rss")
def ingest_rss(payload: IngestRequest, db: Session = Depends(get_db)):
    """Загрузить один RSS-источник."""
    return service.ingest_rss_feed(db, payload.feed_url)


@router.post("/rss/bulk")
def ingest_rss_bulk(payload: IngestBulkRequest, db: Session = Depends(get_db)):
    """
    Загрузить несколько RSS-источников за один запрос.
    Возвращает сводку по каждому источнику + итоговые цифры.
    """
    results = []
    total_inserted = 0
    total_skipped = 0
    total_errors = 0

    for url in payload.feed_urls:
        try:
            result = service.ingest_rss_feed(db, url)
            results.append({"url": url, "status": "ok", **result})
            total_inserted += result.get("inserted", 0)
            total_skipped += result.get("skipped", 0)
        except Exception as e:
            results.append({"url": url, "status": "error", "error": str(e)})
            total_errors += 1

    return {
        "total_inserted": total_inserted,
        "total_skipped": total_skipped,
        "total_errors": total_errors,
        "sources": results,
    }
