import hashlib
import re
from functools import lru_cache

import pymorphy3


EN_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "had", "has", "have", "he", "her", "his", "in", "is", "it", "its",
    "of", "on", "or", "that", "the", "their", "there", "they", "this", "to",
    "was", "were", "will", "with", "would", "could", "should", "into", "than",
    "then", "them", "who", "whom", "what", "when", "where", "why", "how",
    "about", "after", "before", "during", "over", "under", "again", "further",
    "once", "here", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "too",
    "very", "can", "just", "don", "now",
    # news/domain stopwords
    "said", "says", "say", "latest", "despite", "investigation", "ties",
    "region", "official", "officials", "people", "person", "country", "countries",
    "state", "states", "president", "minister", "ministers", "government",
    "week", "weeks", "month", "months", "year", "years", "day", "days",
    "today", "yesterday", "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "new", "must", "may", "might",
    "one", "two", "three", "our", "their", "his", "her", "she", "they",
    "mr", "mrs", "ms", "latest", "according", "reported", "report",
    "news", "times", "york",
}

RU_STOPWORDS = {
    "и", "в", "во", "на", "но", "а", "о", "об", "от", "до", "по", "из", "у",
    "за", "с", "со", "к", "ко", "для", "при", "над", "под", "без", "не", "ни",
    "что", "как", "так", "это", "этот", "эта", "эти", "то", "те", "же", "ли",
    "или", "бы", "был", "была", "были", "быть", "есть", "нет", "его", "ее",
    "их", "мы", "вы", "они", "он", "она", "оно", "я", "ты", "меня", "мне",
    "тебя", "вам", "нас", "них", "который", "которая", "которые", "которое",
    "такой", "такая", "такие", "уже", "еще", "только", "если", "чтобы", "после",
    "перед", "между", "через"
}


@lru_cache
def get_morph():
    return pymorphy3.MorphAnalyzer()


def detect_language(text: str) -> str:
    ru_count = len(re.findall(r"[а-яА-ЯёЁ]", text))
    en_count = len(re.findall(r"[a-zA-Z]", text))
    return "ru" if ru_count >= en_count else "en"


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Zа-яА-ЯёЁ\-]{3,}", text.lower())


def lemmatize_ru(tokens: list[str]) -> list[str]:
    morph = get_morph()
    lemmas = []
    for token in tokens:
        parsed = morph.parse(token)
        lemmas.append(parsed[0].normal_form if parsed else token)
    return lemmas


def remove_stopwords(tokens: list[str], lang: str) -> list[str]:
    stopwords = RU_STOPWORDS if lang == "ru" else EN_STOPWORDS
    return [token for token in tokens if token not in stopwords]


def clean_text(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return ""

    lang = detect_language(normalized)
    tokens = tokenize(normalized)

    if lang == "ru":
        tokens = lemmatize_ru(tokens)

    tokens = remove_stopwords(tokens, lang)
    return " ".join(tokens)


class TextCleaner:
    def clean(self, text: str) -> str:
        return clean_text(text)

    def normalize(self, text: str) -> str:
        return normalize_text(text)

    def tokenize(self, text: str) -> list[str]:
        return tokenize(text)

    def hash_content(self, text: str) -> str:
        cleaned = self.clean(text)
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


class RussianTextPreprocessor:
    def clean(self, text: str) -> str:
        return clean_text(text)