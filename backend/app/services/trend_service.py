from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.ml.trend_detector import TrendCalculator
from app.models.document import Document
from app.models.document_topic import DocumentTopic
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.models.trend_metric import TrendMetric


class TrendService:
    def __init__(self, db: Session):
        self.db = db
        self.calculator = TrendCalculator()

    def rebuild(self) -> dict:
        self.db.query(TrendMetric).delete()
        self.db.commit()

        rows = (
            self.db.query(DocumentTopic, Document, Topic, SentimentResult)
            .join(Document, DocumentTopic.document_id == Document.id)
            .join(Topic, DocumentTopic.topic_id == Topic.id)
            .outerjoin(SentimentResult, SentimentResult.document_id == Document.id)
            .all()
        )

        grouped: dict[tuple[int, date], list[float]] = defaultdict(list)
        for document_topic, document, topic, sentiment in rows:
            doc_date = document.published_at.date() if document.published_at else document.collected_at.date()
            grouped[(topic.id, doc_date)].append(sentiment.score if sentiment else 0.0)

        by_topic: dict[int, list[tuple[date, list[float]]]] = defaultdict(list)
        for (topic_id, day), scores in grouped.items():
            by_topic[topic_id].append((day, scores))

        created = 0
        for topic_id, items in by_topic.items():
            items.sort(key=lambda item: item[0])
            previous_mentions = 0
            for day, scores in items:
                mentions_count = len(scores)
                sentiment_avg = sum(scores) / mentions_count if mentions_count else 0.0
                growth_rate = self.calculator.growth_rate(mentions_count, previous_mentions)
                trend_score = self.calculator.trend_score(mentions_count, growth_rate, sentiment_avg)
                self.db.add(
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

        self.db.commit()
        return {"trend_rows_created": created}
