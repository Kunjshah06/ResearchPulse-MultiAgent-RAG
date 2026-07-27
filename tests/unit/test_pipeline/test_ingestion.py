# =============================================================================
# PaperMind AI — Ingestion Pipeline Tests
# =============================================================================

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
import pytest

from papermind.models.domain.document import DocumentStatus, PipelineType
from papermind.services.document.ingestion_service import IngestionService


@pytest.fixture
def test_pdfs_dir(tmp_path) -> Path:
    """Fixture creating temp directories for test PDFs."""
    pdf_dir = tmp_path / "test_pdfs"
    pdf_dir.mkdir()
    return pdf_dir


@pytest.fixture
def digital_pdf_path(test_pdfs_dir) -> str:
    """Creates a simple native 2-page PDF for testing."""
    pdf_path = test_pdfs_dir / "digital_test.pdf"

    # Generate simple PDF using PyMuPDF
    doc = fitz.open()

    # Page 1: Abstract & Introduction
    page1 = doc.new_page()
    page1.insert_text((50, 50), "PaperMind AI Research Platform", fontsize=20)
    page1.insert_text((50, 100), "Abstract", fontsize=14)
    page1.insert_text((50, 130), "This is a digital native PDF test document used to evaluate extraction pipelines.")
    page1.insert_text((50, 200), "Introduction", fontsize=14, fontname="hebo")
    page1.insert_text((50, 230), "Section 1 details the core architecture and ingestion capabilities.")

    # Page 2: References
    page2 = doc.new_page()
    page2.insert_text((50, 50), "References", fontsize=14)
    page2.insert_text((50, 80), "[1] Vaswani et al. Attention is all you need. 2017.")
    page2.insert_text((50, 110), "[2] Devlin et al. BERT: Pre-training of deep bidirectional transformers. 2018.")

    doc.save(str(pdf_path))
    doc.close()

    return str(pdf_path)


@pytest.fixture
def scanned_pdf_path(test_pdfs_dir) -> str:
    """Creates a scanned PDF (image-only pages) for testing."""
    pdf_path = test_pdfs_dir / "scanned_test.pdf"

    # First create a temp page as image, then insert it as image to a new PDF
    temp_doc = fitz.open()
    temp_page = temp_doc.new_page(width=300, height=300)
    # Put text
    temp_page.insert_text((20, 40), "Scanned Page Text", fontsize=16)
    temp_page.insert_text((20, 100), "This page was rendered and re-inserted as an image.", fontsize=10)

    pix = temp_page.get_pixmap(dpi=100)
    img_data = pix.tobytes()
    temp_doc.close()

    # Write to image-only PDF
    scanned_doc = fitz.open()
    page = scanned_doc.new_page(width=300, height=300)
    page.insert_image(page.rect, stream=img_data)

    scanned_doc.save(str(pdf_path))
    scanned_doc.close()

    return str(pdf_path)


@pytest.mark.asyncio
async def test_digital_pipeline_ingestion(digital_pdf_path):
    """Verifies digital PDF ingestion, metadata parsing, and layout extraction."""
    service = IngestionService()
    doc = await service.ingest_document(digital_pdf_path)

    assert doc.status == DocumentStatus.COMPLETED
    assert doc.pipeline_type == PipelineType.DIGITAL
    assert doc.metadata.page_count == 2
    assert not doc.metadata.is_scanned

    # Verify element extractions
    assert len(doc.elements) > 0
    # Check title detection
    titles = [el for el in doc.elements if el.element_type.value == "title"]
    assert len(titles) > 0
    assert "PaperMind AI" in titles[0].content

    # Check headings
    headings = [el for el in doc.elements if el.element_type.value in ("heading", "subheading")]
    assert len(headings) > 0
    assert any("Introduction" in h.content for h in headings)

    # Check references section
    refs = [el for el in doc.elements if el.element_type.value == "references"]
    assert len(refs) > 0


@pytest.mark.asyncio
async def test_scanned_pipeline_ingestion(mocker, scanned_pdf_path):
    """Verifies scanned PDF ingestion via OCR fallback."""
    from unittest.mock import AsyncMock

    from papermind.models.domain.document import BoundingBox, OCREngine, OCRLine, OCRPage, OCRWord

    mock_page = OCRPage(
        page_number=1,
        lines=[
            OCRLine(
                text="Scanned Page Text",
                confidence=0.9,
                words=[
                    OCRWord(text="Scanned", confidence=0.9, bounding_box=BoundingBox(x0=0.0, y0=0.0, x1=0.2, y1=0.1, page=1), engine=OCREngine.PADDLEOCR),
                    OCRWord(text="Page", confidence=0.9, bounding_box=BoundingBox(x0=0.21, y0=0.0, x1=0.4, y1=0.1, page=1), engine=OCREngine.PADDLEOCR),
                    OCRWord(text="Text", confidence=0.9, bounding_box=BoundingBox(x0=0.41, y0=0.0, x1=0.6, y1=0.1, page=1), engine=OCREngine.PADDLEOCR),
                ],
                bounding_box=BoundingBox(x0=0.0, y0=0.0, x1=0.6, y1=0.1, page=1)
            ),
            OCRLine(
                text="This page was rendered and re-inserted as an image.",
                confidence=0.95,
                words=[
                    OCRWord(text="This", confidence=0.95, bounding_box=BoundingBox(x0=0.0, y0=0.2, x1=0.1, y1=0.3, page=1), engine=OCREngine.PADDLEOCR),
                    OCRWord(text="page", confidence=0.95, bounding_box=BoundingBox(x0=0.11, y0=0.2, x1=0.2, y1=0.3, page=1), engine=OCREngine.PADDLEOCR),
                    OCRWord(text="was", confidence=0.95, bounding_box=BoundingBox(x0=0.21, y0=0.2, x1=0.3, y1=0.3, page=1), engine=OCREngine.PADDLEOCR),
                    OCRWord(text="rendered", confidence=0.95, bounding_box=BoundingBox(x0=0.31, y0=0.2, x1=0.5, y1=0.3, page=1), engine=OCREngine.PADDLEOCR),
                ],
                bounding_box=BoundingBox(x0=0.0, y0=0.2, x1=0.9, y1=0.3, page=1)
            )
        ],
        full_text="Scanned Page Text\nThis page was rendered and re-inserted as an image.",
        mean_confidence=0.92,
        engine=OCREngine.PADDLEOCR,
        processing_time_ms=10.0
    )

    mocker.patch(
        "papermind.ocr.paddleocr.paddle_engine.PaddleOCREngine.perform_ocr",
        new=AsyncMock(return_value=mock_page)
    )

    service = IngestionService()
    doc = await service.ingest_document(scanned_pdf_path)

    assert doc.status == DocumentStatus.COMPLETED
    assert doc.pipeline_type == PipelineType.SCANNED
    assert doc.metadata.is_scanned
    assert doc.metadata.page_count == 1

    # Verify elements and OCR outputs
    assert len(doc.elements) > 0
    assert len(doc.ocr_results) == 1

    # Check content contains extracted OCR strings
    combined_text = " ".join([el.content for el in doc.elements])
    assert "Scanned" in combined_text
    assert "image" in combined_text
