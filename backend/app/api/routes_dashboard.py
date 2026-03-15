from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.models.document import Document
from app.models.topic import Topic
from app.models.sentiment_result import SentimentResult
from app.models.trend_metric import TrendMetric
from app.models.source import Source

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_documents = db.query(func.count(Document.id)).scalar() or 0
    total_topics = db.query(func.count(Topic.id)).scalar() or 0
    total_sources = db.query(func.count(Source.id)).scalar() or 0

    sentiment_rows = (
        db.query(
            SentimentResult.label,
            func.count(SentimentResult.id).label("count"),
            func.avg(SentimentResult.score).label("avg_score"),
        )
        .group_by(SentimentResult.label)
        .all()
    )

    total_sentiment_docs = sum(row.count for row in sentiment_rows) if sentiment_rows else 0
    sentiment_summary = []

    order = {"positive": 0, "neutral": 1, "negative": 2}
    sentiment_rows = sorted(sentiment_rows, key=lambda x: order.get(x.label, 99))

    for row in sentiment_rows:
        share = row.count / total_sentiment_docs if total_sentiment_docs else 0.0
        sentiment_summary.append(
            {
                "label": row.label,
                "count": row.count,
                "share": round(share, 4),
                "avg_score": round(float(row.avg_score or 0.0), 4),
            }
        )

    latest_date = db.query(func.max(TrendMetric.date)).scalar()

    top_trends = []
    if latest_date:
        trend_rows = (
            db.query(TrendMetric, Topic)
            .join(Topic, TrendMetric.topic_id == Topic.id)
            .filter(TrendMetric.date == latest_date)
            .order_by(TrendMetric.trend_score.desc())
            .limit(5)
            .all()
        )

        top_trends = [
            {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "date": trend.date,
                "mentions_count": trend.mentions_count,
                "growth_rate": trend.growth_rate,
                "sentiment_avg": trend.sentiment_avg,
                "trend_score": trend.trend_score,
                "keywords": topic.keywords,
            }
            for trend, topic in trend_rows
        ]

    overall_avg_sentiment = db.query(func.avg(SentimentResult.score)).scalar() or 0.0

    return {
        "total_documents": total_documents,
        "total_topics": total_topics,
        "total_sources": total_sources,
        "latest_trend_date": latest_date,
        "overall_avg_sentiment": round(float(overall_avg_sentiment), 4),
        "sentiment_summary": sentiment_summary,
        "top_trends": top_trends,
    }