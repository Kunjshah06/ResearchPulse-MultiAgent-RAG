# =============================================================================
# PaperMind AI — Layout Detector
# =============================================================================
# Analyzes document elements to detect and classify document regions such as
# text blocks, table regions, figure regions, and equation blocks.
# Uses heuristic rules over bounding-box geometry, font statistics, and
# content patterns to assign high-level region labels.
# =============================================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    BoundingBox,
    DocumentElement,
    ElementType,
)

log = get_logger(__name__)


class RegionType(str, Enum):
    """Detected layout region types."""

    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    EQUATION = "equation"
    HEADER = "header"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    CAPTION = "caption"
    PAGE_NUMBER = "page_number"
    UNKNOWN = "unknown"


@dataclass
class LayoutRegion:
    """A detected region in the page layout."""

    region_type: RegionType
    bounding_box: BoundingBox | None
    page_number: int
    confidence: float = 1.0
    elements: list[DocumentElement] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def text(self) -> str:
        return " ".join(el.content for el in self.elements)


# Regex patterns for detecting equations in text
_EQUATION_PATTERNS = [
    re.compile(r"[=<>≤≥≠±∓∑∏∫∂∇]"),  # math operators
    re.compile(r"\\(?:frac|sqrt|sum|int|prod|lim|log|exp|sin|cos|tan|alpha|beta|gamma|theta|lambda|sigma|delta|omega|phi|psi|epsilon|mu|pi|infty|partial|nabla|mathbb|mathcal|mathbf|mathrm|begin|end)\b"),  # LaTeX
    re.compile(r"\b[a-zA-Z]\s*\(\s*[a-zA-Z]\s*\)"),  # f(x) patterns
    re.compile(r"\b\d+\s*[\+\-\*\/\^]\s*\d+"),  # arithmetic
    re.compile(r"[αβγδεζηθικλμνξπρστυφχψω]"),  # Greek letters
]

# Patterns that indicate a caption
_CAPTION_PATTERNS = [
    re.compile(r"^(?:Figure|Fig\.?|Table|Tab\.?|Equation|Eq\.?)\s*\d+", re.IGNORECASE),
]

# Header/footer detection: elements near top/bottom margins
_HEADER_Y_THRESHOLD = 0.06   # top 6% of page
_FOOTER_Y_THRESHOLD = 0.94   # bottom 6% of page


class LayoutDetector:
    """
    Detects and classifies document layout regions from a list of DocumentElements.

    This detector operates at the page level and uses geometry, font metrics,
    and content heuristics to label each element with its region type.
    """

    def __init__(
        self,
        header_threshold: float = _HEADER_Y_THRESHOLD,
        footer_threshold: float = _FOOTER_Y_THRESHOLD,
        equation_min_symbols: int = 2,
    ) -> None:
        self._header_threshold = header_threshold
        self._footer_threshold = footer_threshold
        self._equation_min_symbols = equation_min_symbols

    def detect_regions(
        self,
        elements: list[DocumentElement],
        page_number: int | None = None,
    ) -> list[LayoutRegion]:
        """
        Classify a list of document elements into layout regions.

        Args:
            elements: Flat list of document elements (from a single page or full doc).
            page_number: If provided, filter elements by this page number.

        Returns:
            List of LayoutRegion objects with assigned region types.
        """
        if page_number is not None:
            elements = [el for el in elements if el.page_number == page_number]

        regions: list[LayoutRegion] = []

        for element in elements:
            region_type = self._classify_element(element)
            region = LayoutRegion(
                region_type=region_type,
                bounding_box=element.bounding_box,
                page_number=element.page_number,
                confidence=element.confidence,
                elements=[element],
            )
            regions.append(region)

        # Merge adjacent regions of the same type on the same page
        merged = self._merge_adjacent_regions(regions)

        log.debug(
            "Layout detection complete",
            page=page_number,
            total_elements=len(elements),
            regions_detected=len(merged),
        )
        return merged

    def _classify_element(self, element: DocumentElement) -> RegionType:
        """Classify a single element into a region type using heuristic rules."""

        # 1. Use existing element type as primary signal
        type_map = {
            ElementType.TABLE: RegionType.TABLE,
            ElementType.FIGURE: RegionType.FIGURE,
            ElementType.EQUATION: RegionType.EQUATION,
            ElementType.CAPTION: RegionType.CAPTION,
            ElementType.HEADER: RegionType.HEADER,
            ElementType.FOOTER: RegionType.FOOTER,
            ElementType.PAGE_NUMBER: RegionType.PAGE_NUMBER,
        }

        if element.element_type in type_map:
            return type_map[element.element_type]

        content = element.content
        bbox = element.bounding_box

        # 2. Caption detection via regex
        for pattern in _CAPTION_PATTERNS:
            if pattern.match(content.strip()):
                return RegionType.CAPTION

        # 3. Header/footer detection via vertical position
        if bbox:
            if bbox.y0 < self._header_threshold:
                # Small text near top is likely a header
                if element.font_size and element.font_size < 10.0:
                    return RegionType.HEADER
            if bbox.y1 > self._footer_threshold:
                if element.font_size and element.font_size < 10.0:
                    return RegionType.FOOTER

        # 4. Equation detection via content heuristics
        if self._is_equation_like(content):
            return RegionType.EQUATION

        # 5. Default: text region
        return RegionType.TEXT

    def _is_equation_like(self, text: str) -> bool:
        """Check if text content looks like a mathematical equation."""
        if len(text.strip()) < 3:
            return False

        match_count = sum(
            1 for pattern in _EQUATION_PATTERNS if pattern.search(text)
        )
        return match_count >= self._equation_min_symbols

    def _merge_adjacent_regions(
        self, regions: list[LayoutRegion]
    ) -> list[LayoutRegion]:
        """
        Merge vertically adjacent regions of the same type on the same page.

        Two regions are considered adjacent if they share the same type,
        are on the same page, and their bounding boxes are vertically close
        (within a small gap threshold).
        """
        if not regions:
            return []

        # Sort by page, then by vertical position
        sorted_regions = sorted(
            regions,
            key=lambda r: (
                r.page_number,
                r.bounding_box.y0 if r.bounding_box else 0.0,
            ),
        )

        merged: list[LayoutRegion] = [sorted_regions[0]]

        gap_threshold = 0.02  # 2% of page height

        for current in sorted_regions[1:]:
            prev = merged[-1]

            # Check merge conditions
            can_merge = (
                prev.region_type == current.region_type
                and prev.page_number == current.page_number
                and prev.bounding_box is not None
                and current.bounding_box is not None
            )

            if can_merge:
                assert prev.bounding_box is not None
                assert current.bounding_box is not None
                vertical_gap = abs(current.bounding_box.y0 - prev.bounding_box.y1)
                if vertical_gap <= gap_threshold:
                    # Merge: expand bounding box, combine elements
                    prev.bounding_box = BoundingBox(
                        x0=min(prev.bounding_box.x0, current.bounding_box.x0),
                        y0=min(prev.bounding_box.y0, current.bounding_box.y0),
                        x1=max(prev.bounding_box.x1, current.bounding_box.x1),
                        y1=max(prev.bounding_box.y1, current.bounding_box.y1),
                        page=prev.page_number,
                    )
                    prev.elements.extend(current.elements)
                    prev.confidence = min(prev.confidence, current.confidence)
                    continue

            merged.append(current)

        return merged
