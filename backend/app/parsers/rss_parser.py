from __future__ import annotations

import email.utils
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup


def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except Exception:
        return None


def extract_text_from_url(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # убираем мусорные теги
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
        return text.strip()
    except Exception:
        return ""


def parse_rss_feed(feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    items: list[dict] = []

    for entry in feed.entries:
        url = entry.get("link", "") or ""
        title = entry.get("title", "Untitled") or "Untitled"
        published_at = parse_date(entry.get("published"))
        author = entry.get("author")

        text_raw = ""
        if url:
            text_raw = extract_text_from_url(url)

        if not text_raw:
            summary = entry.get("summary", "") or ""
            text_raw = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)

        items.append(
            {
                "title": title,
                "url": url,
                "published_at": published_at,
                "text_raw": text_raw,
                "author": author,
            }
        )

    return items


class RSSParser:
    def parse_feed(self, feed_url: str) -> list[dict]:
        return parse_rss_feed(feed_url)