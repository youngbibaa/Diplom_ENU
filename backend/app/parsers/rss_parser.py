"""
rss_parser.py
=============
Универсальный RSS-парсер.

Поддерживает:
  - content:encoded (полный текст прямо в RSS — без HTTP-запроса)
  - rss.app прокси-фиды (Forbes KZ и др.)
  - Reddit RSS (.rss фиды сабреддитов)
  - site-specific CSS-селекторы для казахских и международных источников
  - graceful fallback: content:encoded → summary → HTTP к статье
"""

from __future__ import annotations

import email.utils
import logging
import re
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  CSS-селекторы для конкретных доменов
#  Российские источники (lenta.ru, rbc.ru) удалены намеренно.
# ─────────────────────────────────────────────────────────────────────────────

SITE_SELECTORS: dict[str, list[str]] = {
    # ── Казахстан ──────────────────────────────────────────────────────────
    "tengrinews.kz": [
        "div.read__content",
        "div.article__content",
        "div.content-inner",
        "article",
    ],
    "inform.kz": [
        "div.view-content",
        "div.field-items",
        "div.news-detail__content",
        "div.article-text",
        "article",
    ],
    "kapital.kz": [
        "div.article__body",
        "div.content-text",
        "div.single-content",
        "article",
    ],
    "forbes.kz": [
        "div.article__body",
        "div.entry-content",
        "div.post-content",
        "article",
    ],
    "kursiv.kz": [
        "div.article__content",
        "div.single-post__content",
        "div.entry-content",
        "article",
    ],
    # ── Центральная Азия ───────────────────────────────────────────────────
    "cabar.asia": [
        "div.entry-content",
        "div.post-content",
        "article",
    ],
    "azattyq.org": [
        "div.wsw",
        "div.article-content",
        "article",
    ],
    # ── Глобальные (EN) ────────────────────────────────────────────────────
    "bbc.co.uk": [
        "div[data-component='text-block']",
        "div.ssrcss-11r1m41-RichTextComponentWrapper",
        "article",
    ],
    "bbc.com": [
        "div[data-component='text-block']",
        "div.ssrcss-11r1m41-RichTextComponentWrapper",
        "article",
    ],
    "nytimes.com": [
        "section[name='articleBody']",
        "div.StoryBodyCompanionColumn",
        "article",
    ],
}

# Домены с жёсткой антибот-защитой — берём только RSS-контент, без HTTP
NO_FETCH_DOMAINS: set[str] = {
    "reuters.com",
    "thomsonreuters.com",
    "ir.thomsonreuters.com",
    "bloomberg.com",
    "ft.com",
    "wsj.com",
    # Reddit тоже не скрапим — используем RSS напрямую
    "reddit.com",
    "old.reddit.com",
}

# rss.app добавляет рекламный хвост в конец контента
_RSS_APP_NOISE = re.compile(
    r"(The post .+ appeared first on .+|Read more at .+|Continue reading.+)",
    re.IGNORECASE | re.DOTALL,
)

# Reddit-специфичный мусор в summary
_REDDIT_NOISE = re.compile(
    r"submitted by\s+/u/\S+|<!--.*?-->|\[link\]|\[comments\]",
    re.IGNORECASE | re.DOTALL,
)

MIN_TEXT_LENGTH = 80


# ─────────────────────────────────────────────────────────────────────────────
#  Вспомогательные функции
# ─────────────────────────────────────────────────────────────────────────────

def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except Exception:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None


def _get_domain(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1).lower() if m else ""


def _is_no_fetch(url: str) -> bool:
    domain = _get_domain(url)
    return any(blocked in domain for blocked in NO_FETCH_DOMAINS)


def _is_rss_app(feed_url: str) -> bool:
    return "rss.app" in feed_url


def _is_reddit(feed_url: str) -> bool:
    return "reddit.com" in feed_url


def _get_selectors(url: str) -> list[str]:
    domain = _get_domain(url)
    for key, selectors in SITE_SELECTORS.items():
        if key in domain:
            return selectors
    return []


def _clean_rss_app_noise(text: str) -> str:
    return _RSS_APP_NOISE.sub("", text).strip()


def _clean_reddit_text(text: str) -> str:
    """Убирает Reddit-специфичный мусор и HTML из summary."""
    text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    text = _REDDIT_NOISE.sub("", text).strip()
    return text


def _extract_from_html(soup: BeautifulSoup, url: str) -> str:
    """Извлекает основной текст из HTML через site-specific селекторы."""
    for tag in soup(["script", "style", "noscript", "nav",
                     "footer", "header", "aside", "figure"]):
        tag.decompose()

    for selector in _get_selectors(url):
        container = soup.select_one(selector)
        if container:
            text = container.get_text(" ", strip=True)
            if len(text) >= MIN_TEXT_LENGTH:
                return text

    # Общий fallback — параграфы длиннее 40 символов
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 40
    ]
    return " ".join(paragraphs).strip()


def _extract_rss_content(
    entry: object,
    is_rss_app: bool = False,
    is_reddit: bool = False,
) -> str:
    """
    Извлекает текст напрямую из RSS-записи.
    Порядок: content:encoded → summary/description.
    """
    # 1. content:encoded
    content_list = getattr(entry, "content", None)
    if content_list:
        for c in content_list:
            value = (
                c.get("value", "") if isinstance(c, dict)
                else getattr(c, "value", "")
            )
            if value and len(value) > MIN_TEXT_LENGTH:
                text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
                if is_rss_app:
                    text = _clean_rss_app_noise(text)
                if is_reddit:
                    text = _clean_reddit_text(text)
                if len(text) >= MIN_TEXT_LENGTH:
                    return text

    # 2. summary / description
    summary = getattr(entry, "summary", "") or ""
    if summary:
        if is_reddit:
            text = _clean_reddit_text(summary)
        else:
            text = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)
            if is_rss_app:
                text = _clean_rss_app_noise(text)
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    return ""


def extract_text_from_url(url: str) -> str:
    """Загружает страницу статьи и извлекает основной текст."""
    if _is_no_fetch(url):
        return ""

    try:
        r = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9,kk;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            },
            allow_redirects=True,
        )
        r.raise_for_status()
        if r.encoding and r.encoding.lower() in ("iso-8859-1", "latin-1"):
            r.encoding = "utf-8"
        return _extract_from_html(BeautifulSoup(r.text, "html.parser"), url)

    except requests.exceptions.Timeout:
        logger.warning("rss_parser: timeout %s", url)
        return ""
    except requests.exceptions.RequestException as e:
        logger.warning("rss_parser: fetch error %s — %s", url, e)
        return ""


# ─────────────────────────────────────────────────────────────────────────────
#  Основная функция
# ─────────────────────────────────────────────────────────────────────────────

def parse_rss_feed(feed_url: str) -> list[dict]:
    """
    Парсит RSS-ленту и возвращает список статей с текстом.

    Стратегия получения текста:
    1. Из RSS напрямую (content:encoded или summary) — быстро, без лишних запросов
    2. Если текст слишком короткий — загружаем страницу статьи (кроме NO_FETCH_DOMAINS)
    """
    logger.info("rss_parser: fetching %s", feed_url)

    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        logger.error("rss_parser: feedparser failed %s — %s", feed_url, e)
        return []

    if not feed.entries:
        logger.warning(
            "rss_parser: no entries in %s (status=%s bozo=%s)",
            feed_url,
            getattr(feed, "status", "?"),
            getattr(feed, "bozo", False),
        )
        return []

    is_app    = _is_rss_app(feed_url)
    is_reddit = _is_reddit(feed_url)

    logger.info("rss_parser: %d entries from %s", len(feed.entries), feed_url)

    items: list[dict] = []

    for entry in feed.entries:
        url          = getattr(entry, "link", "") or ""
        title        = (getattr(entry, "title", "") or "").strip() or "Untitled"
        published_at = parse_date(getattr(entry, "published", None))
        author       = getattr(entry, "author", None)

        # Для Reddit author — это username вида "/u/username"
        if is_reddit and author:
            author = author.replace("/u/", "").strip() or None

        # Шаг 1: берём текст из RSS
        text_raw = _extract_rss_content(
            entry, is_rss_app=is_app, is_reddit=is_reddit
        )

        # Шаг 2: если мало — идём за полным текстом на сайт
        if len(text_raw) < MIN_TEXT_LENGTH and url:
            text_raw = extract_text_from_url(url)

        if not text_raw or title == "Untitled":
            logger.debug("rss_parser: skip (no content): %s", url)
            continue

        # Для Reddit добавляем заголовок в текст — он несёт смысловую нагрузку
        if is_reddit and title and title != "Untitled":
            text_raw = f"{title}. {text_raw}"

        items.append({
            "title":        title,
            "url":          url,
            "published_at": published_at,
            "text_raw":     text_raw,
            "author":       author,
        })

    logger.info("rss_parser: %d valid items from %s", len(items), feed_url)
    return items


class RSSParser:
    def parse_feed(self, feed_url: str) -> list[dict]:
        return parse_rss_feed(feed_url)