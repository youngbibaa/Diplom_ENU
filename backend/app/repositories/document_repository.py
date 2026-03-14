from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Document]:
        return self.db.query(Document).order_by(Document.collected_at.desc()).all()

    def exists_by_url_or_hash(self, *, url: str | None, content_hash: str) -> bool:
        query = self.db.query(Document)
        if url:
            if query.filter(Document.url == url).first():
                return True
        return query.filter(Document.content_hash == content_hash).first() is not None

    def create(self, **kwargs) -> Document:
        document = Document(**kwargs)
        self.db.add(document)
        self.db.flush()
        return document
