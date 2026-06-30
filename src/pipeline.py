"""CLI orchestration entrypoint.

Usage:
    python -m src.pipeline ingest
    python -m src.pipeline clean
    python -m src.pipeline enrich
    python -m src.pipeline aggregate
    python -m src.pipeline all
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from src.ingestion.utils import load_sources_config, setup_logging


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase runners
# ---------------------------------------------------------------------------

def run_ingest() -> None:
    """Phase 1 — collect raw reviews from all configured sources."""
    from src.ingestion import google_play, hacker_news, spotify_community, youtube
    from src.storage.db import upsert_raw_reviews

    config = load_sources_config()
    total = 0

    collectors = [
        ("Google Play", google_play, config.get("google_play", {})),
        ("YouTube", youtube, config.get("youtube", {})),
        ("Spotify Community", spotify_community, config.get("spotify_community", {})),
        ("Hacker News", hacker_news, config.get("hacker_news", {})),
    ]

    for name, module, cfg in collectors:
        logger.info("=== Ingesting: %s ===", name)
        try:
            reviews = module.fetch(cfg)
            rows = [r.to_dict() for r in reviews]
            inserted = upsert_raw_reviews(rows)
            logger.info("%s: %d fetched / %d newly inserted", name, len(reviews), inserted)
            total += inserted
        except Exception as exc:
            logger.error("%s ingestion failed: %s", name, exc, exc_info=True)

    logger.info("=== Ingestion complete. Total new records: %d ===", total)


def run_clean() -> None:
    """Phase 2 — clean and normalise raw reviews."""
    from src.processing.clean import print_stats, run_cleaning

    logger.info("=== Phase 2: Cleaning & Normalisation ===")
    stats = run_cleaning()
    print_stats(stats)


def run_store() -> None:
    """Phase 3 — export Parquet snapshots and build ChromaDB vector index."""
    from src.storage.parquet import export_all
    from src.storage.repository import get_relevant_clean
    from src.storage.vector import collection_stats, embed_and_store

    logger.info("=== Phase 3: Storage — Parquet export ===")
    paths = export_all()
    for name, path in paths.items():
        logger.info("  %s → %s", name, path)

    logger.info("=== Phase 3: Storage — Vector embedding ===")
    reviews = get_relevant_clean()
    logger.info("Embedding %d relevant clean reviews…", len(reviews))
    count = embed_and_store(reviews)
    stats = collection_stats()
    logger.info(
        "ChromaDB collection '%s': %d embeddings stored at %s",
        stats["collection"], stats["total_embeddings"], stats["chroma_dir"],
    )


def run_enrich() -> None:
    """Phase 4a — per-review AI enrichment via Groq Llama 3.3 70B."""
    from src.ai.enrich import run_enrichment

    logger.info("=== Phase 4a: Per-Review Enrichment (Groq Llama 3.3 70B) ===")
    total = run_enrichment()
    logger.info("Enrichment done. %d reviews enriched.", total)


def run_cluster() -> None:
    """Phase 4b — HDBSCAN embedding clustering + LLM cluster labeling."""
    from src.ai.cluster import run_clustering

    logger.info("=== Phase 4b: Theme Clustering (HDBSCAN + LLM) ===")
    clusters = run_clustering()
    logger.info("Clustering done. %d clusters discovered.", len(clusters))
    for cid, info in clusters.items():
        logger.info("  [%s] %s — %d reviews", cid, info.get("label", "?"), info.get("size", 0))


def run_summarize() -> None:
    """Phase 4c — LLM summaries per theme and per source."""
    from src.ai.summarize import run_summarization

    logger.info("=== Phase 4c: Theme & Source Summarization (Groq Llama 3.3 70B) ===")
    count = run_summarization()
    logger.info("Summarization done. %d summaries saved.", count)


def run_aggregate() -> None:
    """Phase 5 — insight aggregation."""
    from src.insights.aggregate import print_summary, run_aggregation

    logger.info("=== Phase 5: Insights & Aggregation ===")
    summary = run_aggregation()
    print_summary(summary)


def run_all() -> None:
    """Run the full pipeline end-to-end."""
    run_ingest()
    run_clean()
    run_enrich()
    run_aggregate()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_relevance() -> None:
    """Phase 2 extended — tag relevant reviews per source."""
    from src.processing.relevance import tag_relevant_reviews

    logger.info("=== Phase 2b: Relevance Tagging ===")

    source_configs = [
        ("google_play",       1000, 0.5),
        ("youtube",           1000, 3.0),
        ("hacker_news",       1000, 0.5),  # all HN kept — already on-topic
        ("spotify_community", 1000, 0.5),  # all community kept — already on-topic
    ]

    for source, top_n, min_score in source_configs:
        logger.info("--- Tagging: %s (threshold=%.1f, top_n=%d) ---", source, min_score, top_n)
        stats = tag_relevant_reviews(source=source, top_n=top_n, min_score=min_score)
        logger.info(
            "  Checked=%d  Above threshold=%d  Tagged=%d",
            stats["total_checked"], stats["above_threshold"], stats["tagged_relevant"],
        )


COMMANDS = {
    "ingest": run_ingest,
    "clean": run_clean,
    "relevance": run_relevance,
    "store": run_store,
    "enrich": run_enrich,
    "cluster": run_cluster,
    "summarize": run_summarize,
    "aggregate": run_aggregate,
    "all": run_all,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m src.pipeline",
        description="Spotify Review Discovery Engine — pipeline CLI",
    )
    parser.add_argument(
        "command",
        choices=["ingest", "clean", "relevance", "store", "enrich", "cluster", "summarize", "aggregate", "all"],
        help="Pipeline phase to run.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )

    args = parser.parse_args(argv)
    setup_logging(args.log_level)

    logger.info("Running pipeline command: %s", args.command)
    try:
        COMMANDS[args.command]()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        return 1
    except Exception as exc:
        logger.exception("Pipeline command '%s' failed: %s", args.command, exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
