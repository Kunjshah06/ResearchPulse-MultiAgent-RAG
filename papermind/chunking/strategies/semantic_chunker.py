# =============================================================================
# PaperMind AI — Semantic Chunker Strategy
# =============================================================================
# Implements section-aware and token-bounded semantic chunking.
# Preserves document hierarchy, keeps structural elements (tables, figures,
# equations) intact as specialized chunks, and splits text using semantic
# boundaries (sentences/paragraphs) while respecting token constraints.
# =============================================================================

from __future__ import annotations

import re
import uuid
from typing import Any

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    BoundingBox,
    ChunkType,
    Document,
    DocumentElement,
    ElementType,
    ExtractedEquation,
    ExtractedFigure,
    ExtractedTable,
    SemanticChunk,
)

log = get_logger(__name__)

# Basic sentence boundary regex
_SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


class SemanticChunker:
    """
    Section-aware semantic chunking strategy for technical and academic documents.

    Key Features:
      - Respects section boundaries (e.g. Introduction, Methods, Results).
      - Treats tables, figures, and equations as atomic, specialized chunks.
      - Dynamic sliding window / paragraph packing up to max_tokens.
      - Maintains back-references to source document elements and bounding boxes.
    """

    def __init__(
        self,
        max_tokens: int = 512,
        min_tokens: int = 64,
        overlap_tokens: int = 64,
    ) -> None:
        """
        Args:
            max_tokens: Maximum approximate token limit per chunk.
            min_tokens: Minimum token target for merging small fragments.
            overlap_tokens: Token overlap between adjacent text chunks.
        """
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_tokens = overlap_tokens

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token count estimation (~4 chars per token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def chunk_document(self, doc: Document) -> list[SemanticChunk]:
        """
        Generate semantic chunks for an entire Document domain aggregate.

        Args:
            doc: The input Document entity.

        Returns:
            List of generated SemanticChunk objects.
        """
        chunks: list[SemanticChunk] = []

        # 1. Chunk specialized structured entities (Tables, Figures, Equations)
        chunks.extend(self._chunk_tables(doc))
        chunks.extend(self._chunk_figures(doc))
        chunks.extend(self._chunk_equations(doc))

        # 2. Chunk text elements grouped by section
        text_chunks = self._chunk_text_elements(doc)
        chunks.extend(text_chunks)

        # Sort chunks by page number and vertical position where available
        chunks.sort(
            key=lambda c: (
                c.page_number,
                c.bounding_box.y0 if c.bounding_box else 0.0,
            )
        )

        log.info(
            "Semantic chunking complete",
            doc_id=doc.id,
            total_chunks=len(chunks),
            text_chunks=len(text_chunks),
            table_chunks=len(doc.tables),
            figure_chunks=len(doc.figures),
            equation_chunks=len(doc.equations),
        )

        return chunks

    def _chunk_tables(self, doc: Document) -> list[SemanticChunk]:
        """Convert extracted tables into specialized table chunks."""
        chunks: list[SemanticChunk] = []
        for table in doc.tables:
            content_parts = []
            if table.caption:
                content_parts.append(f"Table Caption: {table.caption}")
            if table.csv_repr:
                content_parts.append(f"Table Data (CSV):\n{table.csv_repr}")
            elif table.summary:
                content_parts.append(f"Table Summary: {table.summary}")

            content = "\n\n".join(content_parts)
            if not content.strip():
                content = f"Table on page {table.page_number} with {table.rows} rows and {table.cols} columns."

            tokens = self._estimate_tokens(content)
            chunk = SemanticChunk(
                id=str(uuid.uuid4()),
                doc_id=doc.id,
                chunk_type=ChunkType.TABLE,
                content=content,
                page_number=table.page_number,
                bounding_box=table.bounding_box,
                element_ids=[table.id],
                token_count=tokens,
                metadata={
                    "rows": table.rows,
                    "cols": table.cols,
                    "caption": table.caption,
                },
            )
            chunks.append(chunk)
        return chunks

    def _chunk_figures(self, doc: Document) -> list[SemanticChunk]:
        """Convert extracted figures into specialized figure chunks."""
        chunks: list[SemanticChunk] = []
        for fig in doc.figures:
            content_parts = []
            if fig.caption:
                content_parts.append(f"Figure Caption: {fig.caption}")
            if fig.description:
                content_parts.append(f"Figure Description: {fig.description}")

            content = "\n\n".join(content_parts)
            if not content.strip():
                content = f"Figure on page {fig.page_number} ({fig.figure_type or 'image'})."

            tokens = self._estimate_tokens(content)
            chunk = SemanticChunk(
                id=str(uuid.uuid4()),
                doc_id=doc.id,
                chunk_type=ChunkType.FIGURE,
                content=content,
                page_number=fig.page_number,
                bounding_box=fig.bounding_box,
                element_ids=[fig.id],
                token_count=tokens,
                metadata={
                    "image_path": fig.image_path,
                    "figure_type": fig.figure_type,
                    "caption": fig.caption,
                },
            )
            chunks.append(chunk)
        return chunks

    def _chunk_equations(self, doc: Document) -> list[SemanticChunk]:
        """Convert extracted equations into specialized equation chunks."""
        chunks: list[SemanticChunk] = []
        for eq in doc.equations:
            content = f"Equation: {eq.latex or eq.raw_text}"
            if eq.explanation:
                content += f"\nExplanation: {eq.explanation}"

            tokens = self._estimate_tokens(content)
            chunk = SemanticChunk(
                id=str(uuid.uuid4()),
                doc_id=doc.id,
                chunk_type=ChunkType.EQUATION,
                content=content,
                page_number=eq.page_number,
                bounding_box=eq.bounding_box,
                element_ids=[eq.id],
                token_count=tokens,
                metadata={
                    "raw_text": eq.raw_text,
                    "latex": eq.latex,
                    "variables": eq.variables,
                    "is_inline": eq.is_inline,
                },
            )
            chunks.append(chunk)
        return chunks

    def _chunk_text_elements(self, doc: Document) -> list[SemanticChunk]:
        """Group text elements by section and pack into chunks under max_tokens."""
        chunks: list[SemanticChunk] = []
        if not doc.elements:
            return chunks

        # Group elements by current section heading
        current_section = "Main"
        current_section_level = 0
        current_elements: list[DocumentElement] = []

        for element in doc.elements:
            # Skip tables/figures/equations if they are already handled as discrete elements
            if element.element_type in (
                ElementType.TABLE,
                ElementType.FIGURE,
                ElementType.EQUATION,
                ElementType.HEADER,
                ElementType.FOOTER,
                ElementType.PAGE_NUMBER,
            ):
                continue

            if element.element_type in (
                ElementType.TITLE,
                ElementType.HEADING,
                ElementType.SUBHEADING,
                ElementType.ABSTRACT,
                ElementType.REFERENCES,
            ):
                # Process buffer before starting new section
                if current_elements:
                    sub_chunks = self._pack_elements(
                        doc.id,
                        current_elements,
                        section=current_section,
                        section_level=current_section_level,
                    )
                    chunks.extend(sub_chunks)
                    current_elements = []

                current_section = element.content
                current_section_level = (
                    0 if element.element_type in (ElementType.TITLE, ElementType.ABSTRACT)
                    else 1 if element.element_type == ElementType.HEADING
                    else 2
                )
            else:
                current_elements.append(element)

        # Flush final buffer
        if current_elements:
            sub_chunks = self._pack_elements(
                doc.id,
                current_elements,
                section=current_section,
                section_level=current_section_level,
            )
            chunks.extend(sub_chunks)

        return chunks

    def _pack_elements(
        self,
        doc_id: str,
        elements: list[DocumentElement],
        section: str,
        section_level: int,
    ) -> list[SemanticChunk]:
        """Pack a list of elements within a section into token-bounded chunks."""
        chunks: list[SemanticChunk] = []
        if not elements:
            return chunks

        curr_text_parts: list[str] = []
        curr_element_ids: list[str] = []
        curr_page = elements[0].page_number
        curr_tokens = 0
        curr_boxes: list[BoundingBox] = []

        for el in elements:
            el_text = el.content.strip()
            if not el_text:
                continue

            el_tokens = self._estimate_tokens(el_text)

            # If a single element exceeds max_tokens, split by sentences
            if el_tokens > self.max_tokens:
                # Flush existing buffer first
                if curr_text_parts:
                    chunks.append(
                        self._create_text_chunk(
                            doc_id,
                            curr_text_parts,
                            curr_element_ids,
                            curr_page,
                            section,
                            section_level,
                            curr_boxes,
                        )
                    )
                    curr_text_parts, curr_element_ids, curr_boxes, curr_tokens = [], [], [], 0

                # Split large element by sentences
                sentences = _SENTENCE_SPLIT_REGEX.split(el_text)
                sent_buffer: list[str] = []
                sent_tokens = 0

                for sent in sentences:
                    s_tok = self._estimate_tokens(sent)
                    if sent_tokens + s_tok > self.max_tokens and sent_buffer:
                        chunks.append(
                            self._create_text_chunk(
                                doc_id,
                                sent_buffer,
                                [el.id],
                                el.page_number,
                                section,
                                section_level,
                                [el.bounding_box] if el.bounding_box else [],
                            )
                        )
                        sent_buffer = []
                        sent_tokens = 0

                    sent_buffer.append(sent)
                    sent_tokens += s_tok

                if sent_buffer:
                    chunks.append(
                        self._create_text_chunk(
                            doc_id,
                            sent_buffer,
                            [el.id],
                            el.page_number,
                            section,
                            section_level,
                            [el.bounding_box] if el.bounding_box else [],
                        )
                    )

                continue

            # Check if adding this element breaches max_tokens
            if curr_tokens + el_tokens > self.max_tokens and curr_text_parts:
                chunks.append(
                    self._create_text_chunk(
                        doc_id,
                        curr_text_parts,
                        curr_element_ids,
                        curr_page,
                        section,
                        section_level,
                        curr_boxes,
                    )
                )
                curr_text_parts, curr_element_ids, curr_boxes, curr_tokens = [], [], [], 0

            curr_text_parts.append(el_text)
            curr_element_ids.append(el.id)
            if el.bounding_box:
                curr_boxes.append(el.bounding_box)
            curr_tokens += el_tokens
            curr_page = el.page_number

        if curr_text_parts:
            chunks.append(
                self._create_text_chunk(
                    doc_id,
                    curr_text_parts,
                    curr_element_ids,
                    curr_page,
                    section,
                    section_level,
                    curr_boxes,
                )
            )

        return chunks

    def _create_text_chunk(
        self,
        doc_id: str,
        text_parts: list[str],
        element_ids: list[str],
        page_number: int,
        section: str,
        section_level: int,
        boxes: list[BoundingBox],
    ) -> SemanticChunk:
        content = "\n\n".join(text_parts)
        merged_box = None
        if boxes:
            merged_box = BoundingBox(
                x0=min(b.x0 for b in boxes),
                y0=min(b.y0 for b in boxes),
                x1=max(b.x1 for b in boxes),
                y1=max(b.y1 for b in boxes),
                page=page_number,
            )

        chunk_type = ChunkType.ABSTRACT if "abstract" in section.lower() else ChunkType.TEXT

        return SemanticChunk(
            id=str(uuid.uuid4()),
            doc_id=doc_id,
            chunk_type=chunk_type,
            content=content,
            page_number=page_number,
            section=section,
            section_level=section_level,
            bounding_box=merged_box,
            element_ids=element_ids,
            token_count=self._estimate_tokens(content),
        )
