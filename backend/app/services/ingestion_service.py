from sqlalchemy.orm import Session

from app.parsers.rss_parser import RSSParser
from app.preprocessing.cleaner import TextCleaner
from app.repositories.document_repository import DocumentRepository
from app.repositories.source_repository import SourceRepository


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.source_repo = SourceRepository(db)
        self.document_repo = DocumentRepository(db)
        self.parser = RSSParser()
        self.cleaner = TextCleaner()

    def ingest_rss(self, feed_url: str) -> dict:
        source = self.source_repo.get_or_create(name=feed_url, source_type="rss", url=feed_url)
        parsed_items = self.parser.parse(feed_url)

        inserted = 0
        skipped_duplicates = 0

        for item in parsed_items:
            if not item.text_raw.strip():
                continue

            content_hash = self.cleaner.hash_content(item.title, item.text_raw)
            if self.document_repo.exists_by_url_or_hash(url=item.url or None, content_hash=content_hash):
                skipped_duplicates += 1
                continue

            self.document_repo.create(
                source_id=source.id,
                title=item.title,
                text_raw=item.text_raw,
                content_hash=content_hash,
                url=item.url or None,
                author=item.author,
                published_at=item.published_at,
            )
            inserted += 1

        self.db.commit()
        return {
            "source_id": source.id,
            "inserted": inserted,
            "skipped_duplicates": skipped_duplicates,
        }
