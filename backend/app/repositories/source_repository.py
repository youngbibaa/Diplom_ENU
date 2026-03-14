from sqlalchemy.orm import Session

from app.models.source import Source


class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, *, name: str, source_type: str, url: str | None) -> Source:
        source = self.db.query(Source).filter(Source.url == url).first() if url else None
        if source:
            return source
        source = Source(name=name, type=source_type, url=url)
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source
