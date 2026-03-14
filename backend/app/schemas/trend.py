from datetime import date

from app.schemas.common import ORMModel


class TrendItem(ORMModel):
    topic_id: int
    topic_name: str
    date: date
    mentions_count: int
    growth_rate: float
    sentiment_avg: float
    trend_score: float
