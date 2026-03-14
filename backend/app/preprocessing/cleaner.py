from __future__ import annotations

import hashlib
import re
from functools import lru_cache

import pymorphy3

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]+>")
NON_WORD_RE = re.compile(r"[^a-zA-Zа-яА-ЯёЁ0-9\s-]")
DASH_RE = re.compile(r"[\u2012-\u2015]")
MULTISPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ-]{2,}")

RU_STOPWORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все", "она", "так",
    "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по", "только", "ее", "мне", "было",
    "вот", "от", "меня", "еще", "нет", "о", "из", "ему", "теперь", "когда", "даже", "ну", "вдруг",
    "ли", "если", "уже", "или", "ни", "быть", "был", "него", "до", "вас", "нибудь", "опять", "уж",
    "вам", "ведь", "там", "потом", "себя", "ничего", "ей", "может", "они", "тут", "где", "есть", "надо",
    "ней", "для", "мы", "тебя", "их", "чем", "была", "сам", "чтоб", "без", "будто", "чего", "раз",
    "тоже", "себе", "под", "будет", "ж", "тогда", "кто", "этот", "того", "потому", "этого", "какой",
    "совсем", "ним", "здесь", "этом", "один", "почти", "мой", "тем", "чтобы", "нее", "сейчас", "были",
    "куда", "зачем", "всех", "никогда", "можно", "при", "наконец", "два", "об", "другой", "хоть", "после",
    "над", "больше", "тот", "через", "эти", "нас", "про", "всего", "них", "какая", "много", "разве",
    "три", "эту", "моя", "впрочем", "хорошо", "свою", "этой", "перед", "иногда", "лучше", "чуть", "том",
    "нельзя", "такой", "им", "более", "всегда", "конечно", "всю", "между", "это", "этот", "эта", "эти",
    "the", "and", "for", "that", "with", "from", "this", "have", "has", "are", "was", "were", "will",
    "into", "about", "after", "before", "than", "them", "they", "their", "said", "says", "would", "could",
}


@lru_cache(maxsize=1)
def _get_morph() -> pymorphy3.MorphAnalyzer:
    return pymorphy3.MorphAnalyzer()


class RussianTextPreprocessor:
    def __init__(self, keep_stopwords: bool = False):
        self.keep_stopwords = keep_stopwords
        self.morph = _get_morph()

    def normalize_raw(self, text: str) -> str:
        text = (text or "").lower().replace("ё", "е")
        text = DASH_RE.sub("-", text)
        text = URL_RE.sub(" ", text)
        text = HTML_TAG_RE.sub(" ", text)
        text = NON_WORD_RE.sub(" ", text)
        text = MULTISPACE_RE.sub(" ", text).strip()
        return text

    def tokenize(self, text: str) -> list[str]:
        normalized = self.normalize_raw(text)
        return TOKEN_RE.findall(normalized)

    def lemmatize_token(self, token: str) -> str:
        if token.isascii():
            return token
        try:
            return self.morph.parse(token)[0].normal_form
        except Exception:
            return token

    def preprocess_tokens(self, text: str) -> list[str]:
        result: list[str] = []
        for token in self.tokenize(text):
            lemma = self.lemmatize_token(token)
            if len(lemma) < 2:
                continue
            if not self.keep_stopwords and lemma in RU_STOPWORDS:
                continue
            result.append(lemma)
        return result

    def preprocess_text(self, text: str) -> str:
        return " ".join(self.preprocess_tokens(text))


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        return RussianTextPreprocessor(keep_stopwords=False).preprocess_text(text)

    @staticmethod
    def hash_content(title: str, text: str) -> str:
        payload = f"{title.strip()}||{text.strip()}".encode("utf-8", errors="ignore")
        return hashlib.sha256(payload).hexdigest()
