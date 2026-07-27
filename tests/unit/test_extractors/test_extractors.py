# =============================================================================
# PaperMind AI — Extractors Unit Tests
# =============================================================================

from __future__ import annotations

import pytest

from papermind.extractors.citations.citation_extractor import CitationExtractor
from papermind.extractors.equations.equation_extractor import EquationExtractor
from papermind.extractors.figures.figure_extractor import FigureExtractor
from papermind.extractors.tables.table_extractor import TableExtractor
from papermind.models.domain.document import (
    BoundingBox,
    DocumentElement,
    ElementType,
    ExtractedFigure,
    ExtractedTable,
)


@pytest.fixture
def sample_elements() -> list[DocumentElement]:
    return [
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="As shown in previous work [1], attention mechanism is effective.",
            page_number=1,
            reading_order=0,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="Vaswani et al. (2017) introduced the transformer model.",
            page_number=1,
            reading_order=1,
        ),
        DocumentElement(
            element_type=ElementType.EQUATION,
            content="E = mc^2",
            page_number=1,
            reading_order=2,
        ),
        DocumentElement(
            element_type=ElementType.CAPTION,
            content="Figure 1: High-level system architecture.",
            page_number=1,
            bounding_box=BoundingBox(x0=0.1, y0=0.5, x1=0.9, y1=0.55, page=1),
            reading_order=3,
        ),
        DocumentElement(
            element_type=ElementType.CAPTION,
            content="Table 1: Benchmark accuracy comparison.",
            page_number=1,
            bounding_box=BoundingBox(x0=0.1, y0=0.8, x1=0.9, y1=0.85, page=1),
            reading_order=4,
        ),
        DocumentElement(
            element_type=ElementType.REFERENCES,
            content="References",
            page_number=2,
            reading_order=5,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="[1] Vaswani, A., et al. Attention is all you need. NIPS, 2017. doi:10.1016/j.artint.2017.01.001",
            page_number=2,
            reading_order=6,
        ),
    ]


def test_citation_and_reference_extraction(sample_elements):
    extractor = CitationExtractor()
    citations = extractor.extract_citations(sample_elements)
    references = extractor.extract_references(sample_elements)
    linked = extractor.link_citations_to_references(citations, references)

    assert len(citations) >= 2
    assert len(references) == 1
    assert references[0].index == 1
    assert references[0].doi == "10.1016/j.artint.2017.01.001"
    assert linked[0].reference_id == references[0].id


def test_equation_extraction(sample_elements):
    extractor = EquationExtractor()
    equations = extractor.extract_equations(sample_elements)

    assert len(equations) >= 1
    assert any("E = mc^2" in eq.raw_text for eq in equations)


def test_figure_caption_pairing(sample_elements):
    extractor = FigureExtractor()
    fig = ExtractedFigure(
        page_number=1,
        bounding_box=BoundingBox(x0=0.1, y0=0.3, x1=0.9, y1=0.48, page=1),
    )

    paired = extractor.pair_captions([fig], sample_elements)
    classified = extractor.classify_figure_type(paired)

    assert paired[0].caption == "Figure 1: High-level system architecture."
    assert classified[0].figure_type == "architecture"


def test_table_caption_pairing(sample_elements):
    extractor = TableExtractor()
    tbl = ExtractedTable(
        page_number=1,
        bounding_box=BoundingBox(x0=0.1, y0=0.6, x1=0.9, y1=0.78, page=1),
        rows=2,
        cols=2,
    )

    paired = extractor.pair_captions([tbl], sample_elements)
    assert paired[0].caption == "Table 1: Benchmark accuracy comparison."
