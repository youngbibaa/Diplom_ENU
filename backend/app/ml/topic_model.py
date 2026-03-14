from __future__ import annotations

from dataclasses import dataclass

from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

from app.preprocessing.cleaner import RU_STOPWORDS, RussianTextPreprocessor


@dataclass
class TopicDefinition:
    name: str
    keywords: str


@dataclass
class TopicAssignment:
    topic_index: int
    probability: float


class LDATopicModeler:
    def __init__(self, topic_count: int = 5, top_words_per_topic: int = 7):
        self.topic_count = topic_count
        self.top_words_per_topic = top_words_per_topic
        self.preprocessor = RussianTextPreprocessor(keep_stopwords=False)

    def build_topics(self, texts: list[str]) -> tuple[list[TopicDefinition], list[TopicAssignment]]:
        filtered_texts = [text for text in texts if text and text.strip()]
        if len(filtered_texts) < 2:
            return [], []

        topic_count = min(self.topic_count, len(filtered_texts))
        vectorizer = CountVectorizer(
            max_df=0.9,
            min_df=1,
            stop_words=list(RU_STOPWORDS),
            token_pattern=r"(?u)\b\w\w+\b",
        )
        document_term_matrix = vectorizer.fit_transform(filtered_texts)
        if document_term_matrix.shape[1] == 0:
            return [], []

        lda = LatentDirichletAllocation(
            n_components=topic_count,
            random_state=42,
            learning_method="batch",
            max_iter=30,
        )
        lda.fit(document_term_matrix)

        feature_names = vectorizer.get_feature_names_out()
        topics: list[TopicDefinition] = []
        for idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[-self.top_words_per_topic:][::-1]
            keywords = [feature_names[i] for i in top_indices]
            topics.append(TopicDefinition(name=f"Topic {idx + 1}", keywords=", ".join(keywords)))

        topic_matrix = lda.transform(document_term_matrix)
        assignments: list[TopicAssignment] = []
        for row in topic_matrix:
            topic_index = int(row.argmax())
            assignments.append(TopicAssignment(topic_index=topic_index, probability=float(row[topic_index])))

        return topics, assignments
