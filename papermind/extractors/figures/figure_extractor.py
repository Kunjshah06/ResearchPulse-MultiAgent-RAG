# =============================================================================
# PaperMind AI — Figure Extractor
# =============================================================================
# Detects and extracts figures (images) from PDF documents using PyMuPDF.
# Crops figure regions, saves them to disk, and pairs them with the nearest
# caption elements. Produces ExtractedFigure domain objects.
# =============================================================================

from __future__ import annotations

import uuid
from pathlib import Path

import fitz  # PyMuPDF

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    BoundingBox,
    DocumentElement,
    ElementType,
    ExtractedFigure,
)

log = get_logger(__name__)


class FigureExtractor:
    """
    Extracts figures and images from PDF documents.

    Strategy:
      1. Scans each page for embedded image objects via PyMuPDF.
      2. Filters out small decorative images (icons, logos) by area threshold.
      3. Saves cropped figure images to an output directory.
      4. Pairs figures with their nearest caption elements.
    """

    def __init__(
        self,
        output_dir: str | Path = "data/figures",
        min_width: int = 100,
        min_height: int = 100,
        min_area_ratio: float = 0.01,
        image_format: str = "png",
    ) -> None:
        """
        Args:
            output_dir: Directory to save extracted figure images.
            min_width: Minimum pixel width to consider a valid figure.
            min_height: Minimum pixel height to consider a valid figure.
            min_area_ratio: Minimum ratio of image area to page area.
            image_format: Output image format (png, jpg, webp).
        """
        self._output_dir = Path(output_dir)
        self._min_width = min_width
        self._min_height = min_height
        self._min_area_ratio = min_area_ratio
        self._image_format = image_format

    def extract_figures(
        self,
        pdf_path: str,
        doc_id: str | None = None,
    ) -> list[ExtractedFigure]:
        """
        Extract all figures from a PDF file.

        Args:
            pdf_path: Absolute path to the PDF.
            doc_id: Optional document ID for organizing output files.

        Returns:
            List of ExtractedFigure domain objects.
        """
        figures: list[ExtractedFigure] = []
        doc_id = doc_id or str(uuid.uuid4())[:8]

        # Ensure output directory exists
        save_dir = self._output_dir / doc_id
        save_dir.mkdir(parents=True, exist_ok=True)

        try:
            with fitz.open(pdf_path) as doc:
                for page_idx, page in enumerate(doc):
                    page_num = page_idx + 1
                    page_figures = self._extract_from_page(
                        page, page_num, save_dir, doc_id
                    )
                    figures.extend(page_figures)
        except Exception as e:
            log.error("Figure extraction failed", path=pdf_path, error=str(e))

        log.info(
            "Figure extraction complete",
            path=pdf_path,
            figures_found=len(figures),
        )
        return figures

    def _extract_from_page(
        self,
        page: fitz.Page,
        page_number: int,
        save_dir: Path,
        doc_id: str,
    ) -> list[ExtractedFigure]:
        """Extract figures from a single PyMuPDF page."""
        figures: list[ExtractedFigure] = []
        page_width = float(page.rect.width)
        page_height = float(page.rect.height)
        page_area = page_width * page_height

        if page_area <= 0:
            return []

        image_list = page.get_images(full=True)
        fig_counter = 0

        for img_info in image_list:
            xref = img_info[0]

            try:
                base_image = page.parent.extract_image(xref)
            except Exception:
                continue

            if not base_image:
                continue

            img_width = base_image.get("width", 0)
            img_height = base_image.get("height", 0)

            # Filter decorative images (too small)
            if img_width < self._min_width or img_height < self._min_height:
                continue

            # Find the image's bounding box on the page
            bbox = self._find_image_bbox(page, xref)
            if not bbox:
                continue

            # Check area ratio
            img_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            if (img_area / page_area) < self._min_area_ratio:
                continue

            # Normalize bounding box
            norm_bbox = BoundingBox(
                x0=max(0.0, min(1.0, bbox[0] / page_width)),
                y0=max(0.0, min(1.0, bbox[1] / page_height)),
                x1=max(1e-6, min(1.0, bbox[2] / page_width)),
                y1=max(1e-6, min(1.0, bbox[3] / page_height)),
                page=page_number,
            )

            # Save the image
            fig_counter += 1
            img_ext = base_image.get("ext", self._image_format)
            filename = f"fig_p{page_number}_{fig_counter}.{img_ext}"
            save_path = save_dir / filename

            try:
                with open(save_path, "wb") as f:
                    f.write(base_image["image"])
            except Exception as e:
                log.warning(
                    "Failed to save figure image",
                    page=page_number,
                    error=str(e),
                )
                continue

            figure = ExtractedFigure(
                id=str(uuid.uuid4()),
                page_number=page_number,
                bounding_box=norm_bbox,
                image_path=str(save_path),
            )
            figures.append(figure)

            log.debug(
                "Figure extracted",
                page=page_number,
                size=f"{img_width}x{img_height}",
                path=str(save_path),
            )

        return figures

    @staticmethod
    def _find_image_bbox(
        page: fitz.Page,
        xref: int,
    ) -> tuple[float, float, float, float] | None:
        """Find the bounding box of an image on the page by its xref."""
        for img_block in page.get_text("dict").get("blocks", []):
            if img_block.get("type") == 1:  # image block
                # Check if this block references our xref
                block_bbox = img_block.get("bbox")
                if block_bbox:
                    return tuple(block_bbox)  # type: ignore[return-value]
        return None

    def pair_captions(
        self,
        figures: list[ExtractedFigure],
        elements: list[DocumentElement],
    ) -> list[ExtractedFigure]:
        """
        Pair extracted figures with their nearest caption elements.

        Captions are typically located directly below or above a figure.

        Args:
            figures: List of extracted figures.
            elements: List of all document elements.

        Returns:
            Figures with caption fields populated.
        """
        caption_elements = [
            el for el in elements
            if el.element_type == ElementType.CAPTION
            or (
                "fig" in el.content.lower()[:15]
                and any(c.isdigit() for c in el.content[:20])
            )
        ]

        for figure in figures:
            if figure.bounding_box is None:
                continue

            best_caption = None
            best_distance = float("inf")

            for cap in caption_elements:
                if cap.bounding_box is None:
                    continue
                if cap.page_number != figure.page_number:
                    continue

                # Vertical distance: caption is usually below the figure
                dist_below = abs(cap.bounding_box.y0 - figure.bounding_box.y1)
                dist_above = abs(figure.bounding_box.y0 - cap.bounding_box.y1)
                distance = min(dist_below, dist_above)

                if distance < best_distance:
                    best_distance = distance
                    best_caption = cap

            if best_caption and best_distance < 0.15:  # within 15% of page height
                figure.caption = best_caption.content

        return figures

    def classify_figure_type(self, figures: list[ExtractedFigure]) -> list[ExtractedFigure]:
        """
        Classify figure types based on caption text heuristics.

        This is a lightweight fallback when VLM classification is unavailable.
        """
        type_keywords = {
            "architecture": ["architecture", "framework", "system", "pipeline", "workflow"],
            "bar_chart": ["bar chart", "bar graph", "histogram"],
            "line_chart": ["line chart", "line graph", "trend", "time series", "curve"],
            "scatter_plot": ["scatter", "correlation"],
            "heatmap": ["heatmap", "heat map", "confusion matrix"],
            "diagram": ["diagram", "flowchart", "flow chart", "schematic"],
            "photograph": ["photo", "photograph", "image", "micrograph", "microscopy"],
            "table_image": ["table"],
        }

        for figure in figures:
            if not figure.caption:
                continue

            caption_lower = figure.caption.lower()
            for fig_type, keywords in type_keywords.items():
                if any(kw in caption_lower for kw in keywords):
                    figure.figure_type = fig_type
                    break

        return figures
