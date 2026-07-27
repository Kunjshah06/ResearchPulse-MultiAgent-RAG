# =============================================================================
# PaperMind AI — Vector Store Factory
# =============================================================================
# Factory module for instantiating vector store backends (Qdrant, FAISS).
# A module-level singleton `_default_store` is used by the API layer so that
# all routes share the same in-memory index within a single process lifetime.
# =============================================================================

from __future__ import annotations

from typing import Literal

from papermind.vectorstore.base import BaseVectorStore
from papermind.vectorstore.faiss.faiss_store import FAISSVectorStore
from papermind.vectorstore.qdrant.qdrant_store import QdrantVectorStore

# ---------------------------------------------------------------------------
# Singleton store used by the API layer
# ---------------------------------------------------------------------------
_default_store: BaseVectorStore | None = None


def get_vector_store(
    backend: Literal["qdrant", "faiss"] = "qdrant",
    dimension: int = 384,
    location: str | None = ":memory:",
) -> BaseVectorStore:
    """
    Returns a configured vector store instance.

    The first call instantiates a singleton that is reused by subsequent calls,
    so documents indexed during /upload are visible to /search within the same
    process (e.g. FastAPI server or TestClient session).

    Args:
        backend: Backend store ('qdrant' or 'faiss').
        dimension: Embedding vector dimension.
        location: Storage location (e.g. ':memory:').

    Returns:
        Shared BaseVectorStore singleton instance.
    """
    global _default_store
    if _default_store is None:
        if backend == "faiss":
            _default_store = FAISSVectorStore(dimension=dimension)
        else:
            _default_store = QdrantVectorStore(dimension=dimension, location=location)
    return _default_store


def reset_vector_store() -> None:
    """
    Reset the singleton — intended for use in tests that need a clean state.
    Call this in teardown fixtures to prevent state leakage between tests.
    """
    global _default_store
    _default_store = None
