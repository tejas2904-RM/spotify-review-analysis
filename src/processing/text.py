"""Text cleaning utilities for Phase 2.

Covers HTML stripping, URL removal, whitespace normalisation,
PII redaction, and token counting.
Emojis are intentionally preserved — they carry sentiment signal.
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

_URL_RE = re.compile(
    r"https?://\S+|www\.\S+",
    re.IGNORECASE,
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_ENTITY_RE = re.compile(r"&(?:#\d+|[a-zA-Z]+);")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d[\d\s\-().]{7,}\d)\b")
_REPEATED_CHAR_RE = re.compile(r"(.)\1{4,}")  # 5+ consecutive same chars
_WHITESPACE_RE = re.compile(r"[ \t]+")
_NEWLINE_RE = re.compile(r"\n{3,}")


def strip_html(text: str) -> str:
    """Remove HTML tags and decode common HTML entities."""
    text = _HTML_TAG_RE.sub(" ", text)
    # Decode a handful of common entities manually (no heavy dep needed)
    entity_map = {
        "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&nbsp;": " ",
        "&apos;": "'",
    }
    for entity, char in entity_map.items():
        text = text.replace(entity, char)
    # Remaining numeric / named entities → strip
    text = _HTML_ENTITY_RE.sub("", text)
    return text


def strip_urls(text: str) -> str:
    """Remove URLs, replacing them with a single space."""
    return _URL_RE.sub(" ", text)


def redact_pii(text: str) -> str:
    """Replace emails and phone numbers with placeholder tokens."""
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    return text


def normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs and limit blank lines to one."""
    text = _WHITESPACE_RE.sub(" ", text)
    text = _NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def normalize_unicode(text: str) -> str:
    """NFC-normalize unicode; convert smart quotes etc. to ASCII equivalents."""
    text = unicodedata.normalize("NFC", text)
    replacements = {
        "\u2018": "'", "\u2019": "'",   # smart single quotes
        "\u201c": '"', "\u201d": '"',   # smart double quotes
        "\u2013": "-", "\u2014": "-",   # en/em dash
        "\u2026": "...",                # ellipsis
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def compress_repeated_chars(text: str) -> str:
    """Collapse 5+ consecutive identical chars to 3 (e.g. 'loooove' → 'loove')."""
    return _REPEATED_CHAR_RE.sub(r"\1\1\1", text)


def clean_text(text: str) -> str:
    """Full cleaning pipeline — returns cleaned text preserving emojis."""
    text = strip_html(text)
    text = strip_urls(text)
    text = redact_pii(text)
    text = normalize_unicode(text)
    text = compress_repeated_chars(text)
    text = normalize_whitespace(text)
    return text


def count_tokens(text: str) -> int:
    """Simple whitespace-based token count (no external model required)."""
    return len(text.split())
