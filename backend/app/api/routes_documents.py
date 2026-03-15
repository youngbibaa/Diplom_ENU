from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.document import Document
from app.models.document_topic import DocumentTopic
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("")
def get_documents(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    source_id: int | None = None,
    topic_id: int | None = None,
    sentiment_label: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    query = db.query(Document)

    if topic_id is not None:
        query = query.join(DocumentTopic, DocumentTopic.document_id == Document.id)
        query = query.filter(DocumentTopic.topic_id == topic_id)

    if sentiment_label is not None:
        query = query.join(SentimentResult, SentimentResult.document_id == Document.id)
        query = query.filter(SentimentResult.label == sentiment_label)

    if source_id is not None:
        query = query.filter(Document.source_id == source_id)

    if date_from is not None:
        query = query.filter(
            Document.published_at >= datetime.combine(date_from, time.min)
        )

    if date_to is not None:
        query = query.filter(
            Document.published_at <= datetime.combine(date_to, time.max)
        )

    total = query.count()

    documents = (
        query.order_by(Document.published_at.desc().nullslast(), Document.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    document_ids = [doc.id for doc in documents]

    sentiment_map = {
        row.document_id: {"label": row.label, "score": row.score}
        for row in db.query(SentimentResult)
        .filter(SentimentResult.document_id.in_(document_ids))
        .all()
    } if document_ids else {}

    topic_rows = (
        db.query(DocumentTopic.document_id, Topic.id, Topic.name)
        .join(Topic, Topic.id == DocumentTopic.topic_id)
        .filter(DocumentTopic.document_id.in_(document_ids))
        .all()
    ) if document_ids else []

    topic_map = {}
    for document_id, t_id, t_name in topic_rows:
        topic_map[document_id] = {"topic_id": t_id, "topic_name": t_name}

    items = []
    for doc in documents:
        items.append(
            {
                "id": doc.id,
                "source_id": doc.source_id,
                "title": doc.title,
                "url": doc.url,
                "author": doc.author,
                "published_at": doc.published_at,
                "collected_at": doc.collected_at,
                "text_clean": doc.text_clean,
                "sentiment": sentiment_map.get(doc.id),
                "topic": topic_map.get(doc.id),
            }
        )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }
