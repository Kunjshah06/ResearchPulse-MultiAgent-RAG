# =============================================================================
# PaperMind AI — Document Knowledge Graph Unit Tests
# =============================================================================

from __future__ import annotations

import pytest

from papermind.graph.builders.document_graph_builder import (
    DocumentGraphBuilder,
    NodeType,
)
from papermind.graph.queries.graph_query_service import GraphQueryService
from papermind.models.domain.document import (
    Citation,
    Document,
    DocumentElement,
    ElementType,
    ExtractedEquation,
    ExtractedFigure,
    ExtractedTable,
    Reference,
)


@pytest.fixture
def sample_document() -> Document:
    doc = Document(filename="test.pdf", file_path="/path/test.pdf")
    doc.metadata.title = "Graph Paper Title"
    doc.metadata.authors = ["Alice Smith", "Bob Jones"]
    doc.metadata.page_count = 2

    doc.elements = [
        DocumentElement(
            element_type=ElementType.TITLE,
            content="Graph Paper Title",
            page_number=1,
            reading_order=0,
        ),
        DocumentElement(
            element_type=ElementType.HEADING,
            content="1. Introduction",
            page_number=1,
            reading_order=1,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="Paragraph content in intro.",
            page_number=1,
            reading_order=2,
        ),
    ]

    ref = Reference(id="ref1", index=1, title="Sample Ref Title", authors=["Vaswani"])
    cite = Citation(id="cite1", cite_key="[1]", page_number=1, reference_id="ref1")
    doc.references = [ref]
    doc.citations = [cite]

    doc.tables = [ExtractedTable(id="tab1", page_number=1, rows=2, cols=2, caption="Table 1")]
    doc.figures = [ExtractedFigure(id="fig1", page_number=1, caption="Figure 1")]
    doc.equations = [ExtractedEquation(id="eq1", page_number=1, raw_text="a^2 + b^2 = c^2")]

    return doc


def test_graph_builder_creates_nodes_and_edges(sample_document):
    builder = DocumentGraphBuilder()
    graph = builder.build(sample_document)

    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0

    node_types = {data.get("node_type") for _, data in graph.nodes(data=True)}
    assert NodeType.DOCUMENT.value in node_types
    assert NodeType.AUTHOR.value in node_types
    assert NodeType.PAGE.value in node_types
    assert NodeType.SECTION.value in node_types
    assert NodeType.CITATION.value in node_types
    assert NodeType.REFERENCE.value in node_types


def test_graph_query_service(sample_document):
    builder = DocumentGraphBuilder()
    graph = builder.build(sample_document)
    query_svc = GraphQueryService(graph)

    authors = query_svc.get_nodes_by_type(NodeType.AUTHOR)
    assert len(authors) == 2

    search_hits = query_svc.search_nodes("Title")
    assert len(search_hits) >= 1

    summary = query_svc.summary()
    assert summary["total_nodes"] == graph.number_of_nodes()
    assert summary["total_edges"] == graph.number_of_edges()
