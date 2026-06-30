"""Shared utilities for all ingestion collectors."""

from __future__ import annotations

import logging
import os
import time
from functools import wraps
from typing import Callable, TypeVar

import yaml

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


def retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator: retry on exception with exponential back-off."""

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            fn.__name__,
                            max_attempts,
                            exc,
                        )
                        raise
                    logger.warning(
                        "%s attempt %d/%d failed (%s). Retrying in %.1fs…",
                        fn.__name__,
                        attempt,
                        max_attempts,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    delay *= backoff

        return wrapper  # type: ignore[return-value]

    return decorator


def load_sources_config(path: str | None = None) -> dict:
    """Load config/sources.yaml relative to the project root."""
    if path is None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "config", "sources.yaml")
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def setup_logging(level: str | None = None) -> None:
    level = level or os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
