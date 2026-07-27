# =============================================================================
# PaperMind AI — Document Ingestion Service
# =============================================================================
# Unified service orchestrating digital vs scanned routing.
# Inspects native text content, coordinates parsing paths, aggregates elements,
# and compiles the final unified Document aggregate entity.
# =============================================================================

from __future__ import annotations

import time
import uuid
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF

from papermind.core.config.settings import get_settings
from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    Document,
    DocumentStatus,
    PipelineType,
    ProcessingStats,
)
from papermind.extractors.citations.citation_extractor import CitationExtractor
from papermind.extractors.equations.equation_extractor import EquationExtractor
from papermind.extractors.figures.figure_extractor import FigureExtractor
from papermind.extractors.tables.table_extractor import TableExtractor
from papermind.pipeline.digital.digital_parser import DigitalPDFParser
from papermind.pipeline.scanned.scanned_parser import ScannedPDFParser

log = get_logger(__name__)


class IngestionService:
    """Orchestrates PDF ingestion by routing to digital or scanned parsing paths."""

    def __init__(self) -> None:
        self.digital_parser = DigitalPDFParser()
        self.scanned_parser = ScannedPDFParser()

    async def ingest_document(self, file_path: str | Path, doc_id: str | None = None) -> Document:
        """
        Ingests a document, auto-detects pipeline routing, and aggregates elements.

        Args:
            file_path: Absolute file system path to the PDF.
            doc_id: Optional explicit document ID alignment.

        Returns:
            Populated Document domain entity.
        """
        t0 = time.perf_counter()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        log.info("Starting document ingestion", file_name=path.name)

        # 1. Initialize metadata & align doc_id with upload prefix
        metadata = self.digital_parser.extract_metadata(str(path))
        if not doc_id:
            parts = path.name.split("_")
            if len(parts) > 1 and len(parts[0]) >= 32:
                doc_id = parts[0]
            else:
                doc_id = str(uuid.uuid4())

        # Create base document shell
        doc = Document(
            id=doc_id,
            filename=path.name,
            file_path=str(path.resolve()),
            status=DocumentStatus.PROCESSING,
            metadata=metadata,
        )

        try:
            with fitz.open(str(path)) as pdf_doc:
                # 2. Determine pipeline type
                # Heuristic: if average text length per page is < 100 characters, route to scanned path
                total_text_len = 0
                for page in pdf_doc:
                    total_text_len += len(page.get_text().strip())

                avg_len = total_text_len / pdf_doc.page_count if pdf_doc.page_count > 0 else 0
                is_scanned = avg_len < 100

                doc.pipeline_type = PipelineType.SCANNED if is_scanned else PipelineType.DIGITAL
                doc.metadata.is_scanned = is_scanned

                log.info(
                    "Detected pipeline routing",
                    file_name=path.name,
                    routing=doc.pipeline_type.value,
                    avg_char_length=round(avg_len, 1),
                )

                elements = []
                ocr_results = []
                total_ocr_conf = 0.0
                ocr_page_count = 0

                # 3. Execute page-by-page parsing & render visual page images
                settings = get_settings()
                figures_dir = settings.storage.upload_dir.parent / "figures" / doc.id
                figures_dir.mkdir(parents=True, exist_ok=True)

                for idx, page in enumerate(pdf_doc):
                    page_num = idx + 1

                    # Render high-res 200-DPI visual page image for zero-download canvas rendering
                    page_img_path = figures_dir / f"page_{page_num}.png"
                    if not page_img_path.exists():
                        try:
                            pix = page.get_pixmap(dpi=200)
                            pix.save(str(page_img_path))
                        except Exception as e:
                            log.warning("Failed rendering page pixmap", page=page_num, error=str(e))

                    if doc.pipeline_type == PipelineType.DIGITAL:
                        page_elements = self.digital_parser.parse_page(page, page_num)
                        elements.extend(page_elements)
                    else:
                        page_elements, ocr_page = await self.scanned_parser.parse_page(page, page_num)
                        elements.extend(page_elements)
                        ocr_results.append(ocr_page)
                        total_ocr_conf += ocr_page.mean_confidence
                        ocr_page_count += 1

                # 4. Finalize Document & Run Specialized Extractors
                doc.elements = elements
                doc.ocr_results = ocr_results

                # Run Table Extractor
                try:
                    table_extractor = TableExtractor()
                    tables = table_extractor.extract_tables(str(path))
                    doc.tables = table_extractor.pair_captions(tables, elements)
                except Exception as e:
                    log.warning("Table extraction failed during ingestion", error=str(e))
                    doc.tables = []

                # Run Figure Extractor
                try:
                    figure_extractor = FigureExtractor()
                    figures = figure_extractor.extract_figures(str(path), doc.id)
                    doc.figures = figure_extractor.pair_captions(figures, elements)
                except Exception as e:
                    log.warning("Figure extraction failed during ingestion", error=str(e))
                    doc.figures = []

                # Run Equation Extractor
                try:
                    equation_extractor = EquationExtractor()
                    doc.equations = equation_extractor.extract_equations(elements)
                except Exception as e:
                    log.warning("Equation extraction failed during ingestion", error=str(e))
                    doc.equations = []

                # Run Citation Extractor
                try:
                    citation_extractor = CitationExtractor()
                    citations = citation_extractor.extract_citations(elements)
                    references = citation_extractor.extract_references(elements)
                    doc.citations = citation_extractor.link_citations_to_references(citations, references)
                    doc.references = references
                except Exception as e:
                    log.warning("Citation extraction failed during ingestion", error=str(e))
                    doc.citations = []
                    doc.references = []

                doc.status = DocumentStatus.COMPLETED

                # Compile statistics
                latency = time.perf_counter() - t0
                doc.stats = ProcessingStats(
                    total_pages=pdf_doc.page_count,
                    ocr_pages=ocr_page_count,
                    digital_pages=pdf_doc.page_count - ocr_page_count,
                    elements_detected=len(elements),
                    ocr_mean_confidence=total_ocr_conf / ocr_page_count if ocr_page_count > 0 else 1.0,
                    processing_time_seconds=latency,
                )

                log.info(
                    "Document ingestion complete",
                    file_name=path.name,
                    pages=doc.stats.total_pages,
                    elements=doc.stats.elements_detected,
                    latency_seconds=round(latency, 2),
                )

        except Exception as e:
            latency = time.perf_counter() - t0
            log.error("Ingestion pipeline failed", file_name=path.name, error=str(e))
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            doc.stats.processing_time_seconds = latency
            raise

        doc.updated_at = datetime.utcnow()
        return doc
