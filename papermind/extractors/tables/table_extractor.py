# =============================================================================
# PaperMind AI — Table Extractor (Option 3: Precision Vector-Line Table Cropping)
# =============================================================================
# Detects true table captions (excluding text mentions like 'Table 1 shows')
# and pairs them with horizontal vector lines to crop 100% exact high-res table images.
# Produces ExtractedTable domain objects with image_path, caption, and CSV export.
# =============================================================================

from __future__ import annotations

import csv
import io
import re
import uuid
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import pdfplumber

from papermind.core.config.settings import get_settings
from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    BoundingBox,
    DocumentElement,
    ElementType,
    ExtractedTable,
    TableCell,
)

log = get_logger(__name__)

# Verbs that indicate a text mention of a table rather than a table caption
_TEXT_MENTION_VERBS = re.compile(
    r"^Table\s+\d+\s+(?:shows|compares|presents|reports|displays|lists|gives|illustrates|demonstrates|is|was|were|can|contains|uses)\b",
    re.IGNORECASE,
)

# Valid table caption pattern (requires colon, period, or dash after number, e.g. "Table 1:", "Table 2.")
_VALID_TABLE_CAPTION = re.compile(
    r"^Table\s+\d+[\:\.\-]",
    re.IGNORECASE,
)


class TableExtractor:
    """
    Extracts tables from PDF documents using precision vector line detection
    and caption region cropping.
    """

    def __init__(
        self,
        min_rows: int = 2,
        min_cols: int = 2,
        output_dir: Path | None = None,
    ) -> None:
        self._min_rows = min_rows
        self._min_cols = min_cols
        if output_dir is None:
            settings = get_settings()
            self._output_dir = settings.storage.upload_dir.parent / "figures"
        else:
            self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def extract_tables(self, pdf_path: str) -> list[ExtractedTable]:
        """Extract all tables from a PDF file."""
        tables: list[ExtractedTable] = []
        doc_id = Path(pdf_path).stem.split("_")[0]
        doc_save_dir = self._output_dir / doc_id
        doc_save_dir.mkdir(parents=True, exist_ok=True)

        try:
            doc = fitz.open(pdf_path)
            for page_idx in range(len(doc)):
                page_num = page_idx + 1
                fitz_page = doc[page_idx]
                page_tables = self._extract_from_page(fitz_page, page_num, doc_save_dir)
                tables.extend(page_tables)
            doc.close()
        except Exception as e:
            log.error("Table extraction failed", path=pdf_path, error=str(e))

        log.info(
            "Table extraction complete",
            path=pdf_path,
            tables_found=len(tables),
        )
        return tables

    def extract_tables_from_page(
        self,
        pdf_path: str,
        page_number: int,
    ) -> list[ExtractedTable]:
        """Extract tables from a specific page."""
        try:
            doc = fitz.open(pdf_path)
            if page_number < 1 or page_number > len(doc):
                doc.close()
                return []
            fitz_page = doc[page_number - 1]
            doc_id = Path(pdf_path).stem.split("_")[0]
            doc_save_dir = self._output_dir / doc_id
            doc_save_dir.mkdir(parents=True, exist_ok=True)
            tables = self._extract_from_page(fitz_page, page_number, doc_save_dir)
            doc.close()
            return tables
        except Exception as e:
            log.error("Page table extraction failed", page=page_number, error=str(e))
            return []

    def _extract_from_page(
        self,
        fitz_page: fitz.Page,
        page_number: int,
        save_dir: Path,
    ) -> list[ExtractedTable]:
        """Detect true table captions and pair with horizontal vector rules for exact table cropping."""
        tables: list[ExtractedTable] = []
        page_rect = fitz_page.rect
        page_width = float(page_rect.width)
        page_height = float(page_rect.height)

        # 1. Extract vector drawings (horizontal lines) on the page
        drawings = fitz_page.get_drawings()
        horizontal_rules: list[fitz.Rect] = []

        for d in drawings:
            r = d["rect"]
            if r.width >= 80 and r.height <= 5:
                horizontal_rules.append(r)

        # 2. Locate standalone Table Captions (exclude text mentions like "Table 1 shows...")
        text_blocks = fitz_page.get_text("blocks")
        caption_blocks = []

        for b in text_blocks:
            txt = b[4].strip()
            if _TEXT_MENTION_VERBS.match(txt):
                continue
            if _VALID_TABLE_CAPTION.match(txt) or (re.match(r"^Table\s+\d+", txt, re.IGNORECASE) and len(txt) < 160):
                caption_blocks.append(b)

        # 3. Crop table region for each valid caption
        seen_bboxes = []

        for cap_idx, cap in enumerate(caption_blocks):
            cap_bbox = cap[:4]
            caption_text = cap[4].strip().replace("\n", " ")

            nearby_rules = [
                r for r in horizontal_rules
                if abs(r.y0 - cap_bbox[1]) < 350 or abs(r.y0 - cap_bbox[3]) < 350
            ]

            if nearby_rules:
                nearby_rules.sort(key=lambda r: r.y0)
                table_y0 = min(r.y0 for r in nearby_rules) - 20
                table_y1 = max(r.y1 for r in nearby_rules) + 15
                table_x0 = max(0, min(r.x0 for r in nearby_rules) - 10)
                table_x1 = min(page_width, max(r.x1 for r in nearby_rules) + 10)
            else:
                table_x0 = 0
                table_x1 = page_width
                table_y0 = max(0, cap_bbox[1] - 5)
                table_y1 = min(page_height, table_y0 + 240)

            crop_y0 = max(0, min(cap_bbox[1] - 10, table_y0))
            crop_y1 = min(page_height, max(table_y1, cap_bbox[3] + 40))

            overlap = False
            for sb in seen_bboxes:
                if abs(sb[1] - crop_y0) < 40 and abs(sb[3] - crop_y1) < 40:
                    overlap = True
                    break
            if overlap:
                continue
            seen_bboxes.append((table_x0, crop_y0, table_x1, crop_y1))

            clip_rect = fitz.Rect(table_x0, crop_y0, table_x1, crop_y1)

            img_path = save_dir / f"table_p{page_number}_{cap_idx + 1}.png"
            try:
                pix = fitz_page.get_pixmap(clip=clip_rect, dpi=250)
                pix.save(str(img_path))
            except Exception as e:
                log.warning("Failed to render table pixmap", error=str(e))

            table_grid = self._cluster_words_into_grid(fitz_page, (table_x0, crop_y0, table_x1, crop_y1))

            bbox = BoundingBox(
                x0=max(0.0, min(1.0, table_x0 / page_width)),
                y0=max(0.0, min(1.0, crop_y0 / page_height)),
                x1=max(1e-6, min(1.0, table_x1 / page_width)),
                y1=max(1e-6, min(1.0, crop_y1 / page_height)),
                page=page_number,
            )

            cells: list[TableCell] = []
            num_rows = len(table_grid) if table_grid else 0
            num_cols = max(len(r) for r in table_grid) if table_grid else 0

            for r_idx, row in enumerate(table_grid):
                for c_idx in range(num_cols):
                    val = row[c_idx] if c_idx < len(row) else ""
                    cells.append(
                        TableCell(
                            row=r_idx,
                            col=c_idx,
                            content=val,
                            is_header=(r_idx == 0),
                        )
                    )

            csv_repr = self._to_csv(table_grid) if table_grid else caption_text

            tables.append(
                ExtractedTable(
                    id=str(uuid.uuid4()),
                    page_number=page_number,
                    bounding_box=bbox,
                    rows=num_rows,
                    cols=num_cols,
                    cells=cells,
                    caption=caption_text,
                    image_path=str(img_path),
                    csv_repr=csv_repr,
                )
            )

        return tables

    def _cluster_words_into_grid(
        self,
        page: fitz.Page,
        clip_rect: tuple[float, float, float, float],
    ) -> list[list[str]]:
        """Cluster PyMuPDF words into lines and columns for CSV fallback."""
        words = page.get_text("words", clip=clip_rect)
        if not words:
            return []

        words_sorted = sorted(words, key=lambda w: (w[1], w[0]))

        rows: list[list[tuple[float, float, float, float, str]]] = []
        for w in words_sorted:
            w_y0 = w[1]
            placed = False
            for r in rows:
                r_y_avg = sum(item[1] for item in r) / len(r)
                if abs(w_y0 - r_y_avg) <= 5.0:
                    r.append((w[0], w[1], w[2], w[3], w[4]))
                    placed = True
                    break
            if not placed:
                rows.append([(w[0], w[1], w[2], w[3], w[4])])

        if not rows:
            return []

        all_x0s = [w[0] for r in rows for w in r]
        all_x0s.sort()

        col_clusters: list[float] = []
        for x in all_x0s:
            if not col_clusters or abs(x - col_clusters[-1]) > 30:
                col_clusters.append(x)

        grid: list[list[str]] = []
        for r in rows:
            row_cells = [""] * len(col_clusters)
            for w in r:
                w_x0 = w[0]
                text = w[4]
                best_col = 0
                best_dist = float("inf")
                for c_idx, c_x in enumerate(col_clusters):
                    dist = abs(w_x0 - c_x)
                    if dist < best_dist:
                        best_dist = dist
                        best_col = c_idx
                if row_cells[best_col]:
                    row_cells[best_col] += " " + text
                else:
                    row_cells[best_col] = text
            cleaned = [c.strip() for c in row_cells]
            if any(cleaned):
                grid.append(cleaned)

        return grid

    def pair_captions(
        self,
        tables: list[ExtractedTable],
        elements: list[DocumentElement],
    ) -> list[ExtractedTable]:
        """Pair extracted tables with caption elements."""
        caption_elements = [
            el for el in elements
            if el.element_type == ElementType.CAPTION
            or (el.content and re.match(r"^Table\s+\d+", el.content, re.IGNORECASE))
        ]

        for table in tables:
            best_caption = None
            best_distance = float("inf")

            for cap in caption_elements:
                if cap.page_number != table.page_number:
                    continue

                if cap.bounding_box and table.bounding_box:
                    dist = abs(cap.bounding_box.y0 - table.bounding_box.y1)
                    dist_below = abs(cap.bounding_box.y1 - table.bounding_box.y0)
                    distance = min(dist, dist_below)
                else:
                    distance = 0.05

                if distance < best_distance:
                    best_distance = distance
                    best_caption = cap

            if best_caption:
                table.caption = best_caption.content

        return tables

    @staticmethod
    def _to_csv(rows: list[list[str]]) -> str:
        """Convert raw row data to CSV string."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        for row in rows:
            writer.writerow(row)
        return buf.getvalue().strip()
