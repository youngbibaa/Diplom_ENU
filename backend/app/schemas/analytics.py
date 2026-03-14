from app.schemas.common import ORMModel


class AnalyticsRunResponse(ORMModel):
    processed: int
    topics_created: int
    trend_rows_created: int


class SentimentSummaryItem(ORMModel):
    label: str
    count: int


class TopicSummaryItem(ORMModel):
    topic_id: int
    name: str
    keywords: str
    documents_count: int
