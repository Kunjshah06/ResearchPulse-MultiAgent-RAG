# =============================================================================
# PaperMind AI — Embedding Service Unit Tests
# =============================================================================

from __future__ import annotations

import pytest

from papermind.embeddings.embedding_service import EmbeddingService
from papermind.embeddings.providers.base import BaseEmbeddingProvider
from papermind.models.domain.document import ChunkType, SemanticChunk


class DummyEmbeddingProvider(BaseEmbeddingProvider):
    @property
    def dimension(self) -> int:
        return 4

    @property
    def model_name(self) -> str:
        return "dummy-model"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, query: str) -> list[float]:
        return [1.0, 0.0, 0.0, 0.0]


def test_embedding_service_embeds_chunks():
    provider = DummyEmbeddingProvider()
    service = EmbeddingService(provider=provider)

    chunks = [
        SemanticChunk(doc_id="doc1", chunk_type=ChunkType.TEXT, content="Test text", page_number=1),
    ]

    updated = service.embed_chunks(chunks)
    assert len(updated) == 1
    assert updated[0].embedding == [1.0, 0.0, 0.0, 0.0]


def test_embedding_service_embed_query():
    provider = DummyEmbeddingProvider()
    service = EmbeddingService(provider=provider)

    vec = service.embed_query("search term")
    assert len(vec) == 4
    assert vec == [1.0, 0.0, 0.0, 0.0]
