"""
sources_config.py
=================
Реестр одобренных RSS-источников для системы анализа общественных трендов.

Фокус: Казахстан + Центральная Азия + глобальные новости (EN).
Российские источники исключены намеренно — они смещают тематическое
моделирование в сторону российской повестки и вытесняют казахстанский контент.

Категории
---------
KAZAKHSTAN   — ведущие казахстанские новостные и деловые издания
CENTRAL_ASIA — региональная повестка Центральной Азии
GLOBAL_EN    — международные англоязычные источники
SOCIAL       — Reddit и другие площадки прямого общественного дискурса
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceEntry:
    url: str
    name: str
    category: str
    language: str
    description: str


# ─────────────────────────────────────────────
#  Казахстан
# ─────────────────────────────────────────────
KAZAKHSTAN: list[SourceEntry] = [
    SourceEntry(
        url="https://tengrinews.kz/news.rss",
        name="Tengrinews",
        category="KAZAKHSTAN",
        language="ru",
        description="Главный новостной портал Казахстана",
    ),
    SourceEntry(
        url="https://www.inform.kz/rss/rus.xml",
        name="Казинформ",
        category="KAZAKHSTAN",
        language="ru",
        description="Государственное информационное агентство Казахстана",
    ),
    SourceEntry(
        url="https://kapital.kz/rss/all/",
        name="Капитал",
        category="KAZAKHSTAN",
        language="ru",
        description="Деловое издание — экономика и бизнес Казахстана",
    ),
    SourceEntry(
        url="https://kursiv.kz/feed/",
        name="Курсив",
        category="KAZAKHSTAN",
        language="ru",
        description="Финансы, рынки, инвестиции Казахстана",
    ),
    SourceEntry(
        url="https://rss.app/feeds/rYZkYLRR8Gieemta.xml",
        name="Forbes Kazakhstan",
        category="KAZAKHSTAN",
        language="ru",
        description="Forbes KZ — бизнес, рейтинги, предпринимательство",
    ),
]

# ─────────────────────────────────────────────
#  Центральная Азия
# ─────────────────────────────────────────────
CENTRAL_ASIA: list[SourceEntry] = [
    SourceEntry(
        url="https://cabar.asia/feed/",
        name="CABAR.asia",
        category="CENTRAL_ASIA",
        language="ru",
        description="Аналитика и новости Центральной Азии",
    ),
    SourceEntry(
        url="https://rus.azattyq.org/api/epiqqlinkn_1",
        name="Азаттык (RFE/RL Казахстан)",
        category="CENTRAL_ASIA",
        language="ru",
        description="Радио Свобода — независимые новости Казахстана",
    ),
]

# ─────────────────────────────────────────────
#  Глобальные англоязычные источники
# ─────────────────────────────────────────────
GLOBAL_EN: list[SourceEntry] = [
    SourceEntry(
        url="https://feeds.bbci.co.uk/news/world/rss.xml",
        name="BBC World News",
        category="GLOBAL_EN",
        language="en",
        description="Международные новости BBC",
    ),
    SourceEntry(
        url="https://ir.thomsonreuters.com/rss/news-releases.xml?items=15",
        name="Thomson Reuters",
        category="GLOBAL_EN",
        language="en",
        description="Пресс-релизы Reuters",
    ),
    SourceEntry(
        url="https://nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/topic/destination/kazakhstan/rss.xml",
        name="NYT — Kazakhstan",
        category="GLOBAL_EN",
        language="en",
        description="New York Times — материалы о Казахстане",
    ),
    SourceEntry(
        url="https://feeds.bbci.co.uk/news/business/rss.xml",
        name="BBC Business",
        category="GLOBAL_EN",
        language="en",
        description="BBC — международная экономика и бизнес",
    ),
]

# ─────────────────────────────────────────────
#  Социальные источники — Reddit
#  (прямой общественный дискурс, не редакционный)
# ─────────────────────────────────────────────
SOCIAL: list[SourceEntry] = [
    SourceEntry(
        url="https://www.reddit.com/r/Kazakhstan/.rss",
        name="Reddit r/Kazakhstan",
        category="SOCIAL",
        language="en",
        description="Сообщество Reddit — обсуждения о Казахстане",
    ),
    SourceEntry(
        url="https://www.reddit.com/r/worldnews/search.rss?q=kazakhstan&sort=new",
        name="Reddit r/worldnews — Kazakhstan",
        category="SOCIAL",
        language="en",
        description="Reddit worldnews — упоминания Казахстана",
    ),
    SourceEntry(
        url="https://www.reddit.com/r/eurasia/.rss",
        name="Reddit r/eurasia",
        category="SOCIAL",
        language="en",
        description="Reddit — Евразийский регион",
    ),
    SourceEntry(
        url="https://www.reddit.com/r/Economics/search.rss?q=kazakhstan&sort=new",
        name="Reddit r/Economics — Kazakhstan",
        category="SOCIAL",
        language="en",
        description="Reddit — экономические дискуссии о Казахстане",
    ),
]

# ─────────────────────────────────────────────
#  Полный реестр и вспомогательные функции
# ─────────────────────────────────────────────
ALL_SOURCES: list[SourceEntry] = KAZAKHSTAN + CENTRAL_ASIA + GLOBAL_EN + SOCIAL

# Домены, которые считаются российскими и подлежат удалению из БД
RUSSIAN_DOMAINS: set[str] = {
    "lenta.ru",
    "rbc.ru",
    "rssexport.rbc.ru",
    "ria.ru",
    "tass.ru",
    "kommersant.ru",
    "vedomosti.ru",
    "iz.ru",
    "interfax.ru",
    "regnum.ru",
}


def get_approved_urls() -> list[str]:
    """Возвращает список URL всех одобренных источников."""
    return [s.url for s in ALL_SOURCES]


def is_russian_source(url: str) -> bool:
    """Проверяет, является ли URL российским источником."""
    url_lower = (url or "").lower()
    return any(domain in url_lower for domain in RUSSIAN_DOMAINS)


def get_by_category(category: str) -> list[SourceEntry]:
    """Возвращает источники по категории."""
    return [s for s in ALL_SOURCES if s.category == category]