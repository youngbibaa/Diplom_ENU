from pydantic import BaseModel, HttpUrl, field_validator


class IngestRequest(BaseModel):
    feed_url: str


class IngestBulkRequest(BaseModel):
    feed_urls: list[str]

    @field_validator("feed_urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("feed_urls не может быть пустым")
        if len(v) > 30:
            raise ValueError("Максимум 30 источников за один запрос")
        return [url.strip() for url in v if url.strip()]


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
