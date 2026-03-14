from __future__ import annotations

import email.utils
from dataclasses import dataclass
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup


@dataclass
class ParsedArticle:
    title: str
    url: str
    published_at: datetime | None
    text_raw: str
    author: str | None


class RSSParser:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {"User-Agent": "TrendAnalysisSystem/1.0"}

    def parse_date(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return email.utils.parsedate_to_datetime(value)
        except Exception:
            return None

    def extract_text_from_url(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=self.timeout, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
            return text.strip()
        except Exception:
            return ""

    def parse(self, feed_url: str) -> list[ParsedArticle]:
        feed = feedparser.parse(feed_url)
        parsed: list[ParsedArticle] = []
        for entry in feed.entries:
            url = entry.get("link", "")
            title = entry.get("title", "Untitled")
            published_at = self.parse_date(entry.get("published"))
            text_raw = self.extract_text_from_url(url) if url else ""
            if not text_raw:
                summary = entry.get("summary", "")
                text_raw = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)
            parsed.append(
                ParsedArticle(
                    title=title,
                    url=url,
                    published_at=published_at,
                    text_raw=text_raw,
                    author=entry.get("author"),
                )
            )
        return parsed
