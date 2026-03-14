from pydantic import BaseModel


class IngestRequest(BaseModel):
    feed_url: str


class AnalyticsRunResponse(BaseModel):
    processed: int
    topics_created: int


class SentimentSummaryItem(BaseModel):
    label: str
    count: int
    share: float
    avg_score: float


class TopicSummaryItem(BaseModel):
    topic_id: int
    name: str
    keywords: str
    documents_count: int