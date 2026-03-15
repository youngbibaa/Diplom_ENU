import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_topic import DocumentTopic
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.models.trend_metric import TrendMetric
from app.services.analytics_service import run_analytics
from app.services.trend_service import rebuild_trends

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


@router.post("/run")
def analytics_run(db: Session = Depends(get_db)):
    run = AnalysisRun(
        status="running",
        model_version="sentiment=tfidf_logreg;topics=lda;trends=log_volume_growth",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    logger.info("Analytics run started: run_id=%s", run.id)

    try:
        analytics_result = run_analytics(db)
        trend_result = rebuild_trends(db)

        run.status = "success"
        run.documents_processed = analytics_result.get("processed", 0)
        run.topics_created = analytics_result.get("topics_created", 0)
        run.trend_rows_created = trend_result.get("trend_rows_created", 0)
        run.finished_at = datetime.now(timezone.utc)

        db.add(run)
        db.commit()
        db.refresh(run)

        logger.info(
            "Analytics run finished: run_id=%s processed=%s topics=%s trends=%s",
            run.id,
            run.documents_processed,
            run.topics_created,
            run.trend_rows_created,
        )

        return {
            "run_id": run.id,
            "processed": run.documents_processed,
            "topics_created": run.topics_created,
            "trend_rows_created": run.trend_rows_created,
            "status": run.status,
        }

    except Exception as exc:
        db.rollback()

        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()

        logger.exception("Analytics run failed: run_id=%s error=%s", run.id, exc)
        raise HTTPException(status_code=500, detail=f"Analytics run failed: {exc}")


@router.get("/runs")
def get_analysis_runs(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(AnalysisRun)
    total = query.count()

    runs = (
        query.order_by(AnalysisRun.started_at.desc(), AnalysisRun.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": run.id,
                "status": run.status,
                "model_version": run.model_version,
                "documents_processed": run.documents_processed,
                "topics_created": run.topics_created,
                "trend_rows_created": run.trend_rows_created,
                "error_message": run.error_message,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
            }
            for run in runs
        ],
    }


@router.get("/sentiment-summary")
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


@router.get("/topics/{topic_id}/documents")
def get_topic_documents(
    topic_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    query = (
        db.query(Document, DocumentTopic, SentimentResult)
        .join(DocumentTopic, DocumentTopic.document_id == Document.id)
        .outerjoin(SentimentResult, SentimentResult.document_id == Document.id)
        .filter(DocumentTopic.topic_id == topic_id)
    )

    total = query.count()

    rows = (
        query.order_by(Document.published_at.desc().nullslast(), Document.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "topic": {
            "topic_id": topic.id,
            "name": topic.name,
            "keywords": topic.keywords,
        },
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": document.id,
                "title": document.title,
                "url": document.url,
                "author": document.author,
                "published_at": document.published_at,
                "text_clean": document.text_clean,
                "topic_probability": round(float(document_topic.probability), 4),
                "sentiment": {
                    "label": sentiment.label,
                    "score": sentiment.score,
                } if sentiment else None,
            }
            for document, document_topic, sentiment in rows
        ],
    }


@router.get("/topics/{topic_id}/timeline")
def get_topic_timeline(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    rows = (
        db.query(TrendMetric)
        .filter(TrendMetric.topic_id == topic_id)
        .order_by(TrendMetric.date.asc())
        .all()
    )

    return {
        "topic": {
            "topic_id": topic.id,
            "name": topic.name,
            "keywords": topic.keywords,
        },
        "items": [
            {
                "date": row.date,
                "mentions_count": row.mentions_count,
                "growth_rate": row.growth_rate,
                "sentiment_avg": row.sentiment_avg,
                "trend_score": row.trend_score,
            }
            for row in rows
        ],
    }