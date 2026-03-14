from sqlalchemy.orm import Session

from app.models.source import Source
from app.models.document import Document
from app.parsers.rss_parser import parse_rss_feed
from app.preprocessing.cleaner import TextCleaner


class IngestionService:
    def __init__(self):
        self.cleaner = TextCleaner()

    def ingest_rss_feed(self, db: Session, feed_url: str) -> dict:
        source = db.query(Source).filter(Source.url == feed_url).first()

        if not source:
            source = Source(name=feed_url, type="rss", url=feed_url)
            db.add(source)
            db.commit()
            db.refresh(source)

        items = parse_rss_feed(feed_url)
        inserted = 0
        skipped = 0

        existing_docs = db.query(Document).all()

        existing_urls = {doc.url for doc in existing_docs if doc.url}

        existing_title_dates = {
            (
                (doc.title or "").strip().lower(),
                doc.published_at.isoformat() if doc.published_at else None,
            )
            for doc in existing_docs
        }

        existing_hashes = set()
        for doc in existing_docs:
            if getattr(doc, "content_hash", None):
                existing_hashes.add(doc.content_hash)
            elif (doc.text_raw or "").strip():
                existing_hashes.add(self.cleaner.hash_content(doc.text_raw))

        for item in items:
            text_raw = (item.get("text_raw") or "").strip()
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            published_at = item.get("published_at")
            author = item.get("author")

            if not text_raw or not title:
                skipped += 1
                continue

            if url and url in existing_urls:
                skipped += 1
                continue

            title_date_key = (
                title.lower(),
                published_at.isoformat() if published_at else None,
            )
            if title_date_key in existing_title_dates:
                skipped += 1
                continue

            text_clean = self.cleaner.clean(text_raw)
            content_hash = self.cleaner.hash_content(text_raw)

            if content_hash in existing_hashes:
                skipped += 1
                continue

            doc = Document(
                source_id=source.id,
                title=title,
                text_raw=text_raw,
                text_clean=text_clean,
                content_hash=content_hash,
                url=url or None,
                author=author,
                published_at=published_at,
            )
            db.add(doc)

            if url:
                existing_urls.add(url)
            existing_title_dates.add(title_date_key)
            existing_hashes.add(content_hash)

            inserted += 1

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "inserted": inserted,
            "skipped": skipped,
            "source_id": source.id,
        }