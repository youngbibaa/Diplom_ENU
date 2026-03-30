"""
routes_sources.py
=================
Управление источниками данных.

Endpoints
---------
GET  /sources                — список всех источников в БД с числом документов
GET  /sources/approved       — реестр одобренных источников (KZ + Global)
POST /sources/cleanup        — удалить российские источники и их документы из БД
DELETE /sources/{source_id}  — удалить конкретный источник и все его документы
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.document import Document
from app.models.source import Source
from app.config.sources_config import ALL_SOURCES, is_russian_source

router = APIRouter(prefix="/sources", tags=["Sources"])
logger = logging.getLogger(__name__)


@router.get("")
def list_sources(db: Session = Depends(get_db)):
    """
    Возвращает все источники в БД с количеством документов.
    Помечает российские источники флагом is_russian.
    """
    rows = (
        db.query(Source, func.count(Document.id).label("doc_count"))
        .outerjoin(Document, Document.source_id == Source.id)
        .group_by(Source.id)
        .order_by(func.count(Document.id).desc())
        .all()
    )

    return {
        "total": len(rows),
        "items": [
            {
                "id": source.id,
                "name": source.name,
                "url": source.url,
                "type": source.type,
                "documents_count": doc_count,
                "is_russian": is_russian_source(source.url or ""),
                "created_at": source.created_at,
            }
            for source, doc_count in rows
        ],
    }


@router.get("/approved")
def get_approved_sources():
    """
    Возвращает реестр одобренных источников, сгруппированных по категориям.
    Используй эти URL для POST /ingestion/rss/bulk.
    """
    from itertools import groupby

    grouped: dict[str, list] = {}
    for source in ALL_SOURCES:
        grouped.setdefault(source.category, []).append({
            "url": source.url,
            "name": source.name,
            "language": source.language,
            "description": source.description,
        })

    return {
        "total": len(ALL_SOURCES),
        "categories": grouped,
        "all_urls": [s.url for s in ALL_SOURCES],
    }


@router.post("/cleanup")
def cleanup_russian_sources(db: Session = Depends(get_db)):
    """
    Удаляет из БД все российские источники и связанные с ними документы.
    Каскадное удаление: Source → Documents → SentimentResults → DocumentTopics.

    Используй после того, как перешёл на казахстанские и глобальные источники.
    """
    all_sources = db.query(Source).all()
    russian_sources = [s for s in all_sources if is_russian_source(s.url or "")]

    if not russian_sources:
        return {
            "status": "ok",
            "message": "Российских источников не найдено — БД уже чистая.",
            "deleted_sources": 0,
            "deleted_documents": 0,
        }

    deleted_docs_total = 0
    deleted_sources = []

    for source in russian_sources:
        doc_count = db.query(Document).filter(Document.source_id == source.id).count()
        deleted_docs_total += doc_count
        deleted_sources.append({"id": source.id, "name": source.name, "url": source.url, "documents": doc_count})

        # Каскадное удаление настроено в модели Source
        db.delete(source)

    db.commit()

    logger.info(
        "sources/cleanup: deleted %d Russian sources, %d documents",
        len(deleted_sources),
        deleted_docs_total,
    )

    return {
        "status": "ok",
        "message": f"Удалено {len(deleted_sources)} российских источников и {deleted_docs_total} документов.",
        "deleted_sources": len(deleted_sources),
        "deleted_documents": deleted_docs_total,
        "details": deleted_sources,
    }


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """
    Удаляет конкретный источник и все его документы по ID.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Источник с id={source_id} не найден")

    doc_count = db.query(Document).filter(Document.source_id == source_id).count()

    db.delete(source)
    db.commit()

    logger.info("sources: deleted source_id=%d (%s), docs=%d", source_id, source.url, doc_count)

    return {
        "status": "ok",
        "message": f"Источник «{source.name}» удалён.",
        "deleted_documents": doc_count,
    }