"""Embedding-based theme clustering — Phase 4.

Uses the ChromaDB embeddings built in Phase 3 as input to HDBSCAN clustering,
then asks Groq Llama 3.3 70B to label each cluster.
Cluster results are persisted to the `insights` table as metric `theme_clusters`.
"""

from __future__ import annotations

import logging

import numpy as np

from src.ai.llm import call, load_cache, save_cache
from src.ai.prompts import CLUSTER_LABEL_SYSTEM, CLUSTER_LABEL_USER_TEMPLATE
from src.storage.repository import save_insight
from src.storage.vector import _get_collection

logger = logging.getLogger(__name__)


def _label_cluster(sample_texts: list[str]) -> dict:
    """Ask the LLM to label a cluster given sample review texts."""
    bullet_lines = "\n".join(f"- {t[:220]}" for t in sample_texts[:10])
    user_prompt = CLUSTER_LABEL_USER_TEMPLATE.format(reviews=bullet_lines)
    try:
        result = call(CLUSTER_LABEL_SYSTEM, user_prompt, max_tokens=200)
        return {
            "label": result.get("label", "Unknown Theme"),
            "description": result.get("description", ""),
        }
    except Exception as exc:
        logger.warning("Cluster labeling failed: %s", exc)
        return {"label": "Unknown Theme", "description": ""}


def run_clustering(
    min_cluster_size: int = 5,
    min_samples: int = 2,
) -> dict:
    """Cluster ChromaDB embeddings with HDBSCAN and label each cluster with the LLM.

    Args:
        min_cluster_size: HDBSCAN minimum cluster size.
        min_samples:      HDBSCAN minimum samples.

    Returns:
        Dict mapping cluster_id → {label, description, size, sources, review_ids}.
        Also saved to the `insights` table as metric `theme_clusters`.
    """
    try:
        import hdbscan
    except ImportError:
        logger.error("hdbscan not installed. Run: pip install hdbscan")
        return {}

    load_cache()

    collection = _get_collection()
    count = collection.count()
    if count == 0:
        logger.warning("No embeddings in ChromaDB — run `store` first.")
        return {}

    logger.info("Fetching %d embeddings from ChromaDB …", count)
    raw = collection.get(include=["embeddings", "documents", "metadatas"])
    ids: list[str] = raw["ids"]
    embeddings = np.array(raw["embeddings"], dtype=np.float32)
    documents: list[str] = raw["documents"]
    metadatas: list[dict] = raw["metadatas"]

    # Normalise embeddings for cosine similarity (L2-norm → dot product = cosine)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    embeddings = embeddings / norms

    logger.info("Running HDBSCAN (min_cluster_size=%d, min_samples=%d, metric=cosine) …",
                min_cluster_size, min_samples)
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",   # euclidean on L2-normalised vectors == cosine
        cluster_selection_method="eom",
        core_dist_n_jobs=-1,
    )
    labels: np.ndarray = clusterer.fit_predict(embeddings)

    unique = set(labels)
    n_clusters = len(unique - {-1})
    n_noise = int((labels == -1).sum())
    logger.info("Clusters found: %d  |  noise points: %d", n_clusters, n_noise)

    # Group reviews by cluster label
    groups: dict[int, dict] = {}
    for idx, (lbl, doc, meta) in enumerate(zip(labels, documents, metadatas)):
        lbl = int(lbl)
        if lbl == -1:
            continue
        if lbl not in groups:
            groups[lbl] = {"texts": [], "ids": [], "sources": []}
        groups[lbl]["texts"].append(doc)
        groups[lbl]["ids"].append(ids[idx])
        groups[lbl]["sources"].append(meta.get("source", "unknown"))

    # Label each cluster
    cluster_summary: dict[str, dict] = {}
    for lbl in sorted(groups):
        data = groups[lbl]
        labeling = _label_cluster(data["texts"])
        source_counts = {s: data["sources"].count(s) for s in set(data["sources"])}
        cluster_summary[str(lbl)] = {
            "label": labeling["label"],
            "description": labeling["description"],
            "size": len(data["texts"]),
            "sources": source_counts,
            "review_ids": data["ids"],
        }
        logger.info(
            "  Cluster %d — '%s' (%d reviews) [%s]",
            lbl,
            labeling["label"],
            len(data["texts"]),
            ", ".join(f"{s}:{n}" for s, n in source_counts.items()),
        )

    save_cache()
    save_insight("theme_clusters", cluster_summary)
    logger.info("Cluster results saved to insights table (metric='theme_clusters').")
    return cluster_summary
