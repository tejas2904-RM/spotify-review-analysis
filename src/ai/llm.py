"""LLM client — multi-provider with automatic priority selection.

Provider priority (first key found wins):
  1. OPENAI_API_KEY  → GPT-4o-mini        (recommended: fast, cheap, reliable)
  2. GEMINI_API_KEY  → Gemini 2.0 Flash   (free tier, high TPM)
  3. GROQ_API_KEY    → Llama 3.3 70B      (free tier, low TPM)

Public API:
  call(system, user)  — structured JSON call with caching + rate limiting
  load_cache()        — load response cache from disk
  save_cache()        — persist response cache to disk
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

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL   = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

def _provider() -> str:
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    if os.getenv("GEMINI_API_KEY", "").strip():
        return "gemini"
    if os.getenv("GROQ_API_KEY", "").strip():
        return "groq"
    raise EnvironmentError(
        "No LLM API key found. Set OPENAI_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY in .env"
    )

# RPM limits per provider
_RPM = {"openai": 400, "gemini": 14, "groq": 10}

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_DEFAULT_CACHE = Path(os.getenv("DATA_DIR", "data")) / "enriched" / "llm_cache.json"
CACHE_FILE     = Path(os.getenv("LLM_CACHE_FILE", str(_DEFAULT_CACHE)))

_cache: dict[str, dict]        = {}
_call_timestamps: deque[float] = deque()

# Lazy-initialised clients
_openai_client = None
_gemini_client = None
_groq_client   = None


def load_cache() -> None:
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
    rpm = _RPM.get(_provider(), 10)
    now = time.monotonic()
    while _call_timestamps and now - _call_timestamps[0] > 60:
        _call_timestamps.popleft()
    if len(_call_timestamps) >= rpm:
        wait = 61.0 - (now - _call_timestamps[0])
        if wait > 0:
            logger.info("Rate limit reached — sleeping %.1f s …", wait)
            time.sleep(wait)


# ---------------------------------------------------------------------------
# Provider clients
# ---------------------------------------------------------------------------

def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY", "").strip()
        _openai_client = OpenAI(api_key=key)
        logger.info("LLM provider: OpenAI / %s", OPENAI_MODEL)
    return _openai_client


def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        key = os.getenv("GEMINI_API_KEY", "").strip()
        _gemini_client = genai.Client(api_key=key)
        logger.info("LLM provider: Google / %s", GEMINI_MODEL)
    return _gemini_client


def _get_groq():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        key = os.getenv("GROQ_API_KEY", "").strip()
        _groq_client = Groq(api_key=key)
        logger.info("LLM provider: Groq / %s", GROQ_MODEL)
    return _groq_client


# ---------------------------------------------------------------------------
# Provider call implementations
# ---------------------------------------------------------------------------

def _call_openai(system: str, user: str, max_tokens: int, temperature: float) -> dict:
    client = _get_openai()
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content or "{}")


def _call_gemini(system: str, user: str, max_tokens: int, temperature: float) -> dict:
    from google.genai import types
    client = _get_gemini()
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{system}\n\n{user}",
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        ),
    )
    return json.loads(resp.text)


def _call_groq(system: str, user: str, max_tokens: int, temperature: float) -> dict:
    client = _get_groq()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content or "{}")


_IMPLS = {
    "openai": _call_openai,
    "gemini": _call_gemini,
    "groq":   _call_groq,
}


# ---------------------------------------------------------------------------
# Public call
# ---------------------------------------------------------------------------

def call(
    system: str,
    user: str,
    max_tokens: int = 1500,
    temperature: float = 0.0,
    retries: int = 4,
) -> dict:
    """Make a single LLM call returning parsed JSON.

    Provider is auto-selected based on available API keys.
    Results are cached so re-runs skip already-processed inputs.
    """
    key = _cache_key(system, user)
    if key in _cache:
        return _cache[key]

    provider = _provider()
    impl     = _IMPLS[provider]

    for attempt in range(retries):
        _throttle()
        try:
            result = impl(system, user, max_tokens, temperature)
            _call_timestamps.append(time.monotonic())
            _cache[key] = result
            return result

        except Exception as exc:
            exc_str = str(exc)
            is_rate_limit = (
                "429"               in exc_str
                or "rate_limit"     in type(exc).__name__.lower()
                or "resource_exhausted" in exc_str.lower()
                or "quota"          in exc_str.lower()
                or "RateLimitError" in type(exc).__name__
            )
            if is_rate_limit:
                wait = 65
                logger.warning(
                    "Rate limited (attempt %d/%d). Cooling down %d s …",
                    attempt + 1, retries, wait,
                )
                time.sleep(wait)
            elif attempt < retries - 1:
                wait = 5 * (2 ** attempt)
                logger.warning(
                    "%s on attempt %d: %s. Retrying in %d s …",
                    type(exc).__name__, attempt + 1, exc, wait,
                )
                time.sleep(wait)
            else:
                raise RuntimeError(
                    f"LLM call failed after {retries} attempts: {exc}"
                ) from exc

    raise RuntimeError("LLM call failed — exhausted all retries.")
