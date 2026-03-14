from datetime import datetime

from app.schemas.common import ORMModel


class DocumentOut(ORMModel):
    id: int
    source_id: int
    title: str
    url: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    collected_at: datetime
    text_clean: str | None = None
