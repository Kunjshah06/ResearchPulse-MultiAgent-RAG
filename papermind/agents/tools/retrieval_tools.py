# =============================================================================
# PaperMind AI — Agent Retrieval Tools (Hybrid Vector + Metadata Filter)
# =============================================================================

from __future__ import annotations

from papermind.core.logging.logger import get_logger
from papermind.embeddings.embedding_service import EmbeddingService
from papermind.models.domain.document import ChunkType, SemanticChunk
from papermind.vectorstore.base import BaseVectorStore, VectorSearchResult
from papermind.vectorstore.factory import get_vector_store

log = get_logger(__name__)


class RetrievalTools:
    """
    Retrieval toolkit for agent nodes.

    Wraps vector similarity search with optional:
      - doc_id scoping
      - chunk type filtering (text, table, figure, equation)
      - top-k control per agent
    """

    def __init__(
        self,
        vector_store: BaseVectorStore | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.vector_store = vector_store or get_vector_store()
        self.embedding_service = embedding_service or EmbeddingService()

    def search_vector_store(
        self,
        query: str,
        top_k: int = 5,
        filter_doc_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        """Dense vector search over indexed document chunks with conversational fallback."""
        query_vector = self.embedding_service.embed_query(query)
        hits = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            filter_doc_ids=filter_doc_ids,
        )

        # Fallback: If 0 hits found, strip conversational stop words and search core keywords
        if not hits:
            import re
            cleaned_query = re.sub(
                r"(?i)\b(here|in|this|paper|manuscript|document|tell|me|which|were|present|what|is|are|the)\b",
                " ",
                query,
            ).strip()

            if cleaned_query and len(cleaned_query) >= 3:
                clean_vector = self.embedding_service.embed_query(cleaned_query)
                hits = self.vector_store.search(
                    query_vector=clean_vector,
                    top_k=top_k,
                    filter_doc_ids=filter_doc_ids,
                )

        # Ultimate Fallback: If still 0 hits, fetch general document chunks for the requested doc_id
        if not hits and filter_doc_ids:
            all_vector = self.embedding_service.embed_query("overview methodology results discussion abstract")
            hits = self.vector_store.search(
                query_vector=all_vector,
                top_k=top_k,
                filter_doc_ids=filter_doc_ids,
            )

        log.info("Vector retrieval", query=query[:60], hits=len(hits))
        return hits

    def search_by_chunk_type(
        self,
        query: str,
        chunk_type: ChunkType,
        top_k: int = 3,
        filter_doc_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        """Retrieve only chunks of a specific type (table, figure, equation)."""
        all_hits = self.search_vector_store(
            query=query,
            top_k=top_k * 5,  # oversample then filter
            filter_doc_ids=filter_doc_ids,
        )
        typed = [h for h in all_hits if h.chunk.chunk_type == chunk_type]
        return typed[:top_k]

    def format_context(
        self,
        hits: list[VectorSearchResult],
        include_metadata: bool = True,
    ) -> str:
        """Format retrieved hits into an LLM-ready context block."""
        if not hits:
            return ""
        blocks: list[str] = []
        for idx, hit in enumerate(hits, 1):
            c = hit.chunk
            header = (
                f"[Source {idx}] "
                f"Doc={c.doc_id[:8]}… | "
                f"Page={c.page_number} | "
                f"Type={c.chunk_type.value}"
            )
            if c.section and include_metadata:
                header += f" | Section={c.section}"
            blocks.append(f"{header}\n{c.content}")
        return "\n\n---\n\n".join(blocks)
