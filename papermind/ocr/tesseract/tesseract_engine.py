# =============================================================================
# PaperMind AI — Tesseract OCR Wrapper
# =============================================================================

from __future__ import annotations

import time
import pytesseract
from PIL import Image

from papermind.core.config.settings import get_settings
from papermind.core.exceptions.errors import OCRError
from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    BoundingBox,
    OCREngine,
    OCRLine,
    OCRPage,
    OCRWord,
)

log = get_logger(__name__)


class TesseractOCREngine:
    """Tesseract OCR Engine wrapper with standardized outputs."""

    def __init__(self) -> None:
        settings = get_settings()
        self.cmd = settings.ocr.tesseract_cmd
        self.lang = settings.ocr.lang
        self.confidence_threshold = settings.ocr.confidence_threshold

        # If custom path is set in env, update pytesseract cmd path
        if self.cmd and self.cmd != "tesseract":
            pytesseract.pytesseract.tesseract_cmd = self.cmd

    async def perform_ocr(self, pil_img: Image.Image, page_number: int) -> OCRPage:
        """
        Runs Tesseract OCR on a page image and parses words and lines.

        Args:
            pil_img: Preprocessed page Image.
            page_number: 1-indexed page index.

        Returns:
            Structured OCRPage object.
        """
        t0 = time.perf_counter()
        w, h = pil_img.size

        try:
            # Query word-level details (includes coordinates, text, and confidence)
            # config: Oem 3 = Default OCR engine, Psm 1 = Automatic page segmentation with OSD
            data = pytesseract.image_to_data(
                pil_img,
                lang=self.lang,
                config="--oem 3 --psm 1",
                output_type=pytesseract.Output.DICT,
            )
        except Exception as e:
            log.error("Tesseract execution failed", page=page_number, error=str(e))
            raise OCRError(page=page_number, reason=f"Tesseract failure: {str(e)}") from e

        # Tesseract output parser
        words: list[OCRWord] = []
        n_elements = len(data["text"])

        # Group words by line_num, block_num, and par_num to reconstruct lines
        lines_map: dict[tuple[int, int, int], list[OCRWord]] = {}

        for i in range(n_elements):
            text = str(data["text"][i]).strip()
            conf_val = float(data["conf"][i])

            # Filter out spacing blocks or empty words
            if not text or conf_val < 0:
                continue

            # Normalized confidence [0..1]
            conf = conf_val / 100.0

            # Bounding box
            left = float(data["left"][i])
            top = float(data["top"][i])
            width = float(data["width"][i])
            height = float(data["height"][i])

            # Normalize coordinates relative to page size
            box = BoundingBox(
                x0=max(0.0, left / w),
                y0=max(0.0, top / h),
                x1=min(1.0, (left + width) / w),
                y1=min(1.0, (top + height) / h),
                page=page_number,
            )

            word = OCRWord(
                text=text,
                confidence=conf,
                bounding_box=box,
                engine=OCREngine.TESSERACT,
            )
            words.append(word)

            # Route to group
            line_key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            if line_key not in lines_map:
                lines_map[line_key] = []
            lines_map[line_key].append(word)

        # Assemble OCRLines
        ocr_lines: list[OCRLine] = []
        full_text_parts: list[str] = []
        total_conf = 0.0
        word_count = 0

        for line_key, line_words in lines_map.items():
            if not line_words:
                continue

            # Sort words horizontally within the line
            line_words.sort(key=lambda x: x.bounding_box.x0)

            # Construct line content
            line_text = " ".join([w.text for w in line_words])
            full_text_parts.append(line_text)

            # Compute line bounding box (union of word boxes)
            x0 = min([w.bounding_box.x0 for w in line_words])
            y0 = min([w.bounding_box.y0 for w in line_words])
            x1 = max([w.bounding_box.x1 for w in line_words])
            y1 = max([w.bounding_box.y1 for w in line_words])

            line_box = BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1, page=page_number)
            line_mean_conf = sum([w.confidence for w in line_words]) / len(line_words)

            ocr_line = OCRLine(
                text=line_text,
                confidence=line_mean_conf,
                words=line_words,
                bounding_box=line_box,
            )
            ocr_lines.append(ocr_line)

            total_conf += sum([w.confidence for w in line_words])
            word_count += len(line_words)

        mean_confidence = total_conf / word_count if word_count > 0 else 1.0
        latency_ms = (time.perf_counter() - t0) * 1000

        log.debug(
            "Tesseract page complete",
            page=page_number,
            words=word_count,
            lines=len(ocr_lines),
            confidence=round(mean_confidence, 3),
            latency_ms=round(latency_ms, 1),
        )

        return OCRPage(
            page_number=page_number,
            lines=ocr_lines,
            full_text="\n".join(full_text_parts),
            mean_confidence=mean_confidence,
            engine=OCREngine.TESSERACT,
            processing_time_ms=latency_ms,
        )
