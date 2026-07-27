# =============================================================================
# PaperMind AI — Chunker Service
# =============================================================================
# High-level entry point for semantic document chunking.
# Orchestrates chunking strategies, updates document statistics, and manages
# chunk persistence.
# =============================================================================

from __future__ import annotations

from papermind.chunking.strategies.semantic_chunker import SemanticChunker
from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import Document, SemanticChunk

log = get_logger(__name__)


class ChunkerService:
    """Service for orchestrating document chunking."""

    def __init__(self, default_chunker: SemanticChunker | None = None) -> None:
        self.chunker = default_chunker or SemanticChunker()

    def process_document(self, doc: Document) -> list[SemanticChunk]:
        """
        Extract semantic chunks from a Document and attach them to doc.chunks.

        Args:
            doc: The Document aggregate root entity.

        Returns:
            List of generated SemanticChunk domain entities.
        """
        log.info("Starting chunking process for document", doc_id=doc.id, title=doc.metadata.title)
        chunks = self.chunker.chunk_document(doc)
        
        # Attach chunks to Document entity and update stats
        doc.chunks = chunks
        doc.stats.chunks_created = len(chunks)

        log.info(
            "Completed document chunking",
            doc_id=doc.id,
            chunks_created=len(chunks),
        )

        return chunks
