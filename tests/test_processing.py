"""Unit tests for Phase 2 processing components."""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# text.py
# ---------------------------------------------------------------------------

class TestStripHtml:
    def test_removes_tags(self):
        from src.processing.text import strip_html
        result = strip_html("<b>Hello</b> <em>World</em>")
        assert "Hello" in result and "World" in result
        assert "<b>" not in result and "<em>" not in result

    def test_decodes_entities(self):
        from src.processing.text import strip_html
        assert "&amp;" not in strip_html("Rock &amp; Roll")
        assert "&" in strip_html("Rock &amp; Roll")

    def test_no_html_unchanged(self):
        from src.processing.text import strip_html
        assert strip_html("Plain text") == "Plain text"


class TestStripUrls:
    def test_removes_http(self):
        from src.processing.text import strip_urls
        result = strip_urls("Check https://spotify.com for details")
        assert "spotify.com" not in result

    def test_removes_www(self):
        from src.processing.text import strip_urls
        result = strip_urls("visit www.example.com please")
        assert "example.com" not in result

    def test_no_url_unchanged(self):
        from src.processing.text import strip_urls
        assert strip_urls("No links here") == "No links here"


class TestRedactPII:
    def test_redacts_email(self):
        from src.processing.text import redact_pii
        result = redact_pii("Contact me at user@example.com please")
        assert "user@example.com" not in result
        assert "[EMAIL]" in result

    def test_no_pii_unchanged(self):
        from src.processing.text import redact_pii
        assert "Spotify" in redact_pii("I love Spotify")


class TestNormalizeWhitespace:
    def test_collapses_spaces(self):
        from src.processing.text import normalize_whitespace
        assert normalize_whitespace("too   many   spaces") == "too many spaces"

    def test_strips_leading_trailing(self):
        from src.processing.text import normalize_whitespace
        assert normalize_whitespace("  hello  ") == "hello"


class TestCompressRepeatedChars:
    def test_collapses_long_run(self):
        from src.processing.text import compress_repeated_chars
        # "ssssssssss" (10 chars) → "sss" (3 chars); "works" keeps its 's'
        result = compress_repeated_chars("Yesssssssss it works")
        # Confirm the long run is compressed (original had 10 s's, now max 3 in one run)
        assert "ssss" not in result

    def test_leaves_short_run(self):
        from src.processing.text import compress_repeated_chars
        assert compress_repeated_chars("good") == "good"


class TestCleanText:
    def test_full_pipeline(self):
        from src.processing.text import clean_text
        dirty = "  <b>Love</b> this app!!! Visit https://x.com &amp; follow us!   "
        result = clean_text(dirty)
        assert "<b>" not in result
        assert "x.com" not in result
        assert "&amp;" not in result
        assert result == result.strip()

    def test_preserves_emojis(self):
        from src.processing.text import clean_text
        result = clean_text("Great app 🎵🎶")
        assert "🎵" in result
        assert "🎶" in result


class TestCountTokens:
    def test_basic(self):
        from src.processing.text import count_tokens
        assert count_tokens("hello world") == 2

    def test_empty(self):
        from src.processing.text import count_tokens
        assert count_tokens("") == 0

    def test_single_word(self):
        from src.processing.text import count_tokens
        assert count_tokens("Spotify") == 1


# ---------------------------------------------------------------------------
# filters.py
# ---------------------------------------------------------------------------

class TestIsSpam:
    def test_too_short(self):
        from src.processing.filters import is_spam
        spam, reason = is_spam("ok")
        assert spam is True
        assert "too_short" in reason

    def test_normal_review_not_spam(self):
        from src.processing.filters import is_spam
        text = "Spotify's Discover Weekly has become repetitive and no longer surfaces new artists."
        spam, _ = is_spam(text)
        assert spam is False

    def test_boilerplate(self):
        from src.processing.filters import is_spam
        spam, reason = is_spam("lol")
        assert spam is True

    def test_promo_content(self):
        from src.processing.filters import is_spam
        spam, reason = is_spam("Click here to get a discount promo code for premium!")
        assert spam is True
        assert "promotional" in reason

    def test_all_caps_long(self):
        from src.processing.filters import is_spam
        spam, reason = is_spam("THIS APP IS ABSOLUTELY TERRIBLE AND BROKEN COMPLETELY")
        assert spam is True
        assert "all_caps" in reason

    def test_repetitive_words(self):
        from src.processing.filters import is_spam
        spam, reason = is_spam("bad bad bad bad bad bad bad bad music")
        assert spam is True

    def test_emoji_only_short(self):
        from src.processing.filters import is_spam
        spam, _ = is_spam("👍👍👍")
        assert spam is True  # low alpha ratio + too short


# ---------------------------------------------------------------------------
# dedup.py
# ---------------------------------------------------------------------------

class TestMakeHash:
    def test_same_text_same_hash(self):
        from src.processing.dedup import make_hash
        assert make_hash("hello world") == make_hash("hello world")

    def test_case_insensitive(self):
        from src.processing.dedup import make_hash
        assert make_hash("Spotify") == make_hash("spotify")

    def test_whitespace_normalised(self):
        from src.processing.dedup import make_hash
        assert make_hash("hello  world") == make_hash("hello world")

    def test_different_texts_different_hash(self):
        from src.processing.dedup import make_hash
        assert make_hash("apple") != make_hash("orange")


class TestDeduplicate:
    def test_exact_duplicate_removed(self):
        from src.processing.dedup import deduplicate
        texts = ["Spotify is great", "Spotify is great", "Different review here"]
        result = deduplicate(texts)
        assert len(result.kept) == 2
        assert len(result.dropped_exact) == 1

    def test_near_duplicate_removed(self):
        from src.processing.dedup import deduplicate
        texts = [
            "Spotify recommendations are getting worse every week",
            "Spotify recommendations getting worse every week",   # near-dup
            "Hacker News thread about music discovery",
        ]
        result = deduplicate(texts, threshold=85)
        assert len(result.dropped_near) >= 1

    def test_unique_texts_all_kept(self):
        from src.processing.dedup import deduplicate
        texts = [
            "Great music discovery features",
            "Terrible battery drain on Android",
            "Discover Weekly stopped working for me",
        ]
        result = deduplicate(texts)
        assert len(result.kept) == 3

    def test_empty_input(self):
        from src.processing.dedup import deduplicate
        result = deduplicate([])
        assert result.kept == []
        assert result.dropped_exact == []
        assert result.dropped_near == []
