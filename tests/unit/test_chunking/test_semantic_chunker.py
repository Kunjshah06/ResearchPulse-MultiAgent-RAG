# =============================================================================
# PaperMind AI — Semantic Chunker Unit Tests
# =============================================================================

from __future__ import annotations

import pytest

from papermind.chunking.chunker_service import ChunkerService
from papermind.chunking.strategies.semantic_chunker import SemanticChunker
from papermind.models.domain.document import (
    BoundingBox,
    ChunkType,
    Document,
    DocumentElement,
    ElementType,
    ExtractedEquation,
    ExtractedFigure,
    ExtractedTable,
    TableCell,
)


@pytest.fixture
def sample_document() -> Document:
    doc = Document(filename="test.pdf", file_path="/path/test.pdf")
    doc.elements = [
        DocumentElement(
            element_type=ElementType.TITLE,
            content="Sample Paper Title",
            page_number=1,
            reading_order=0,
        ),
        DocumentElement(
            element_type=ElementType.ABSTRACT,
            content="Abstract content explaining the core paper contribution.",
            page_number=1,
            reading_order=1,
        ),
        DocumentElement(
            element_type=ElementType.HEADING,
            content="1. Introduction",
            page_number=1,
            reading_order=2,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="This is the first sentence of the introduction. Here is more detail.",
            page_number=1,
            reading_order=3,
        ),
    ]

    doc.tables = [
        ExtractedTable(
            page_number=1,
            rows=2,
            cols=2,
            cells=[TableCell(row=0, col=0, content="H1"), TableCell(row=0, col=1, content="H2")],
            caption="Table 1: Test Results",
            csv_repr="H1,H2\nV1,V2",
        )
    ]

    doc.figures = [
        ExtractedFigure(
            page_number=1,
            caption="Figure 1: Architecture Diagram",
            description="Flowchart of pipeline",
        )
    ]

    doc.equations = [
        ExtractedEquation(
            page_number=1,
            raw_text="E = mc^2",
            latex="E = mc^2",
        )
    ]

    return doc


def test_semantic_chunker_generates_chunks(sample_document):
    chunker = SemanticChunker(max_tokens=100)
    chunks = chunker.chunk_document(sample_document)

    assert len(chunks) > 0
    types = {c.chunk_type for c in chunks}
    assert ChunkType.TABLE in types
    assert ChunkType.FIGURE in types
    assert ChunkType.EQUATION in types


def test_chunker_service_attaches_chunks(sample_document):
    service = ChunkerService()
    chunks = service.process_document(sample_document)

    assert len(sample_document.chunks) == len(chunks)
    assert sample_document.stats.chunks_created == len(chunks)
