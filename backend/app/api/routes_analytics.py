from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.document_topic import DocumentTopic
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.schemas.analytics import AnalyticsRunResponse
from app.services.analytics_service import AnalyticsService
from app.services.trend_service import TrendService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/run", response_model=AnalyticsRunResponse)
def run_analytics(db: Session = Depends(get_db)):
    analytics_result = AnalyticsService(db).run()
    trend_result = TrendService(db).rebuild()
    return {**analytics_result, **trend_result}


@router.get("/sentiment-summary")
def sentiment_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(SentimentResult.label, func.count(SentimentResult.id).label("count"))
        .group_by(SentimentResult.label)
        .order_by(SentimentResult.label.asc())
        .all()
    )
    return [{"label": label, "count": count} for label, count in rows]


@router.get("/topics")
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
