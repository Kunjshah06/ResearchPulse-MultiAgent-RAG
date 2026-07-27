# =============================================================================
# PaperMind AI — API Routes Unit Tests
# =============================================================================
# EmbeddingService is mocked to avoid loading SentenceTransformer weights,
# which requires torch >= 2.6 (CVE-2025-32434). All other pipeline components
# (ingestion, chunking, vectorstore, graph) use real implementations.
# =============================================================================

from __future__ import annotations

from unittest.mock import patch

import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient

import papermind.vectorstore.factory as vs_factory
from papermind.api.main import app


# ---------------------------------------------------------------------------
# Mock EmbeddingService
# ---------------------------------------------------------------------------

class _FakeEmbeddingService:
    """Drop-in mock that returns deterministic 384-dim vectors without loading torch."""

    _DIM = 384

    def embed_document(self, doc):
        for chunk in doc.chunks:
            chunk.embedding = [0.1] * self._DIM
        doc.stats.embeddings_created = len(doc.chunks)
        return doc

    def embed_query(self, query: str) -> list[float]:
        return [0.1] * self._DIM


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_store():
    """Reset the singleton vector store before each test to prevent state leakage."""
    vs_factory.reset_vector_store()
    yield
    vs_factory.reset_vector_store()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_pdf_bytes(tmp_path) -> bytes:
    pdf_path = tmp_path / "api_test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "API Route Test Paper", fontsize=18)
    page.insert_text((50, 100), "This is an automated test for FastAPI document upload endpoint in PaperMind AI.")
    page.insert_text((50, 130), "Section 1 details the core architecture and ingestion capabilities of the dual-path PDF parser.")
    page.insert_text((50, 160), "Document intelligence platforms require robust section-aware chunking and graph reasoning.")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path.read_bytes()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health_check_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@patch("papermind.api.routes.documents.EmbeddingService", return_value=_FakeEmbeddingService())
def test_upload_document_endpoint(mock_embedder, client, sample_pdf_bytes):
    """
    Verifies the full upload pipeline (ingest → chunk → embed → index → graph).
    EmbeddingService is mocked to bypass torch version constraint.
    """
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("api_test.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["filename"] == "api_test.pdf"
    assert data["element_count"] > 0
    assert "id" in data
    assert data["chunk_count"] >= 1


@patch("papermind.api.routes.documents.EmbeddingService", return_value=_FakeEmbeddingService())
@patch("papermind.api.routes.search.EmbeddingService", return_value=_FakeEmbeddingService())
def test_search_documents_endpoint(mock_search_emb, mock_upload_emb, client, sample_pdf_bytes):
    """
    Verifies search returns hits from documents indexed during the same session.
    Both upload and search use the shared singleton vector store.
    """
    upload_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("api_test.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text

    search_res = client.post(
        "/api/v1/search/",
        json={"query": "FastAPI document upload", "top_k": 2},
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_hits"] >= 1
