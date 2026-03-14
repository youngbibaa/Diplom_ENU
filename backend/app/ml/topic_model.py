from __future__ import annotations

from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS


CUSTOM_NEWS_STOPWORDS = {
    "said", "says", "say", "latest", "despite", "investigation", "ties",
    "region", "official", "officials", "people", "person", "country", "countries",
    "state", "states", "president", "minister", "ministers", "government",
    "week", "weeks", "month", "months", "year", "years", "day", "days",
    "today", "yesterday", "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "new", "must", "may", "might",
    "one", "two", "three", "our", "their", "his", "her", "she", "they",
    "mr", "mrs", "ms", "according", "reported", "report",
    "news", "times", "york", "middle", "east"
}

DEFAULT_STOPWORDS = ENGLISH_STOP_WORDS.union(CUSTOM_NEWS_STOPWORDS)

WEAK_TOPIC_WORDS = DEFAULT_STOPWORDS.union({
    "attack", "attacks", "war", "conflict", "crisis", "situation"
})


def _is_good_topic_name_token(token: str) -> bool:
    token = token.strip().lower()
    if not token:
        return False
    if token in WEAK_TOPIC_WORDS and token not in {"iran", "israel", "china", "oil"}:
        return False
    if len(token) < 4 and token not in {"iran", "iraq", "oil"}:
        return False
    return True


def _build_topic_name(keywords: list[str], topic_index: int) -> str:
    selected = []

    for keyword in keywords:
        keyword = keyword.strip().lower()
        if not keyword:
            continue

        parts = [part for part in keyword.split() if _is_good_topic_name_token(part)]
        if not parts:
            continue

        candidate = " ".join(parts[:2]).strip()
        if candidate and candidate not in selected:
            selected.append(candidate)

        if len(selected) >= 3:
            break

    if not selected:
        fallback = [kw for kw in keywords if kw.strip()]
        if fallback:
            return " / ".join(fallback[:3])
        return f"Topic {topic_index}"

    return " / ".join(selected[:3])


def build_topics(texts: list[str], n_topics: int = 5, n_top_words: int = 7):
    filtered_texts = [text for text in texts if text and text.strip()]
    if len(filtered_texts) < 3:
        return [], []

    min_df = 2 if len(filtered_texts) >= 10 else 1

    vectorizer = CountVectorizer(
        stop_words=list(DEFAULT_STOPWORDS),
        max_df=0.85,
        min_df=min_df,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b",
    )

    dtm = vectorizer.fit_transform(filtered_texts)

    if dtm.shape[1] == 0:
        return [], []

    n_topics = min(n_topics, max(1, min(dtm.shape[0], dtm.shape[1])))

    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        learning_method="batch",
        max_iter=30,
    )
    lda.fit(dtm)

    feature_names = vectorizer.get_feature_names_out()
    topics = []

    for topic_idx, topic_weights in enumerate(lda.components_, start=1):
        sorted_indices = topic_weights.argsort()[::-1]

        keywords = []
        seen = set()

        for term_idx in sorted_indices:
            term = feature_names[term_idx].strip().lower()
            if not term:
                continue
            if term in seen:
                continue
            if all(part in DEFAULT_STOPWORDS for part in term.split()):
                continue

            keywords.append(term)
            seen.add(term)

            if len(keywords) >= n_top_words:
                break

        topic_name = _build_topic_name(keywords, topic_idx)

        topics.append(
            {
                "name": topic_name,
                "keywords": ", ".join(keywords),
            }
        )

    doc_topic_matrix = lda.transform(dtm)
    assignments = []

    for row in doc_topic_matrix:
        topic_index = int(row.argmax())
        probability = float(row[topic_index])
        assignments.append((topic_index, probability))

    return topics, assignments