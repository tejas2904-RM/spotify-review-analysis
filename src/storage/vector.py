"""Vector store — ChromaDB + sentence-transformers embeddings.

Embeds every relevant, non-spam clean review using the
`all-MiniLM-L6-v2` model and persists them in a local ChromaDB
collection at data/chroma/.

Provides:
  - embed_and_store()   — batch-embed all relevant reviews, upsert into Chroma
  - search()            — semantic nearest-neighbour search
  - collection_stats()  — quick size/metadata summary
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ChromaDB persist directory — override with CHROMA_DIR env var on Render
_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
_DEFAULT_CHROMA = str(_ROOT / "data" / "chroma")
CHROMA_DIR = os.getenv("CHROMA_DIR", _DEFAULT_CHROMA)
COLLECTION_NAME = "spotify_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 64   # sentence-transformers batch size

_client = None
_collection = None
_embedder = None


def _get_client():
    global _client
    if _client is None:
        import chromadb
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


def _get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers model: %s …", EMBED_MODEL)
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def embed_and_store(
    reviews: list[Any],          # list of CleanReview ORM objects
    batch_size: int = BATCH_SIZE,
) -> int:
    """Embed a list of CleanReview objects and upsert into ChromaDB.

    Returns the number of embeddings upserted.
    """
    if not reviews:
        logger.info("No reviews to embed.")
        return 0

    collection = _get_collection()
    embedder = _get_embedder()
    total = 0

    for i in range(0, len(reviews), batch_size):
        batch = reviews[i : i + batch_size]
        texts = [r.clean_text for r in batch]
        ids = [str(r.id) for r in batch]
        metadatas = [
            {
                "source": r.source,
                "is_spam": int(r.is_spam),
                "is_relevant": int(r.is_relevant),
                "language": r.language or "unknown",
                "token_count": r.token_count or 0,
                "created_at": str(r.created_at) if r.created_at else "",
                "raw_review_id": r.raw_review_id,
            }
            for r in batch
        ]

        embeddings = embedder.encode(texts, batch_size=batch_size, show_progress_bar=False).tolist()

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total += len(batch)
        logger.debug("Embedded and stored batch %d–%d (%d total so far)", i, i + len(batch), total)

    logger.info("Upserted %d embeddings into ChromaDB collection '%s'.", total, COLLECTION_NAME)
    return total


def search(
    query: str,
    n_results: int = 10,
    source_filter: str | None = None,
) -> list[dict]:
    """Semantic nearest-neighbour search over stored embeddings.

    Args:
        query:         Natural language query string.
        n_results:     Number of results to return.
        source_filter: Optionally restrict to a single source.

    Returns:
        List of dicts with keys: id, text, source, distance, metadata.
    """
    embedder = _get_embedder()
    collection = _get_collection()

    encoded = embedder.encode([query])
    query_embedding = encoded.tolist() if hasattr(encoded, "tolist") else list(encoded)

    where = {"source": source_filter} if source_filter else None
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, dist, cid in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
        results["ids"][0],
    ):
        output.append(
            {
                "id": cid,
                "text": doc,
                "source": meta.get("source"),
                "distance": round(dist, 4),
                "metadata": meta,
            }
        )
    return output


def collection_stats() -> dict:
    """Return basic stats about the ChromaDB collection."""
    collection = _get_collection()
    count = collection.count()
    return {
        "collection": COLLECTION_NAME,
        "total_embeddings": count,
        "chroma_dir": CHROMA_DIR,
        "embed_model": EMBED_MODEL,
    }


def reset_collection() -> None:
    """Delete and recreate the collection (use with caution)."""
    global _collection
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.warning("Deleted ChromaDB collection '%s'.", COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    _get_collection()
    logger.info("Recreated ChromaDB collection '%s'.", COLLECTION_NAME)
