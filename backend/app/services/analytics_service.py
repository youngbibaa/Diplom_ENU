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

# ─────────────────────────────────────────────
#  Параметры фильтрации корпуса
# ─────────────────────────────────────────────

# Минимальное число токенов после очистки для участия в topic modeling.
# 8 (старое значение) — слишком мало, это одно-два предложения.
# 20 — разумный минимум для LDA: достаточно сигнала, мало шума.
TOPIC_MIN_TOKEN_COUNT = 20

# Минимальная доля кириллических символов для русскоязычных документов.
# Фильтрует смешанный мусор (коды, URL, транслит).
RU_CHAR_RATIO_THRESHOLD = 0.4

# Минимальное число уникальных слов в документе.
# Короткий повтор одного слова — не тема.
TOPIC_MIN_UNIQUE_WORDS = 8

# Порог уверенности при назначении темы документу.
# LDA даёт распределение по темам; берём только высоковероятные назначения.
TOPIC_ASSIGNMENT_MIN_PROBABILITY = 0.45  # снижено с 0.65 — меньше "неназначенных"

# Адаптивное число тем:
# маленький корпус → меньше тем, большой → больше.
TOPIC_COUNT_THRESHOLDS = [
    (200, 7),
    (80,  6),
    (30,  5),
    (10,  4),
    (0,   3),
]

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
    "what's good",
    "what\u2019s good",
    "morning briefing",
    "evening briefing",
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


def _cyrillic_ratio(text: str | None) -> float:
    """Доля кириллических символов в тексте (без пробелов)."""
    if not text:
        return 0.0
    chars = [c for c in text if c.strip()]
    if not chars:
        return 0.0
    cyrillic = sum(1 for c in chars if "\u0400" <= c <= "\u04ff")
    return cyrillic / len(chars)


def _contains_noise(text: str | None, patterns: tuple[str, ...]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(p in lowered for p in patterns)


def _get_adaptive_n_topics(n_docs: int) -> int:
    for threshold, n_topics in TOPIC_COUNT_THRESHOLDS:
        if n_docs >= threshold:
            return n_topics
    return 3


def _is_document_eligible_for_topics(doc: Document) -> tuple[bool, str | None]:
    """
    Определяет, подходит ли документ для участия в topic modeling.

    Возвращает (True, None) если документ подходит,
    или (False, reason) с причиной исключения.
    """
    url = (doc.url or "").lower()
    title = (doc.title or "").strip()
    text_clean = (doc.text_clean or "").strip()

    if not text_clean:
        return False, "empty_text"

    # Улучшенный порог: 20 токенов вместо 8
    if _token_count(text_clean) < TOPIC_MIN_TOKEN_COUNT:
        return False, "too_short"

    # Слишком мало уникальных слов — вероятно мусор или повтор
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

    # ── 1. Предобработка текста + sentiment ──────────────────────────────────
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
        "Analytics: cleared previous topics (document_topics=%s, topics=%s)",
        deleted_doc_topics, deleted_topics,
    )

    # ── 3. Фильтрация корпуса ────────────────────────────────────────────────
    all_docs = db.query(Document).all()
    eligible_docs: list[Document] = []
    skipped_reasons: Counter = Counter()

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

    # ── 4. Topic modeling ────────────────────────────────────────────────────
    texts = [doc.text_clean for doc in eligible_docs]

    # Адаптивное число тем в зависимости от размера корпуса
    n_topics = _get_adaptive_n_topics(len(eligible_docs))
    logger.info("Analytics: using n_topics=%s for %s eligible docs", n_topics, len(eligible_docs))

    topics_data, assignments = build_topics(
        texts=texts,
        n_topics=n_topics,
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

    # ── 5. Сохранение тем в БД ───────────────────────────────────────────────
    topic_objects: list[Topic] = []
    for topic_data in topics_data:
        topic = Topic(name=topic_data["name"], keywords=topic_data["keywords"])
        db.add(topic)
        topic_objects.append(topic)

    db.commit()
    for topic in topic_objects:
        db.refresh(topic)

    logger.info("Analytics: topics built = %s", len(topic_objects))

    # ── 6. Назначение документов темам ───────────────────────────────────────
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
        "skipped_low_prob": skipped_low_probability,
        "skipped_reasons": dict(skipped_reasons),
    }
