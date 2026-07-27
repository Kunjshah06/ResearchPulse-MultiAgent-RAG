# =============================================================================
# PaperMind AI — Base Vector Store Interface
# =============================================================================
# Abstract interface for vector database implementations (Qdrant, FAISS, etc.).
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from papermind.models.domain.document import SemanticChunk


class VectorSearchResult:
    """Represents a vector similarity search hit."""

    def __init__(
        self,
        chunk: SemanticChunk,
        score: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.chunk = chunk
        self.score = score
        self.metadata = metadata or {}


class BaseVectorStore(ABC):
    """Abstract interface for storing and retrieving vector embeddings."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize collection/index schema."""
        pass

    @abstractmethod
    def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        """
        Insert or update a list of SemanticChunk objects with embeddings.

        Args:
            chunks: List of SemanticChunk domain objects containing embeddings.

        Returns:
            True if successful.
        """
        pass

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter_doc_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        """
        Perform vector similarity search.

        Args:
            query_vector: Search vector.
            top_k: Number of top results to return.
            filter_doc_ids: Optional list of document IDs to restrict search to.

        Returns:
            List of VectorSearchResult objects sorted by score descending.
        """
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """Delete all vectors associated with a specific document ID."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all stored vectors in the index/collection."""
        pass
