"""Spotify Community discussion scraper.

Uses Playwright (headless Chromium) to render JavaScript-heavy community
pages and BeautifulSoup to parse posts and replies.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from datetime import datetime

from bs4 import BeautifulSoup

from src.ingestion.models import RawReview
from src.ingestion.utils import retry

logger = logging.getLogger(__name__)

SOURCE = "spotify_community"
PAGE_LOAD_TIMEOUT = 30_000  # ms
SCROLL_PAUSE = 1.5  # seconds


def _make_id(url: str, text: str) -> str:
    raw = f"{url}:{text[:128]}"
    return hashlib.sha1(raw.encode()).hexdigest()[:20]


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    patterns = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in patterns:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _extract_posts(html: str, page_url: str) -> list[RawReview]:
    """Parse post/reply nodes from a rendered Spotify Community (Khoros) page."""
    soup = BeautifulSoup(html, "lxml")
    reviews: list[RawReview] = []

    # Each post body on the Khoros platform
    body_nodes = soup.select("div.lia-message-body-content")
    if not body_nodes:
        # Fallback: try broader selectors
        body_nodes = soup.select("div[class*='MessageBody'], div[class*='message-body']")

    for body in body_nodes:
        text = body.get_text(separator=" ", strip=True)
        if not text or len(text) < 10:
            continue

        # Walk up to find the message container that holds author + timestamp
        container = body
        for _ in range(6):
            parent = container.parent
            if parent is None:
                break
            # Khoros message wrapper class patterns
            cls = " ".join(parent.get("class", []))
            if any(k in cls for k in ("lia-message", "MessageView", "lia-quilt")):
                container = parent
                break
            container = parent

        # Author
        author: str | None = None
        for sel in ("a.lia-user-name-link", "span.UserName", "a[href*='/users/']", ".author-name"):
            node = container.select_one(sel)
            if node:
                author = node.get_text(strip=True)
                break

        # Timestamp
        created_at: datetime | None = None
        for sel in ("span.local-date", "time[datetime]", "abbr.published", "span[class*='date']"):
            node = container.select_one(sel)
            if node:
                dt_str = node.get("datetime") or node.get("title") or node.get_text(strip=True)
                created_at = _parse_datetime(dt_str)
                if created_at:
                    break

        # Kudos / likes
        kudos: int | None = None
        for sel in ("span.kudos-count", "span[data-kudos-count]", "span[class*='kudos']", "button[class*='kudos']"):
            node = container.select_one(sel)
            if node:
                try:
                    kudos = int(re.sub(r"[^\d]", "", node.get_text()))
                except ValueError:
                    pass
                break

        reviews.append(
            RawReview(
                external_id=_make_id(page_url, text),
                source=SOURCE,
                text=text,
                source_url=page_url,
                author=author,
                rating=None,
                likes=kudos,
                created_at=created_at,
                metadata={"thread_url": page_url},
            )
        )

    return reviews


def _playwright_available() -> bool:
    """Check whether Playwright and its Chromium browser are installed."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False


@retry(max_attempts=3, base_delay=3.0, exceptions=(Exception,))
def _scrape_with_playwright(url: str) -> str:
    """Render the page with Playwright (anti-detection config) and return HTML."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page.goto(url, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
        time.sleep(SCROLL_PAUSE)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(SCROLL_PAUSE)
        html = page.content()
        browser.close()
    return html


@retry(max_attempts=3, base_delay=3.0, exceptions=(Exception,))
def _scrape_with_requests(url: str) -> str:
    """Fallback: fetch page with plain requests (no JS rendering)."""
    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def _scrape_url(url: str) -> str:
    """Render page — use Playwright if available, fall back to requests."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return _scrape_with_playwright(url)
    except Exception:
        logger.warning("Playwright unavailable; falling back to requests for %s", url)
        return _scrape_with_requests(url)


def fetch(config: dict) -> list[RawReview]:
    """Scrape Spotify Community threads as per config dict.

    Expected config keys:
        urls (list[str]): community thread URLs
    """
    urls: list[str] = config.get("urls", [])
    if not urls:
        logger.warning("No Spotify Community URLs configured. Skipping.")
        return []

    all_reviews: list[RawReview] = []

    for url in urls:
        logger.info("Scraping Spotify Community thread: %s", url)
        try:
            html = _scrape_url(url)
            posts = _extract_posts(html, url)
            logger.info("  → %d posts extracted", len(posts))
            all_reviews.extend(posts)
        except Exception as exc:
            logger.error("Failed to scrape %s: %s", url, exc)

    logger.info("Collected %d Spotify Community posts total", len(all_reviews))
    return all_reviews
