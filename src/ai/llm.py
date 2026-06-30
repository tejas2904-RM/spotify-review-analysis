"""Groq LLM client — Llama 3.3 70B Versatile.

Provides:
  call(system, user)    — single structured JSON call with caching + rate limiting
  load_cache()          — load response cache from disk
  save_cache()          — persist response cache to disk
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"
RPM_LIMIT = 10          # conservative — stay well within Groq free-tier TPM budget
_DEFAULT_CACHE = Path(os.getenv("DATA_DIR", "data")) / "enriched" / "llm_cache.json"
CACHE_FILE = Path(os.getenv("LLM_CACHE_FILE", str(_DEFAULT_CACHE)))

_client = None
_cache: dict[str, dict] = {}
_call_timestamps: deque[float] = deque()   # tracks timestamps of recent calls


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        _client = Groq(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def load_cache() -> None:
    """Load cached LLM responses from disk into memory."""
    global _cache
    if CACHE_FILE.exists():
        try:
            _cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            logger.info("LLM cache loaded: %d entries.", len(_cache))
        except Exception as exc:
            logger.warning("Could not load LLM cache: %s. Starting fresh.", exc)
            _cache = {}
    else:
        _cache = {}


def save_cache() -> None:
    """Persist in-memory cache to disk."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")
    logger.debug("LLM cache saved: %d entries.", len(_cache))


def _cache_key(system: str, user: str) -> str:
    payload = f"{system[:120]}||{user}"
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def _throttle() -> None:
    """Block until we are under the RPM cap."""
    now = time.monotonic()
    # Drop timestamps older than 60 s
    while _call_timestamps and now - _call_timestamps[0] > 60:
        _call_timestamps.popleft()
    if len(_call_timestamps) >= RPM_LIMIT:
        wait = 61.0 - (now - _call_timestamps[0])
        if wait > 0:
            logger.info("Rate limit reached — sleeping %.1f s …", wait)
            time.sleep(wait)


# ---------------------------------------------------------------------------
# Core call
# ---------------------------------------------------------------------------

def call(
    system: str,
    user: str,
    max_tokens: int = 1500,
    temperature: float = 0.0,
    retries: int = 4,
) -> dict:
    """Make a single Groq LLM call returning parsed JSON.

    Results are cached by (system_prefix, user_prompt) hash so re-runs
    skip already-processed inputs without hitting the API again.

    Args:
        system:     System prompt string.
        user:       User prompt string.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature (0 = deterministic).
        retries:    Number of retry attempts on transient errors.

    Returns:
        Parsed JSON dict from the model response.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    key = _cache_key(system, user)
    if key in _cache:
        return _cache[key]

    client = _get_client()

    for attempt in range(retries):
        _throttle()
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            _call_timestamps.append(time.monotonic())
            content = resp.choices[0].message.content or "{}"
            result = json.loads(content)
            _cache[key] = result
            return result

        except Exception as exc:
            exc_type = type(exc).__name__
            if "rate_limit" in exc_type.lower() or "429" in str(exc):
                # Fixed 65 s cooldown on every 429 — lets the TPM window reset
                wait = 65
                logger.warning("Rate limited (attempt %d/%d). Cooling down %d s …", attempt + 1, retries, wait)
                time.sleep(wait)
            elif attempt < retries - 1:
                wait = 5 * (2 ** attempt)
                logger.warning("%s on attempt %d: %s. Retrying in %d s …", exc_type, attempt + 1, exc, wait)
                time.sleep(wait)
            else:
                raise RuntimeError(f"LLM call failed after {retries} attempts: {exc}") from exc

    raise RuntimeError("LLM call failed — exhausted all retries.")
