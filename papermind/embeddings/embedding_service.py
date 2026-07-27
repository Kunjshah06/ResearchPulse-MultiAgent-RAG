# =============================================================================
# PaperMind AI — Embedding Service
# =============================================================================
# High-level service for generating and attaching embeddings to SemanticChunks
# and Document aggregates using configured providers.
# =============================================================================

# from __future__ import annotations

# import time

# from papermind.core.config.settings import get_settings
# from papermind.core.logging.logger import get_logger
# from papermind.embeddings.providers.base import BaseEmbeddingProvider
# from papermind.embeddings.providers.sentence_transformers_provider import (
#     SentenceTransformersProvider,
# )
# from papermind.models.domain.document import Document, SemanticChunk

# log = get_logger(__name__)


# class EmbeddingService:
#     """Service to generate dense embeddings for document chunks and queries."""

#     def __init__(self, provider: BaseEmbeddingProvider | None = None) -> None:
#         if provider is None:
#             settings = get_settings().embedding
#             if settings.provider == "sentence_transformers":
#                 provider = SentenceTransformersProvider(
#                     model_name=settings.model,
#                     device=settings.device,
#                     batch_size=settings.batch_size,
#                 )
#             else:
#                 # Default fallback
#                 provider = SentenceTransformersProvider(
#                     model_name="all-MiniLM-L6-v2",
#                     device="cpu",
#                 )
#         self.provider = provider
from __future__ import annotations

import time

from papermind.core.config.settings import get_settings
from papermind.core.logging.logger import get_logger
from papermind.embeddings.providers.base import BaseEmbeddingProvider
from papermind.embeddings.providers.fastembed_provider import (
    FastEmbedProvider,
)
from papermind.models.domain.document import Document, SemanticChunk

from papermind.embeddings.providers.tfidf_provider import TfIdfEmbeddingProvider

log = get_logger(__name__)


class EmbeddingService:
    """Service to generate dense embeddings for document chunks and queries."""

    def __init__(self, provider: BaseEmbeddingProvider | None = None) -> None:
        if provider is None:
            try:
                provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
                # Test embedding vector generation
                test_dim = provider.dimension
                if provider._use_mock:
                    log.warning("FastEmbed mock triggered. Switching to TfIdfEmbeddingProvider for accurate retrieval.")
                    provider = TfIdfEmbeddingProvider(dimension=384)
            except Exception as e:
                log.warning("FastEmbed load error. Switching to TfIdfEmbeddingProvider", error=str(e))
                provider = TfIdfEmbeddingProvider(dimension=384)

        self.provider = provider
        
    def embed_chunks(self, chunks: list[SemanticChunk]) -> list[SemanticChunk]:
        """
        Generate and assign embeddings to a list of SemanticChunk domain entities.

        Args:
            chunks: List of SemanticChunk objects.

        Returns:
            The input list with `embedding` populated on each chunk.
        """
        if not chunks:
            return []

        t0 = time.perf_counter()
        texts = [chunk.content for chunk in chunks]

        log.info("Generating embeddings for chunks", count=len(chunks), provider=self.provider.model_name)
        embeddings = self.provider.embed_texts(texts)

        for chunk, vec in zip(chunks, embeddings):
            chunk.embedding = vec

        latency = time.perf_counter() - t0
        log.info("Embeddings generated", count=len(chunks), latency_sec=round(latency, 2))

        return chunks

    def embed_document(self, doc: Document) -> Document:
        """
        Generate embeddings for all chunks in a Document and update stats.

        Args:
            doc: Document aggregate.

        Returns:
            Updated Document aggregate.
        """
        if not doc.chunks:
            log.warning("No chunks found in document for embedding", doc_id=doc.id)
            return doc

        self.embed_chunks(doc.chunks)
        doc.stats.embeddings_created = len(doc.chunks)
        return doc

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding vector for a user search query."""
        return self.provider.embed_query(query)
