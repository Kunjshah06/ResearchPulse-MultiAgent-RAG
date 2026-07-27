# =============================================================================
# PaperMind AI — Layout & Tree Analysis Unit Tests
# =============================================================================

from __future__ import annotations

import pytest

from papermind.layout.detectors.layout_detector import (
    LayoutDetector,
    LayoutRegion,
    RegionType,
)
from papermind.layout.parsers.tree_builder import (
    DocumentTree,
    DocumentTreeBuilder,
    TreeNode,
)
from papermind.models.domain.document import (
    BoundingBox,
    DocumentElement,
    ElementType,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_elements() -> list[DocumentElement]:
    """Create a realistic list of document elements for testing."""
    return [
        DocumentElement(
            element_type=ElementType.TITLE,
            content="PaperMind AI: Document Intelligence Platform",
            page_number=1,
            bounding_box=BoundingBox(x0=0.1, y0=0.05, x1=0.9, y1=0.1, page=1),
            font_size=20.0,
            is_bold=True,
            reading_order=0,
        ),
        DocumentElement(
            element_type=ElementType.ABSTRACT,
            content="Abstract This paper presents a novel document understanding system.",
            page_number=1,
            bounding_box=BoundingBox(x0=0.1, y0=0.12, x1=0.9, y1=0.2, page=1),
            font_size=11.0,
            reading_order=1,
        ),
        DocumentElement(
            element_type=ElementType.HEADING,
            content="Introduction",
            page_number=1,
            bounding_box=BoundingBox(x0=0.1, y0=0.25, x1=0.5, y1=0.28, page=1),
            font_size=14.0,
            is_bold=True,
            reading_order=2,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="Document understanding is a critical challenge in AI research.",
            page_number=1,
            bounding_box=BoundingBox(x0=0.1, y0=0.3, x1=0.9, y1=0.4, page=1),
            font_size=10.0,
            reading_order=3,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="We propose a multi-stage pipeline for processing research papers.",
            page_number=1,
            bounding_box=BoundingBox(x0=0.1, y0=0.42, x1=0.9, y1=0.5, page=1),
            font_size=10.0,
            reading_order=4,
        ),
        DocumentElement(
            element_type=ElementType.HEADING,
            content="Methodology",
            page_number=2,
            bounding_box=BoundingBox(x0=0.1, y0=0.05, x1=0.5, y1=0.08, page=2),
            font_size=14.0,
            is_bold=True,
            reading_order=5,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="Our methodology leverages transformer-based models.",
            page_number=2,
            bounding_box=BoundingBox(x0=0.1, y0=0.1, x1=0.9, y1=0.2, page=2),
            font_size=10.0,
            reading_order=6,
        ),
        DocumentElement(
            element_type=ElementType.REFERENCES,
            content="References",
            page_number=2,
            bounding_box=BoundingBox(x0=0.1, y0=0.7, x1=0.4, y1=0.73, page=2),
            font_size=14.0,
            is_bold=True,
            reading_order=7,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            content="[1] Vaswani et al. Attention is all you need. 2017.",
            page_number=2,
            bounding_box=BoundingBox(x0=0.1, y0=0.75, x1=0.9, y1=0.78, page=2),
            font_size=9.0,
            reading_order=8,
        ),
    ]


# ---------------------------------------------------------------------------
# Layout Detector Tests
# ---------------------------------------------------------------------------


class TestLayoutDetector:
    def test_detect_regions_returns_regions(self, sample_elements):
        detector = LayoutDetector()
        regions = detector.detect_regions(sample_elements)
        assert len(regions) > 0
        assert all(isinstance(r, LayoutRegion) for r in regions)

    def test_detect_regions_filter_by_page(self, sample_elements):
        detector = LayoutDetector()
        page1_regions = detector.detect_regions(sample_elements, page_number=1)
        page1_elements = [el for el in sample_elements if el.page_number == 1]
        # Regions may be merged, so count <= elements
        assert len(page1_regions) <= len(page1_elements)

    def test_table_element_detected_as_table(self):
        detector = LayoutDetector()
        elements = [
            DocumentElement(
                element_type=ElementType.TABLE,
                content="Table content",
                page_number=1,
                bounding_box=BoundingBox(x0=0.1, y0=0.3, x1=0.9, y1=0.6, page=1),
            ),
        ]
        regions = detector.detect_regions(elements)
        assert regions[0].region_type == RegionType.TABLE

    def test_caption_detection_via_pattern(self):
        detector = LayoutDetector()
        elements = [
            DocumentElement(
                element_type=ElementType.PARAGRAPH,
                content="Figure 3: Architecture of the proposed model.",
                page_number=1,
                bounding_box=BoundingBox(x0=0.2, y0=0.5, x1=0.8, y1=0.52, page=1),
            ),
        ]
        regions = detector.detect_regions(elements)
        assert regions[0].region_type == RegionType.CAPTION

    def test_equation_detection_via_content(self):
        detector = LayoutDetector()
        elements = [
            DocumentElement(
                element_type=ElementType.PARAGRAPH,
                content="E = mc² where α = ∫ f(x) dx",
                page_number=1,
                bounding_box=BoundingBox(x0=0.2, y0=0.4, x1=0.8, y1=0.42, page=1),
            ),
        ]
        regions = detector.detect_regions(elements)
        assert regions[0].region_type == RegionType.EQUATION

    def test_header_detection_by_position(self):
        detector = LayoutDetector()
        elements = [
            DocumentElement(
                element_type=ElementType.PARAGRAPH,
                content="Journal of AI Research",
                page_number=1,
                font_size=8.0,
                bounding_box=BoundingBox(x0=0.3, y0=0.01, x1=0.7, y1=0.03, page=1),
            ),
        ]
        regions = detector.detect_regions(elements)
        assert regions[0].region_type == RegionType.HEADER

    def test_merge_adjacent_regions(self):
        detector = LayoutDetector()
        elements = [
            DocumentElement(
                element_type=ElementType.PARAGRAPH,
                content="First paragraph.",
                page_number=1,
                bounding_box=BoundingBox(x0=0.1, y0=0.3, x1=0.9, y1=0.35, page=1),
                reading_order=0,
            ),
            DocumentElement(
                element_type=ElementType.PARAGRAPH,
                content="Second paragraph.",
                page_number=1,
                bounding_box=BoundingBox(x0=0.1, y0=0.36, x1=0.9, y1=0.41, page=1),
                reading_order=1,
            ),
        ]
        regions = detector.detect_regions(elements)
        # Should be merged into 1 region (gap = 0.01 < threshold 0.02)
        assert len(regions) == 1
        assert len(regions[0].elements) == 2


# ---------------------------------------------------------------------------
# Tree Builder Tests
# ---------------------------------------------------------------------------


class TestDocumentTreeBuilder:
    def test_build_creates_tree(self, sample_elements):
        builder = DocumentTreeBuilder()
        tree = builder.build(sample_elements)
        assert isinstance(tree, DocumentTree)
        assert tree.total_nodes == len(sample_elements)

    def test_root_has_children(self, sample_elements):
        builder = DocumentTreeBuilder()
        tree = builder.build(sample_elements)
        assert len(tree.root.children) > 0

    def test_sections_detected(self, sample_elements):
        builder = DocumentTreeBuilder()
        tree = builder.build(sample_elements)
        sections = tree.sections
        # Should find: Title, Abstract, Introduction, Methodology, References
        section_titles = [s.section_title for s in sections]
        assert any("Introduction" in t for t in section_titles)
        assert any("Methodology" in t for t in section_titles)

    def test_paragraphs_nested_under_sections(self, sample_elements):
        builder = DocumentTreeBuilder()
        tree = builder.build(sample_elements)

        # Find the Introduction section node
        intro_node = None
        for node in tree.root.walk():
            if "Introduction" in node.section_title:
                intro_node = node
                break

        assert intro_node is not None
        # Introduction should have child paragraphs
        assert len(intro_node.children) > 0

    def test_flatten_preserves_all_elements(self, sample_elements):
        builder = DocumentTreeBuilder()
        tree = builder.build(sample_elements)
        flat = tree.flatten()
        assert len(flat) == len(sample_elements)

    def test_get_all_text(self, sample_elements):
        builder = DocumentTreeBuilder()
        tree = builder.build(sample_elements)
        text = tree.root.get_all_text()
        assert "PaperMind AI" in text
        assert "Introduction" in text

    def test_max_depth(self, sample_elements):
        builder = DocumentTreeBuilder()
        tree = builder.build(sample_elements)
        assert tree.max_depth >= 2  # root -> section -> paragraph

    def test_empty_elements(self):
        builder = DocumentTreeBuilder()
        tree = builder.build([])
        assert tree.total_nodes == 0
        assert tree.max_depth == 0
