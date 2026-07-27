# =============================================================================
# PaperMind AI — Qdrant Vector Store
# =============================================================================
# Vector database implementation powered by Qdrant.
# Supports payload filtering (by doc_id, section, chunk_type), HNSW indexing,
# and cosine/dot distance metric configurations.
# =============================================================================

from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from papermind.core.config.settings import get_settings
from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import BoundingBox, ChunkType, SemanticChunk
from papermind.vectorstore.base import BaseVectorStore, VectorSearchResult

log = get_logger(__name__)


class QdrantVectorStore(BaseVectorStore):
    """Qdrant vector database store implementation."""

    def __init__(
        self,
        collection_name: str | None = None,
        dimension: int = 384,
        host: str | None = None,
        port: int | None = None,
        location: str | None = None,
    ) -> None:
        settings = get_settings().vector_store
        self.collection_name = collection_name or settings.collection_name
        self.dimension = dimension

        if location == ":memory:":
            self.client = QdrantClient(":memory:")
        elif host or settings.host:
            self.client = QdrantClient(
                host=host or settings.host,
                port=port or settings.port,
                api_key=settings.api_key or None,
            )
        else:
            self.client = QdrantClient(":memory:")

        self.initialize()

    def initialize(self) -> None:
        """Create Qdrant collection if it does not already exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                log.info(
                    "Creating Qdrant collection",
                    collection=self.collection_name,
                    dim=self.dimension,
                )
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimension,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
        except Exception as e:
            log.error("Failed to initialize Qdrant collection", error=str(e))

    def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        valid_chunks = [c for c in chunks if c.embedding is not None]
        if not valid_chunks:
            log.warning("No chunks with valid embeddings provided for upsert")
            return False

        points = []
        for chunk in valid_chunks:
            assert chunk.embedding is not None
            payload = {
                "doc_id": chunk.doc_id,
                "chunk_type": chunk.chunk_type.value,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "section": chunk.section or "",
                "section_level": chunk.section_level,
                "token_count": chunk.token_count,
                "element_ids": chunk.element_ids,
            }
            if chunk.bounding_box:
                payload["bbox"] = {
                    "x0": chunk.bounding_box.x0,
                    "y0": chunk.bounding_box.y0,
                    "x1": chunk.bounding_box.x1,
                    "y1": chunk.bounding_box.y1,
                    "page": chunk.bounding_box.page,
                }

            point = qmodels.PointStruct(
                id=chunk.id,
                vector=chunk.embedding,
                payload=payload,
            )
            points.append(point)

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            log.info("Upserted points to Qdrant", count=len(points))
            return True
        except Exception as e:
            log.error("Qdrant upsert failed", error=str(e))
            return False

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter_doc_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        query_filter = None
        if filter_doc_ids:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="doc_id",
                        match=qmodels.MatchAny(any=filter_doc_ids),
                    )
                ]
            )

        try:
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
            )
            hits = response.points
        except Exception as e:
            log.error("Qdrant search failed", error=str(e))
            return []

        results = []
        for hit in hits:
            payload = hit.payload or {}
            bbox = None
            if "bbox" in payload:
                b = payload["bbox"]
                bbox = BoundingBox(
                    x0=b["x0"], y0=b["y0"], x1=b["x1"], y1=b["y1"], page=b["page"]
                )

            chunk = SemanticChunk(
                id=str(hit.id),
                doc_id=payload.get("doc_id", ""),
                chunk_type=ChunkType(payload.get("chunk_type", "text")),
                content=payload.get("content", ""),
                page_number=payload.get("page_number", 1),
                section=payload.get("section") or None,
                section_level=payload.get("section_level", 0),
                bounding_box=bbox,
                element_ids=payload.get("element_ids", []),
                token_count=payload.get("token_count", 0),
            )
            results.append(VectorSearchResult(chunk=chunk, score=hit.score, metadata=payload))

        return results

    def delete_document(self, doc_id: str) -> bool:
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="doc_id",
                                match=qmodels.MatchValue(value=doc_id),
                            )
                        ]
                    )
                ),
            )
            log.info("Deleted document vectors from Qdrant", doc_id=doc_id)
            return True
        except Exception as e:
            log.error("Failed to delete document from Qdrant", doc_id=doc_id, error=str(e))
            return False

    def clear(self) -> bool:
        try:
            self.client.delete_collection(self.collection_name)
            self.initialize()
            return True
        except Exception as e:
            log.error("Failed to clear Qdrant collection", error=str(e))
            return False
