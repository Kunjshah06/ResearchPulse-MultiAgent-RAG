# =============================================================================
# PaperMind AI — Digital PDF Parser
# =============================================================================
# Uses PyMuPDF (fitz) to extract character coordinate boundaries, font specs,
# bold/italic styling, bookmarks, outline hierarchy, and metadata.
# Uses pdfplumber as a fallback or structure enhancer.
# =============================================================================

from __future__ import annotations

import fitz  # PyMuPDF
import pdfplumber

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    BoundingBox,
    DocumentElement,
    DocumentMetadata,
    DocumentType,
    ElementType,
)

log = get_logger(__name__)


class DigitalPDFParser:
    """Parses digital (native) PDFs, recovering characters, styles, fonts, and geometry."""

    def extract_metadata(self, doc_path: str) -> DocumentMetadata:
        """Extracts standard PDF header metadata, outlines, and metrics."""
        metadata = DocumentMetadata()

        try:
            with fitz.open(doc_path) as doc:
                metadata.page_count = doc.page_count
                info = doc.metadata or {}

                metadata.title = info.get("title") or None
                # Parse authors (split by comma if multiple)
                authors_raw = info.get("author")
                if authors_raw:
                    metadata.authors = [a.strip() for a in authors_raw.split(",") if a.strip()]

                # Date parsing: D:20241105... -> Extract year
                creation_date = info.get("creationDate")
                if creation_date and len(creation_date) >= 6:
                    try:
                        # Creation date format: D:YYYYMMDDHHMMSS
                        year_str = creation_date[2:6]
                        metadata.publication_year = int(year_str)
                    except ValueError:
                        pass

                # Check if TOC exists
                toc = doc.get_toc()
                metadata.has_toc = len(toc) > 0
                metadata.has_references = False  # Checked downstream

                # Guess paper type
                metadata.document_type = DocumentType.RESEARCH_PAPER

                # Basic scanner heuristic: If first page contains no selectable characters,
                # mark it tentatively as scanned.
                if doc.page_count > 0:
                    first_page = doc[0]
                    text = first_page.get_text()
                    if not text or len(text.strip()) < 20:
                        metadata.is_scanned = True

            # Get file size
            import os
            metadata.file_size_bytes = os.path.getsize(doc_path)

        except Exception as e:
            log.error("Failed to parse metadata", path=doc_path, error=str(e))

        return metadata

    def parse_page(self, page: fitz.Page, page_number: int) -> list[DocumentElement]:
        """
        Parses character spans, bounding boxes, and styles from a page.
        Groups them into raw layout chunks (e.g. paragraphs, headings).
        """
        elements: list[DocumentElement] = []
        w = float(page.rect.width)
        h = float(page.rect.height)

        if w <= 0 or h <= 0:
            return elements

        # Get low-level structured text blocks
        # "dict" format yields blocks -> lines -> spans -> characters
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        reading_counter = 0

        for block in blocks:
            # Type 0 is text block, Type 1 is image block
            if block.get("type") != 0:
                continue

            block_text_parts: list[str] = []
            block_spans = []

            # Aggregate all spans inside this text block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if text.strip():
                        block_text_parts.append(text)
                        block_spans.append(span)

            if not block_spans:
                continue

            # Merge text content
            full_text = " ".join(block_text_parts).strip()
            if not full_text:
                continue

            # Bounding box of the block
            bbox = block.get("bbox", (0, 0, 0, 0))
            box = BoundingBox(
                x0=max(0.0, bbox[0] / w),
                y0=max(0.0, bbox[1] / h),
                x1=min(1.0, bbox[2] / w),
                y1=min(1.0, bbox[3] / h),
                page=page_number,
            )

            # Determine dominant font size, font name, bold and italic states
            # from spans in this block
            font_sizes = [s.get("size", 10.0) for s in block_spans]
            font_names = [s.get("font", "") for s in block_spans]
            flags = [s.get("flags", 0) for s in block_spans]

            dom_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 10.0
            dom_name = max(set(font_names), key=font_names.count) if font_names else ""
            
            # Check style flags (bitmask: 2=Italic, 16=Bold)
            is_bold = any(flag & (1 << 4) for flag in flags)
            is_italic = any(flag & (1 << 1) for flag in flags)

            # Fallback string heuristics for bold/italic if flags are missing
            if not is_bold and any(
                any(term in name.lower() for term in ("bold", "black", "heavy", "semibold"))
                for name in font_names
            ):
                is_bold = True
            if not is_italic and any(
                "italic" in name.lower() or "oblique" in name.lower()
                for name in font_names
            ):
                is_italic = True

            # Heuristics to classify element type based on text length, font size, and layout position
            el_type = ElementType.PARAGRAPH
            lower_text = full_text.lower()

            if dom_size > 18.0 and page_number == 1 and reading_counter < 3:
                el_type = ElementType.TITLE
            elif dom_size > 11.5 and is_bold and len(full_text) < 120:
                el_type = ElementType.HEADING
            elif dom_size > 10.0 and is_bold and len(full_text) < 80:
                el_type = ElementType.SUBHEADING
            elif page_number == 1 and "abstract" in lower_text[:40]:
                el_type = ElementType.ABSTRACT
            elif "references" in lower_text and len(full_text) < 50:
                el_type = ElementType.REFERENCES
            elif len(full_text) < 6 and full_text.isdigit():
                el_type = ElementType.PAGE_NUMBER

            elements.append(
                DocumentElement(
                    element_type=el_type,
                    content=full_text,
                    page_number=page_number,
                    bounding_box=box,
                    confidence=1.0,
                    level=0,
                    font_size=dom_size,
                    font_name=dom_name,
                    is_bold=is_bold,
                    is_italic=is_italic,
                    reading_order=reading_counter,
                )
            )
            reading_counter += 1

        return elements
