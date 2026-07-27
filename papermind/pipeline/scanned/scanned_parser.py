# =============================================================================
# PaperMind AI — Scanned PDF Parser
# =============================================================================
# Processes non-selectable scanned PDFs.
# Renders pages to images, preprocesses them with OpenCV, runs OCR, and wraps
# the results in standard DocumentElement hierarchies.
# =============================================================================

from __future__ import annotations

import fitz  # PyMuPDF
from PIL import Image

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    DocumentElement,
    ElementType,
    OCRPage,
)
from papermind.ocr.paddleocr.paddle_engine import PaddleOCREngine
from papermind.pipeline.preprocessing.image_processor import ImagePreprocessor

log = get_logger(__name__)


class ScannedPDFParser:
    """Renders scanned PDFs, applies computer vision preprocessing, and executes OCR."""

    def __init__(self) -> None:
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = PaddleOCREngine()

    def render_page_to_image(self, page: fitz.Page, dpi: int = 150) -> Image.Image:
        """Renders a PDF page to a PIL Image at specified DPI."""
        zoom = dpi / 72  # 72 is native PDF point scale
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        
        # Convert pixmap to PIL Image
        # Check if color channels match RGB or grayscale
        if pix.alpha:
            img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
            return img.convert("RGB")
        else:
            return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    async def parse_page(
        self,
        page: fitz.Page,
        page_number: int,
        dpi: int = 150,
    ) -> tuple[list[DocumentElement], OCRPage]:
        """
        Renders, preprocesses, runs OCR, and maps page output to DocumentElements.

        Args:
            page: PyMuPDF Page object.
            page_number: 1-indexed page index.
            dpi: Render resolution.

        Returns:
            Tuple of (DocumentElements, raw OCRPage).
        """
        log.info("Rendering scanned page", page=page_number, dpi=dpi)

        # 1. Render page to PIL image
        raw_img = self.render_page_to_image(page, dpi=dpi)

        # 2. Preprocess using CV techniques (deskew, denoise, CLAHE)
        processed_img = self.preprocessor.preprocess(
            raw_img,
            apply_deskew=True,
            apply_denoise=True,
            apply_clahe=True,
            apply_binarization=False,  # Keep grayscale/color for PaddleOCR
        )

        # 3. Perform OCR (PaddleOCR with Tesseract fallback)
        ocr_result = await self.ocr_engine.perform_ocr(processed_img, page_number)

        # 4. Map OCRLines into DocumentElements to match the digital pipeline output schema
        elements: list[DocumentElement] = []
        for line_idx, line in enumerate(ocr_result.lines):
            # Apply basic layout classification on string context
            lower_text = line.text.lower()
            el_type = ElementType.PARAGRAPH

            if len(line.text) < 80 and any(
                term in lower_text for term in ("abstract", "introduction", "conclusion", "references")
            ):
                if "references" in lower_text:
                    el_type = ElementType.REFERENCES
                elif "abstract" in lower_text:
                    el_type = ElementType.ABSTRACT
                else:
                    el_type = ElementType.HEADING
            elif len(line.text) < 6 and line.text.isdigit():
                el_type = ElementType.PAGE_NUMBER

            elements.append(
                DocumentElement(
                    element_type=el_type,
                    content=line.text,
                    page_number=page_number,
                    bounding_box=line.bounding_box,
                    confidence=line.confidence,
                    reading_order=line_idx,
                )
            )

        return elements, ocr_result
