from __future__ import annotations

from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS

# ─────────────────────────────────────────────
#  Стоп-слова
# ─────────────────────────────────────────────

RU_STOPWORDS = {
    # служебные части речи
    "и", "в", "во", "на", "но", "а", "о", "об", "от", "до", "по", "из",
    "у", "за", "с", "со", "к", "ко", "для", "при", "над", "под", "без",
    "не", "ни", "что", "как", "так", "это", "этот", "эта", "эти", "то",
    "те", "же", "ли", "или", "бы", "был", "была", "были", "быть", "есть",
    "нет", "его", "ее", "её", "их", "мы", "вы", "они", "он", "она", "оно",
    "я", "ты", "меня", "мне", "тебя", "вам", "нас", "них",
    "который", "которая", "которые", "которое",
    "такой", "такая", "такие", "уже", "еще", "ещё", "только", "если",
    "чтобы", "после", "перед", "между", "через", "тогда", "когда", "где",
    "здесь", "там", "сейчас", "потом", "затем", "поэтому", "однако",
    "также", "тоже", "всё", "всех", "все", "весь", "вся", "всем",
    # ЛЕММЫ местоимений (pymorphy3 нормализует к этим формам)
    "тот",      # того, тем, тех → тот
    "свой",     # своих, своим, свою → свой
    "каждый",   # каждого → каждый
    "другой",   # другого → другой
    "сам",      # самого → сам
    "один",     # одного → один
    # ЛЕММЫ частотных глаголов без тематической нагрузки
    "мочь",       # может, могут, мог → мочь
    "стать",      # стал, стала → стать
    "говорить",   # говорит, говорят → говорить
    "сказать",    # сказал → сказать
    "являться",   # является → являться
    "получать",   # получает → получать
    "иметь",      # имеет → иметь
    "делать",     # делает → делать
    "хотеть",     # хочет → хотеть
    "идти",       # идёт → идти
    "знать",      # знает → знать
    "видеть",     # видит → видеть
    "работать",   # работает → работать
    "ранее",      # наречие — очень частое в новостях без смысла
    "именно", "просто", "очень", "более", "менее", "около",
    "снова", "вообще", "теперь", "сразу", "пока",
    # новостные шаблонные слова (леммы)
    "сообщить",   # сообщил → сообщить
    "заявить",    # заявил → заявить
    "добавить",   # добавил → добавить
    "отметить",   # отметил → отметить
    "пояснить",   # пояснил → пояснить
    "уточнить",   # уточнил → уточнить
    "передавать", # передаёт → передавать
    "рассказать", # рассказал → рассказать
    "слово",      # по словам → слово
    "президент", "министр", "правительство", "официальный",
    "страна", "государство", "регион",
    "день", "неделя", "месяц", "год",
    "сегодня", "вчера",
    "первый", "второй", "третий", "новый",
    "два", "три", "четыре", "пять",
    "согласно", "данный", "информация",
    "ситуация", "вопрос", "решение", "процесс",
    "результат", "сторона", "время", "место", "часть", "число",
    "уровень", "случай", "человек",
    # Медиа-артефакты (Lenta.ru, RBC и др.)
    "реклама", "фото", "видео",
    "reuters", "afp", "тасс", "интерфакс",
    "агентство", "издание", "канал",
}

CUSTOM_EN_STOPWORDS = {
    "said", "says", "say", "latest", "despite", "investigation", "ties",
    "region", "official", "officials", "people", "person", "country",
    "countries", "state", "states", "president", "minister", "ministers",
    "government", "week", "weeks", "month", "months", "year", "years",
    "day", "days", "today", "yesterday", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday",
    "new", "must", "may", "might", "would", "could",
    "one", "two", "three", "our", "their", "his", "her", "she", "he", "they",
    "mr", "mrs", "ms", "according", "reported", "report",
    "news", "times", "york", "middle", "east",
    "showed", "show", "shows", "earlier", "later",
    "prime", "video", "political", "economic",
    "including", "around", "across", "back", "still",
    "among", "without", "within", "agency", "office", "statement",
    "called", "calling", "told", "saying",
    "first", "second", "third", "least", "almost", "another", "several",
}

EN_STOPWORDS_FULL = ENGLISH_STOP_WORDS.union(CUSTOM_EN_STOPWORDS)

# Дополнительные стоп-слова специфичные для казахских источников
KZ_EXTRA_STOPWORDS = {
    # Погода (inform.kz публикует много погодных новостей)
    "ночью", "днём", "утром", "вечером",
    "туман", "ветер", "температура", "воздух", "осадок",
    "облачный", "дождь", "снег", "мороз", "тепло", "градус",
    "метр", "секунда",
    # Медиа-артефакты
    "kazinform", "автор", "редакция", "лицо", "сайт",
    "агентство", "издание", "канал", "публикация",
    # Месяцы — создают ложные кластеры
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
    # Английские месяцы (из NYT/Reuters)
    "january", "february", "march", "april", "june", "july",
    "august", "september", "october", "november", "december",
    # Глаголы-леммы без тематической нагрузки
    "достигнуть", "зарегистрировать", "поделиться", "ожидаться",
    "составить", "превысить", "увеличиться", "снизиться", "вырасти",
    "должный",    # лемма от «должен/должна» — модальный глагол
    # Географические слова без специфики темы
    "область", "север", "юг", "восток", "запад", "район", "округ",
    # Имена собственные с чрезмерной частотой (вытесняют тематику)
    "токай",           # Токаев (фамилия)
    "касым-жомарт",    # Токаев (имя)
    "владимир",
    # Бренды источников
    "tengrinews", "kursiv", "kapital", "forbes",
    "nbsp", "external",  # BBC RSS артефакт
    # Аббревиатуры
    "млн", "млрд", "тыс",
    # Частотные наречия и модальные слова (леммы)
    "даже", "можно", "нельзя", "надо", "нужно", "важно",
    "хорошо", "плохо", "долго", "быстро", "легко",
    # Частотные глаголы без тематики (леммы)
    "произойти", "выдать", "принять", "провести",
    "начать", "закончить", "продолжить", "остаться",
    "прийти", "появиться", "изменить", "показать",
    # Погода — направления и прилагательные
    "северо-восточный", "юго-западный", "северо-западный", "юго-восточный",
    "восточный", "западный", "северный", "южный",
    "переменный", "облачность", "осадок",
    # Reddit
    "upvote", "downvote", "comment", "reddit", "post", "thread",
    "edit", "link", "tldr",
    # Слишком общие слова (леммы)
    "ребёнок",        # без контекста не несёт тему
    "государственный", # очень частое в KZ-источниках без специфики
    "хороший",        # оценочное без содержания
    "переменный",     # дублирование выше
}

ALL_STOPWORDS = EN_STOPWORDS_FULL.union(RU_STOPWORDS).union(KZ_EXTRA_STOPWORDS)

# Слова, нежелательные в названии темы (слишком общие)
WEAK_TOPIC_NAME_WORDS = ALL_STOPWORDS.union({
    "war", "attack", "attacks", "conflict", "crisis", "situation",
    "strikes", "military", "officials", "reported", "showed",
    "война", "атака", "атаки", "конфликт", "кризис", "ситуация",
    "удары", "военный", "военные",
    # Слова которые попадали в названия тем но не несут смысла
    "наука", "самый", "правило", "себя", "матч", "жизнь",
})

# Короткие токены, важные для новостей (не фильтруем по длине)
IMPORTANT_SHORT_TOKENS = {"iran", "iraq", "oil", "gaza", "isis", "сша", "рф", "оон", "нато"}


# ─────────────────────────────────────────────
#  Формирование названия темы
# ─────────────────────────────────────────────

def _is_good_topic_name_token(token: str) -> bool:
    token = token.strip().lower()
    if not token:
        return False
    if token in WEAK_TOPIC_NAME_WORDS and token not in IMPORTANT_SHORT_TOKENS:
        return False
    if len(token) < 4 and token not in IMPORTANT_SHORT_TOKENS:
        return False
    return True


def _build_topic_name(keywords: list[str], topic_index: int) -> str:
    selected = []
    for keyword in keywords:
        keyword = keyword.strip().lower()
        if not keyword:
            continue
        parts = [p for p in keyword.split() if _is_good_topic_name_token(p)]
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
        return f"Тема {topic_index}"

    return " / ".join(selected[:3])


# ─────────────────────────────────────────────
#  Основная функция построения тем
# ─────────────────────────────────────────────

def build_topics(
    texts: list[str],
    n_topics: int = 5,
    n_top_words: int = 7,
) -> tuple[list[dict], list[tuple[int, float]]]:
    """
    Строит тематическую модель LDA на корпусе текстов.

    Параметры
    ---------
    texts       : список предобработанных текстов (text_clean из БД)
    n_topics    : желаемое количество тем (адаптируется под размер корпуса)
    n_top_words : количество ключевых слов на тему

    Возвращает
    ----------
    topics      : список словарей {"name": str, "keywords": str}
    assignments : список (topic_index, probability) для каждого документа
    """
    filtered_texts = [t for t in texts if t and t.strip()]
    if len(filtered_texts) < 3:
        return [], []

    # Адаптивный min_df: при маленьком корпусе снижаем порог
    if len(filtered_texts) >= 50:
        min_df = 3
    elif len(filtered_texts) >= 10:
        min_df = 2
    else:
        min_df = 1

    vectorizer = CountVectorizer(
        # ИСПРАВЛЕНО: поддержка кириллицы + латиницы
        token_pattern=r"(?u)\b[a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ\-]{2,}\b",
        stop_words=list(ALL_STOPWORDS),
        max_df=0.82,
        min_df=min_df,
        ngram_range=(1, 2),
    )

    dtm = vectorizer.fit_transform(filtered_texts)

    if dtm.shape[1] == 0:
        return [], []

    # Адаптивное количество тем: не больше документов и не больше словаря
    n_topics = min(n_topics, max(1, min(dtm.shape[0] // 3, dtm.shape[1], n_topics)))

    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        learning_method="batch",
        max_iter=30,
        doc_topic_prior=0.1,   # разреженное распределение тем по документам
        topic_word_prior=0.01, # разреженное распределение слов по темам
    )
    lda.fit(dtm)

    feature_names = vectorizer.get_feature_names_out()
    topics = []

    for topic_idx, topic_weights in enumerate(lda.components_, start=1):
        sorted_indices = topic_weights.argsort()[::-1]
        keywords = []
        seen: set[str] = set()

        for term_idx in sorted_indices:
            term = feature_names[term_idx].strip().lower()
            if not term or term in seen:
                continue
            # Пропускаем чисто стоп-словные биграммы
            if all(part in ALL_STOPWORDS for part in term.split()):
                continue
            keywords.append(term)
            seen.add(term)
            if len(keywords) >= n_top_words:
                break

        topic_name = _build_topic_name(keywords, topic_idx)
        topics.append({"name": topic_name, "keywords": ", ".join(keywords)})

    doc_topic_matrix = lda.transform(dtm)
    assignments = [
        (int(row.argmax()), float(row.max()))
        for row in doc_topic_matrix
    ]

    return topics, assignments