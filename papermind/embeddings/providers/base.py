# =============================================================================
# PaperMind AI — Base Embedding Provider
# =============================================================================
# Abstract base class interface for all embedding providers (SentenceTransformers, OpenAI, etc).
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    """Abstract interface for dense embedding generation providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality of the embedding model."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name or identifier of the underlying model."""
        pass

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate dense embeddings for a list of string texts.

        Args:
            texts: List of strings to embed.

        Returns:
            List of float vector embeddings.
        """
        pass

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """
        Generate dense embedding for a single search query string.

        Args:
            query: Query string.

        Returns:
            Float vector embedding.
        """
        pass
