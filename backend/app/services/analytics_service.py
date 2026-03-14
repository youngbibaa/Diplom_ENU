from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.sentiment_model import TfidfLogRegSentimentAnalyzer
from app.ml.topic_model import LDATopicModeler
from app.models.document import Document
from app.models.document_topic import DocumentTopic
from app.models.sentiment_result import SentimentResult
from app.models.topic import Topic
from app.preprocessing.cleaner import RussianTextPreprocessor


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.preprocessor = RussianTextPreprocessor(keep_stopwords=False)
        self.sentiment_analyzer = TfidfLogRegSentimentAnalyzer()
        self.topic_modeler = LDATopicModeler(settings.topic_count, settings.top_words_per_topic)

    def run(self) -> dict:
        documents = self.db.query(Document).all()
        if not documents:
            return {"processed": 0, "topics_created": 0}

        processed = 0
        for document in documents:
            cleaned = self.preprocessor.preprocess_text(document.text_raw)
            document.text_clean = cleaned
            prediction = self.sentiment_analyzer.predict(document.text_raw)

            existing = (
                self.db.query(SentimentResult)
                .filter(SentimentResult.document_id == document.id)
                .first()
            )
            if existing:
                existing.label = prediction.label
                existing.score = prediction.score
            else:
                self.db.add(
                    SentimentResult(
                        document_id=document.id,
                        label=prediction.label,
                        score=prediction.score,
                    )
                )
            processed += 1

        self.db.commit()

        self.db.query(DocumentTopic).delete()
        self.db.query(Topic).delete()
        self.db.commit()

        clean_documents = (
            self.db.query(Document)
            .filter(Document.text_clean.is_not(None))
            .filter(func.length(Document.text_clean) > 0)
            .all()
        )
        texts = [document.text_clean for document in clean_documents if document.text_clean]
        topics, assignments = self.topic_modeler.build_topics(texts)

        topic_entities: list[Topic] = []
        for item in topics:
            topic = Topic(name=item.name, keywords=item.keywords)
            self.db.add(topic)
            topic_entities.append(topic)

        self.db.commit()
        for topic in topic_entities:
            self.db.refresh(topic)

        indexed_docs = [document for document in clean_documents if document.text_clean]
        for document, assignment in zip(indexed_docs, assignments):
            if assignment.topic_index < len(topic_entities):
                self.db.add(
                    DocumentTopic(
                        document_id=document.id,
                        topic_id=topic_entities[assignment.topic_index].id,
                        probability=assignment.probability,
                    )
                )

        self.db.commit()
        return {"processed": processed, "topics_created": len(topic_entities)}
