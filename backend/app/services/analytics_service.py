import logging
from collections import Counter
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.models.document_topic import DocumentTopic
from app.preprocessing.cleaner import clean_text
from app.ml.sentiment_model import predict_sentiment
from app.ml.topic_model import build_topics

logger = logging.getLogger(__name__)

TOPIC_ASSIGNMENT_MIN_PROBABILITY = 0.65

BLOCKED_URL_PATTERNS = (
    "/video/",
    "/briefing/",
    "/arts/",
    "/music/",
    "/opinion/",
    "/interactive/",
    "/live/",
)

NOISY_TEXT_PATTERNS = (
    "video loaded",
    "advertisement",
    "sign up",
    "newsletter",
    "supported by",
    "listen to this article",
    "watch:",
    "opinion video",
    "visual investigations",
)

NOISY_TITLE_PATTERNS = (
    "what’s good",
    "what's good",
    "morning briefing",
    "evening briefing",
)


def _token_count(text: str | None) -> int:
    if not text:
        return 0
    return len([token for token in text.split() if token.strip()])


def _contains_noise(text: str | None, patterns: tuple[str, ...]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def _is_document_eligible_for_topics(doc: Document) -> tuple[bool, str | None]:
    """
    Возвращает:
    (True, None)  -> документ можно использовать для topic modeling
    (False, reason) -> документ исключаем из topic modeling
    """
    url = (doc.url or "").lower()
    title = (doc.title or "").strip()
    text_clean = (doc.text_clean or "").strip()

    if not text_clean:
        return False, "empty_text"

    if _token_count(text_clean) < 8:
        return False, "too_short"

    if len(title.split()) < 3:
        return False, "short_title"

    if url and any(pattern in url for pattern in BLOCKED_URL_PATTERNS):
        return False, "blocked_url"

    if _contains_noise(title, NOISY_TITLE_PATTERNS):
        return False, "noisy_title"

    if _contains_noise(text_clean, NOISY_TEXT_PATTERNS):
        return False, "noisy_text"

    return True, None


def run_analytics(db: Session) -> dict:
    logger.info("Analytics: started")

    documents = db.query(Document).all()
    if not documents:
        logger.info("Analytics: no documents found")
        return {"processed": 0, "topics_created": 0}

    logger.info("Analytics: documents loaded = %s", len(documents))

    processed = 0

    for doc in documents:
        cleaned = clean_text(doc.text_raw or "")
        doc.text_clean = cleaned

        label, score = predict_sentiment(cleaned)

        existing = (
            db.query(SentimentResult)
            .filter(SentimentResult.document_id == doc.id)
            .first()
        )

        if existing:
            existing.label = label
            existing.score = score
        else:
            db.add(
                SentimentResult(
                    document_id=doc.id,
                    label=label,
                    score=score,
                )
            )

        processed += 1

    db.commit()
    logger.info("Analytics: sentiment updated for %s documents", processed)

    deleted_doc_topics = db.query(DocumentTopic).delete()
    deleted_topics = db.query(Topic).delete()
    db.commit()

    logger.info(
        "Analytics: cleared previous topics (document_topics=%s, topics=%s)",
        deleted_doc_topics,
        deleted_topics,
    )

    all_docs = db.query(Document).all()

    eligible_docs: list[Document] = []
    skipped_reasons = Counter()

    for doc in all_docs:
        eligible, reason = _is_document_eligible_for_topics(doc)
        if eligible:
            eligible_docs.append(doc)
        else:
            skipped_reasons[reason] += 1

    logger.info("Analytics: eligible documents for topic modeling = %s", len(eligible_docs))
    if skipped_reasons:
        logger.info("Analytics: excluded documents by reason = %s", dict(skipped_reasons))

    if len(eligible_docs) < 3:
        logger.info("Analytics: not enough eligible documents for topic modeling")
        return {
            "processed": processed,
            "topics_created": 0,
            "eligible_for_topics": len(eligible_docs),
            "assigned_to_topics": 0,
        }

    texts = [doc.text_clean for doc in eligible_docs]

    topics_data, assignments = build_topics(
        texts=texts,
        n_topics=5,
        n_top_words=7,
    )

    if not topics_data:
        logger.info("Analytics: no topics built")
        return {
            "processed": processed,
            "topics_created": 0,
            "eligible_for_topics": len(eligible_docs),
            "assigned_to_topics": 0,
        }

    topic_objects: list[Topic] = []

    for topic_data in topics_data:
        topic = Topic(
            name=topic_data["name"],
            keywords=topic_data["keywords"],
        )
        db.add(topic)
        topic_objects.append(topic)

    db.commit()

    for topic in topic_objects:
        db.refresh(topic)

    logger.info("Analytics: topics built = %s", len(topic_objects))

    assigned_count = 0
    skipped_low_probability = 0

    for doc, (topic_index, probability) in zip(eligible_docs, assignments):
        if topic_index >= len(topic_objects):
            continue

        if probability < TOPIC_ASSIGNMENT_MIN_PROBABILITY:
            skipped_low_probability += 1
            continue

        db.add(
            DocumentTopic(
                document_id=doc.id,
                topic_id=topic_objects[topic_index].id,
                probability=round(probability, 4),
            )
        )
        assigned_count += 1

    db.commit()

    logger.info("Analytics: topic assignments created = %s", assigned_count)
    logger.info("Analytics: low-probability assignments skipped = %s", skipped_low_probability)
    logger.info("Analytics: finished")

    return {
        "processed": processed,
        "topics_created": len(topic_objects),
        "eligible_for_topics": len(eligible_docs),
        "assigned_to_topics": assigned_count,
    }