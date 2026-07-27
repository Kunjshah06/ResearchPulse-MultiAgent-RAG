# =============================================================================
# PaperMind AI — FAISS Vector Store
# =============================================================================
# Local fast vector database powered by Facebook AI Similarity Search (FAISS).
# Uses IndexFlatIP with L2 normalized vectors for exact inner product / cosine similarity.
# Stores chunk payloads in an in-memory mapping with optional disk persistence.
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import BoundingBox, ChunkType, SemanticChunk
from papermind.vectorstore.base import BaseVectorStore, VectorSearchResult

log = get_logger(__name__)


class FAISSVectorStore(BaseVectorStore):
    """FAISS vector store implementation for local embedded vector search."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        self.index: faiss.IndexFlatIP | None = None
        self._chunks: list[SemanticChunk] = []
        self.initialize()

    def initialize(self) -> None:
        """Initialize FAISS IndexFlatIP."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self._chunks = []

    def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        valid_chunks = [c for c in chunks if c.embedding is not None]
        if not valid_chunks or self.index is None:
            return False

        vectors = np.array([c.embedding for c in valid_chunks], dtype=np.float32)
        # Normalize vectors for Cosine Similarity via Inner Product
        faiss.normalize_L2(vectors)

        self.index.add(vectors)
        self._chunks.extend(valid_chunks)

        log.info("Added vectors to FAISS index", count=len(valid_chunks), total=self.index.ntotal)
        return True

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter_doc_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        if self.index is None or self.index.ntotal == 0:
            return []

        q_vec = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q_vec)

        # Retrieve top_k * 3 if filtering by doc_id to account for filtered out hits
        fetch_k = top_k if not filter_doc_ids else min(self.index.ntotal, top_k * 5)
        scores, indices = self.index.search(q_vec, k=fetch_k)

        results: list[VectorSearchResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            chunk = self._chunks[idx]

            if filter_doc_ids and chunk.doc_id not in filter_doc_ids:
                continue

            results.append(VectorSearchResult(chunk=chunk, score=float(score)))
            if len(results) >= top_k:
                break

        return results

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document vectors by rebuilding the index without the specified doc_id.
        """
        if not self._chunks:
            return True

        remaining_chunks = [c for c in self._chunks if c.doc_id != doc_id]
        if len(remaining_chunks) == len(self._chunks):
            return True

        log.info("Rebuilding FAISS index to remove doc_id", doc_id=doc_id)
        self.initialize()
        return self.upsert_chunks(remaining_chunks)

    def clear(self) -> bool:
        self.initialize()
        return True

    def save(self, filepath: str | Path) -> None:
        """Save FAISS index and chunk metadata to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, str(path) + ".index")
        with open(str(path) + ".json", "w", encoding="utf-8") as f:
            f.write(json.dumps([c.model_dump(mode="json") for c in self._chunks]))
        log.info("Saved FAISS index to disk", path=str(filepath))

    def load(self, filepath: str | Path) -> None:
        """Load FAISS index and chunk metadata from disk."""
        path = Path(filepath)
        if Path(str(path) + ".index").exists():
            self.index = faiss.read_index(str(path) + ".index")
        if Path(str(path) + ".json").exists():
            with open(str(path) + ".json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self._chunks = [SemanticChunk.model_validate(item) for item in data]
        log.info("Loaded FAISS index from disk", path=str(filepath), total=self.index.ntotal if self.index else 0)
