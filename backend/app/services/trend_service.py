from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_topic import DocumentTopic
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.models.trend_metric import TrendMetric
from app.ml.trend_detector import calculate_growth_rate, calculate_trend_score


def rebuild_trends(db: Session) -> dict:
    db.query(TrendMetric).delete()
    db.commit()

    rows = (
        db.query(DocumentTopic, Document, Topic, SentimentResult)
        .join(Document, DocumentTopic.document_id == Document.id)
        .join(Topic, DocumentTopic.topic_id == Topic.id)
        .outerjoin(SentimentResult, SentimentResult.document_id == Document.id)
        .all()
    )

    grouped = defaultdict(lambda: {"mentions": 0, "scores": []})

    for document_topic, document, topic, sentiment in rows:
        doc_date = None
        if document.published_at:
            doc_date = document.published_at.date()
        elif document.collected_at:
            doc_date = document.collected_at.date()

        if not doc_date:
            continue

        key = (topic.id, doc_date)
        grouped[key]["mentions"] += 1

        if sentiment is not None and sentiment.score is not None:
            grouped[key]["scores"].append(float(sentiment.score))

    if not grouped:
        return {"trend_rows_created": 0}

    created = 0
    by_topic: dict[int, list[tuple[date, dict]]] = defaultdict(list)

    for (topic_id, day), payload in grouped.items():
        by_topic[topic_id].append((day, payload))

    for topic_id, items in by_topic.items():
        items.sort(key=lambda x: x[0])
        previous_mentions = 0

        for day, payload in items:
            mentions_count = payload["mentions"]
            scores = payload["scores"]

            sentiment_avg = round(sum(scores) / len(scores), 4) if scores else 0.0
            growth_rate = round(
                calculate_growth_rate(mentions_count, previous_mentions),
                4,
            )
            trend_score = calculate_trend_score(
                mentions_count=mentions_count,
                growth_rate=growth_rate,
                sentiment_avg=sentiment_avg,
            )

            db.add(
                TrendMetric(
                    topic_id=topic_id,
                    date=day,
                    mentions_count=mentions_count,
                    growth_rate=growth_rate,
                    sentiment_avg=sentiment_avg,
                    trend_score=trend_score,
                )
            )

            previous_mentions = mentions_count
            created += 1

    db.commit()
    return {"trend_rows_created": created}