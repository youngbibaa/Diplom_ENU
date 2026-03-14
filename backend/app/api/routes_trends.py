from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.topic import Topic
from app.models.trend_metric import TrendMetric

router = APIRouter(prefix="/trends", tags=["Trends"])


def _serialize(rows):
    return [
        {
            "topic_id": topic.id,
            "topic_name": topic.name,
            "date": trend.date,
            "mentions_count": trend.mentions_count,
            "growth_rate": trend.growth_rate,
            "sentiment_avg": trend.sentiment_avg,
            "trend_score": trend.trend_score,
        }
        for trend, topic in rows
    ]


@router.get("/")
def list_trends(db: Session = Depends(get_db)):
    rows = (
        db.query(TrendMetric, Topic)
        .join(Topic, TrendMetric.topic_id == Topic.id)
        .order_by(TrendMetric.date.desc(), TrendMetric.trend_score.desc())
        .all()
    )
    return _serialize(rows)


@router.get("/top")
def top_trends(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    rows = (
        db.query(TrendMetric, Topic)
        .join(Topic, TrendMetric.topic_id == Topic.id)
        .order_by(TrendMetric.trend_score.desc())
        .limit(limit)
        .all()
    )
    return _serialize(rows)


@router.get("/timeline")
def topic_timeline(topic_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(TrendMetric, Topic)
        .join(Topic, TrendMetric.topic_id == Topic.id)
        .filter(TrendMetric.topic_id == topic_id)
        .order_by(TrendMetric.date.asc())
        .all()
    )
    return _serialize(rows)
