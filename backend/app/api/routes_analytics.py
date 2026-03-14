from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.models.document_topic import DocumentTopic
from app.services.analytics_service import run_analytics
from app.services.trend_service import rebuild_trends

router = APIRouter()


@router.post("/analytics/run")
def analytics_run(db: Session = Depends(get_db)):
    result = run_analytics(db)
    trend_result = rebuild_trends(db)
    return {**result, **trend_result}


@router.get("/analytics/sentiment-summary")
def sentiment_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(
            SentimentResult.label,
            func.count(SentimentResult.id).label("count"),
            func.avg(SentimentResult.score).label("avg_score"),
        )
        .group_by(SentimentResult.label)
        .all()
    )

    total_documents = sum(count for _, count, _ in rows)
    overall_avg_score = db.query(func.avg(SentimentResult.score)).scalar() or 0.0

    order = {"positive": 0, "neutral": 1, "negative": 2}
    rows = sorted(rows, key=lambda item: order.get(item[0], 99))

    items = []
    for label, count, avg_score in rows:
        share = (count / total_documents) if total_documents else 0.0
        items.append(
            {
                "label": label,
                "count": count,
                "share": round(share, 4),
                "avg_score": round(float(avg_score or 0.0), 4),
            }
        )

    return {
        "total_documents": total_documents,
        "overall_avg_score": round(float(overall_avg_score), 4),
        "items": items,
    }


@router.get("/analytics/topics")
def get_topics(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Topic.id,
            Topic.name,
            Topic.keywords,
            func.count(DocumentTopic.id).label("documents_count"),
        )
        .outerjoin(DocumentTopic, DocumentTopic.topic_id == Topic.id)
        .group_by(Topic.id, Topic.name, Topic.keywords)
        .order_by(func.count(DocumentTopic.id).desc(), Topic.id.asc())
        .all()
    )

    return [
        {
            "topic_id": topic_id,
            "name": name,
            "keywords": keywords,
            "documents_count": documents_count,
        }
        for topic_id, name, keywords, documents_count in rows
    ]