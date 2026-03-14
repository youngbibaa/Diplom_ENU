from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.models.document_topic import DocumentTopic
from app.preprocessing.cleaner import clean_text
from app.ml.sentiment_model import predict_sentiment
from app.ml.topic_model import build_topics


def run_analytics(db: Session) -> dict:
    documents = db.query(Document).all()
    if not documents:
        return {"processed": 0, "topics_created": 0}

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

    db.query(DocumentTopic).delete()
    db.query(Topic).delete()
    db.commit()

    indexed_docs = [
        doc for doc in db.query(Document).all()
        if doc.text_clean and doc.text_clean.strip()
    ]
    texts = [doc.text_clean for doc in indexed_docs]

    topics_data, assignments = build_topics(
        texts=texts,
        n_topics=5,
        n_top_words=7,
    )

    if not topics_data:
        return {"processed": processed, "topics_created": 0}

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

    for doc, (topic_index, probability) in zip(indexed_docs, assignments):
        if topic_index < len(topic_objects):
            db.add(
                DocumentTopic(
                    document_id=doc.id,
                    topic_id=topic_objects[topic_index].id,
                    probability=round(probability, 4),
                )
            )

    db.commit()

    return {
        "processed": processed,
        "topics_created": len(topic_objects),
    }