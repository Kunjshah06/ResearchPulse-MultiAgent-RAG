# =============================================================================
# PaperMind AI — Vector Store Unit Tests
# =============================================================================

from __future__ import annotations

import pytest

from papermind.models.domain.document import ChunkType, SemanticChunk
from papermind.vectorstore.faiss.faiss_store import FAISSVectorStore
from papermind.vectorstore.qdrant.qdrant_store import QdrantVectorStore


@pytest.fixture
def sample_chunks():
    c1 = SemanticChunk(doc_id="doc1", chunk_type=ChunkType.TEXT, content="Introduction to AI", page_number=1)
    c1.embedding = [1.0, 0.0, 0.0, 0.0]

    c2 = SemanticChunk(doc_id="doc2", chunk_type=ChunkType.TEXT, content="Deep learning models", page_number=2)
    c2.embedding = [0.0, 1.0, 0.0, 0.0]

    return [c1, c2]


def test_faiss_vector_store(sample_chunks):
    store = FAISSVectorStore(dimension=4)
    success = store.upsert_chunks(sample_chunks)
    assert success is True

    # Search for first vector
    results = store.search(query_vector=[1.0, 0.0, 0.0, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0].chunk.doc_id == "doc1"

    # Filter doc_ids
    filtered = store.search(query_vector=[1.0, 0.0, 0.0, 0.0], top_k=2, filter_doc_ids=["doc2"])
    assert len(filtered) == 1
    assert filtered[0].chunk.doc_id == "doc2"


def test_qdrant_in_memory_vector_store(sample_chunks):
    store = QdrantVectorStore(dimension=4, location=":memory:", collection_name="test_col")
    success = store.upsert_chunks(sample_chunks)
    assert success is True

    results = store.search(query_vector=[1.0, 0.0, 0.0, 0.0], top_k=2)
    assert len(results) >= 1
    assert results[0].chunk.doc_id == "doc1"
