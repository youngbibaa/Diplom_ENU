from pydantic import BaseModel, HttpUrl


class RSSIngestRequest(BaseModel):
    feed_url: HttpUrl


class IngestResponse(BaseModel):
    source_id: int
    inserted: int
    skipped_duplicates: int
