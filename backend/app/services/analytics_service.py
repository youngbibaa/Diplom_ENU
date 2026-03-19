import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.models.document_topic import DocumentTopic
from app.preprocessing.cleaner import clean_text
from app.ml.sentiment_model import predict_sentiment
from app.ml.topic_model import build_topics

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  Параметры фильтрации корпуса
# ─────────────────────────────────────────────

# Только статьи не старше этого количества дней участвуют в topic modeling.
# Исключает архивные статьи BBC/NYT (2023–2024), которые попадают в RSS
# и искажают trend_score и growth_rate.
TOPIC_MAX_AGE_DAYS = 30

TOPIC_MIN_TOKEN_COUNT = 20
TOPIC_MIN_UNIQUE_WORDS = 8
TOPIC_ASSIGNMENT_MIN_PROBABILITY = 0.45

TOPIC_COUNT_THRESHOLDS = [
    (600, 9),
    (300, 8),
    (150, 7),
    (80,  6),
    (30,  5),
    (10,  4),
    (0,   3),
]

BLOCKED_URL_PATTERNS = (
    "/video/", "/briefing/", "/arts/",
    "/music/", "/opinion/", "/interactive/", "/live/",
)

NOISY_TEXT_PATTERNS = (
    "video loaded", "advertisement", "sign up", "newsletter",
    "supported by", "listen to this article", "watch:",
    "opinion video", "visual investigations",
)

NOISY_TITLE_PATTERNS = (
    "what's good", "what\u2019s good",
    "morning briefing", "evening briefing",
)


# ─────────────────────────────────────────────
#  Вспомогательные функции
# ─────────────────────────────────────────────

def _token_count(text: str | None) -> int:
    if not text:
        return 0
    return len([t for t in text.split() if t.strip()])


def _unique_word_count(text: str | None) -> int:
    if not text:
        return 0
    return len(set(t.lower() for t in text.split() if t.strip()))


def _contains_noise(text: str | None, patterns: tuple[str, ...]) -> bool:
    if not text:
        return False
    return any(p in text.lower() for p in patterns)


def _get_adaptive_n_topics(n_docs: int) -> int:
    for threshold, n_topics in TOPIC_COUNT_THRESHOLDS:
        if n_docs >= threshold:
            return n_topics
    return 3


def _is_recent(doc: Document, cutoff: datetime) -> bool:
    """Проверяет, что документ опубликован не раньше cutoff."""
    pub = doc.published_at or doc.collected_at
    if not pub:
        return False
    if pub.tzinfo is None:
        pub = pub.replace(tzinfo=timezone.utc)
    return pub >= cutoff


def _is_document_eligible_for_topics(
    doc: Document,
    cutoff: datetime,
) -> tuple[bool, str | None]:
    url = (doc.url or "").lower()
    title = (doc.title or "").strip()
    text_clean = (doc.text_clean or "").strip()

    if not text_clean:
        return False, "empty_text"

    if not _is_recent(doc, cutoff):
        return False, "too_old"

    if _token_count(text_clean) < TOPIC_MIN_TOKEN_COUNT:
        return False, "too_short"

    if _unique_word_count(text_clean) < TOPIC_MIN_UNIQUE_WORDS:
        return False, "low_unique_words"

    if len(title.split()) < 3:
        return False, "short_title"

    if url and any(p in url for p in BLOCKED_URL_PATTERNS):
        return False, "blocked_url"

    if _contains_noise(title, NOISY_TITLE_PATTERNS):
        return False, "noisy_title"

    if _contains_noise(text_clean, NOISY_TEXT_PATTERNS):
        return False, "noisy_text"

    return True, None


# ─────────────────────────────────────────────
#  Основная функция аналитики
# ─────────────────────────────────────────────

def run_analytics(db: Session) -> dict:
    logger.info("Analytics: started")

    documents = db.query(Document).all()
    if not documents:
        logger.info("Analytics: no documents found")
        return {"processed": 0, "topics_created": 0}

    logger.info("Analytics: documents loaded = %s", len(documents))

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=TOPIC_MAX_AGE_DAYS)
    logger.info("Analytics: topic modeling cutoff = %s", cutoff.date())

    # ── 1. Предобработка + sentiment (все документы без ограничения по дате) ─
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
            db.add(SentimentResult(document_id=doc.id, label=label, score=score))

        processed += 1

    db.commit()
    logger.info("Analytics: sentiment updated for %s documents", processed)

    # ── 2. Очистка старых тем ────────────────────────────────────────────────
    deleted_doc_topics = db.query(DocumentTopic).delete()
    deleted_topics = db.query(Topic).delete()
    db.commit()
    logger.info(
        "Analytics: cleared previous topics (doc_topics=%s, topics=%s)",
        deleted_doc_topics, deleted_topics,
    )

    # ── 3. Фильтрация корпуса (только свежие документы) ─────────────────────
    all_docs = db.query(Document).all()
    eligible_docs: list[Document] = []
    skipped_reasons: Counter = Counter()

    for doc in all_docs:
        eligible, reason = _is_document_eligible_for_topics(doc, cutoff)
        if eligible:
            eligible_docs.append(doc)
        else:
            skipped_reasons[reason] += 1

    logger.info("Analytics: eligible for topic modeling = %s", len(eligible_docs))
    if skipped_reasons:
        logger.info("Analytics: skipped by reason = %s", dict(skipped_reasons))

    if len(eligible_docs) < 3:
        logger.info("Analytics: not enough eligible documents")
        return {
            "processed": processed,
            "topics_created": 0,
            "eligible_for_topics": len(eligible_docs),
            "assigned_to_topics": 0,
        }

    # ── 4. Topic modeling ────────────────────────────────────────────────────
    texts = [doc.text_clean for doc in eligible_docs]
    n_topics = _get_adaptive_n_topics(len(eligible_docs))
    logger.info("Analytics: n_topics=%s for %s docs", n_topics, len(eligible_docs))

    topics_data, assignments = build_topics(texts=texts, n_topics=n_topics, n_top_words=7)

    if not topics_data:
        logger.info("Analytics: no topics built")
        return {
            "processed": processed,
            "topics_created": 0,
            "eligible_for_topics": len(eligible_docs),
            "assigned_to_topics": 0,
        }

    # ── 5. Сохранение тем ────────────────────────────────────────────────────
    topic_objects: list[Topic] = []
    for td in topics_data:
        t = Topic(name=td["name"], keywords=td["keywords"])
        db.add(t)
        topic_objects.append(t)

    db.commit()
    for t in topic_objects:
        db.refresh(t)

    logger.info("Analytics: topics created = %s", len(topic_objects))

    # ── 6. Назначение документов темам ───────────────────────────────────────
    assigned_count = 0
    skipped_low_prob = 0

    for doc, (topic_index, probability) in zip(eligible_docs, assignments):
        if topic_index >= len(topic_objects):
            continue
        if probability < TOPIC_ASSIGNMENT_MIN_PROBABILITY:
            skipped_low_prob += 1
            continue

        db.add(DocumentTopic(
            document_id=doc.id,
            topic_id=topic_objects[topic_index].id,
            probability=round(probability, 4),
        ))
        assigned_count += 1

    db.commit()

    logger.info("Analytics: assignments created = %s", assigned_count)
    logger.info("Analytics: skipped low-prob = %s", skipped_low_prob)
    logger.info("Analytics: finished")

    return {
        "processed": processed,
        "topics_created": len(topic_objects),
        "eligible_for_topics": len(eligible_docs),
        "assigned_to_topics": assigned_count,
        "skipped_low_prob": skipped_low_prob,
        "skipped_reasons": dict(skipped_reasons),
    }