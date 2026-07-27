# =============================================================================
# PaperMind AI — PaddleOCR Wrapper with Tesseract Fallback
# =============================================================================

from __future__ import annotations

import time
from PIL import Image

from papermind.core.config.settings import get_settings
from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    BoundingBox,
    OCREngine,
    OCRLine,
    OCRPage,
    OCRWord,
)
from papermind.ocr.tesseract.tesseract_engine import TesseractOCREngine

log = get_logger(__name__)


class PaddleOCREngine:
    """
    PaddleOCR Engine wrapper.
    Falls back gracefully to Tesseract if PaddleOCR is not installed,
    crashes on import, or fails during execution.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.lang = settings.ocr.lang
        self.use_gpu = settings.ocr.use_gpu
        self.confidence_threshold = settings.ocr.confidence_threshold
        self._paddle_ocr = None
        self._fallback_engine = None
        self._init_failed = False

        if settings.ocr.engine == "tesseract":
            log.info("PaddleOCR bypassed; using Tesseract explicitly.")
            self._fallback_engine = TesseractOCREngine()
            return

        try:
            from paddleocr import PaddleOCR
            # Disable paddle logs to avoid console clutter
            self._paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False,
            )
            log.info("PaddleOCR engine loaded successfully.")
        except Exception as e:
            log.warning(
                "Failed to initialize PaddleOCR. Falling back to Tesseract.",
                error=str(e),
            )
            self._init_failed = True
            self._fallback_engine = TesseractOCREngine()

    async def perform_ocr(self, pil_img: Image.Image, page_number: int) -> OCRPage:
        """
        Runs PaddleOCR or falls back to Tesseract if needed.
        """
        if self._init_failed or self._paddle_ocr is None:
            # Safe fallback
            assert self._fallback_engine is not None
            return await self._fallback_engine.perform_ocr(pil_img, page_number)

        t0 = time.perf_counter()
        w, h = pil_img.size

        try:
            # Convert PIL to BGR array for PaddleOCR
            import numpy as np
            img_arr = np.array(pil_img.convert("RGB"))

            # PaddleOCR expects BGR format
            import cv2
            img_cv = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)

            # Perform OCR (cls=True enables orientation classification)
            result = self._paddle_ocr.ocr(img_cv, cls=True)
        except Exception as e:
            log.error(
                "PaddleOCR runtime failed. Executing Tesseract fallback.",
                page=page_number,
                error=str(e),
            )
            if self._fallback_engine is None:
                self._fallback_engine = TesseractOCREngine()
            return await self._fallback_engine.perform_ocr(pil_img, page_number)

        # Handle empty pages
        if not result or result[0] is None:
            return OCRPage(
                page_number=page_number,
                lines=[],
                full_text="",
                mean_confidence=1.0,
                engine=OCREngine.PADDLEOCR,
                processing_time_ms=(time.perf_counter() - t0) * 1000,
            )

        ocr_lines: list[OCRLine] = []
        full_text_parts: list[str] = []
        total_conf = 0.0
        word_count = 0

        # PaddleOCR outputs lines of text with coordinates:
        # [[[ [x0, y0], [x1, y1], [x2, y2], [x3, y3] ], ("text", confidence)]]
        page_results = result[0]
        for line_idx, line_data in enumerate(page_results):
            coords_box, (line_text, confidence) = line_data
            line_text = line_text.strip()
            if not line_text or confidence < self.confidence_threshold:
                continue

            # Extract box extremes and normalize
            xs = [pt[0] for pt in coords_box]
            ys = [pt[1] for pt in coords_box]
            x0 = max(0.0, min(xs) / w)
            y0 = max(0.0, min(ys) / h)
            x1 = min(1.0, max(xs) / w)
            y1 = min(1.0, max(ys) / h)

            line_box = BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1, page=page_number)

            # PaddleOCR returns line level text.
            # To match the domain schema of word coordinates, we split the words
            # and estimate coordinates proportionally to character counts
            words_in_line = line_text.split()
            ocr_words: list[OCRWord] = []
            char_count = sum(len(wd) for wd in words_in_line) + len(words_in_line) - 1

            current_x = x0
            line_width = x1 - x0

            for word_idx, wd_text in enumerate(words_in_line):
                wd_len = len(wd_text)
                # Approximate word width proportionally
                wd_w = (wd_len / max(1, char_count)) * line_width
                wd_x0 = current_x
                wd_x1 = min(x1, wd_x0 + wd_w)

                word_box = BoundingBox(
                    x0=wd_x0,
                    y0=y0,
                    x1=wd_x1,
                    y1=y1,
                    page=page_number,
                )

                ocr_words.append(
                    OCRWord(
                        text=wd_text,
                        confidence=confidence,
                        bounding_box=word_box,
                        engine=OCREngine.PADDLEOCR,
                    )
                )

                # Move boundary (plus gap fraction)
                current_x = wd_x1 + (1.0 / max(1, char_count)) * line_width

            # Append to lists
            full_text_parts.append(line_text)
            ocr_lines.append(
                OCRLine(
                    text=line_text,
                    confidence=confidence,
                    words=ocr_words,
                    bounding_box=line_box,
                )
            )

            total_conf += confidence * len(ocr_words)
            word_count += len(ocr_words)

        mean_confidence = total_conf / word_count if word_count > 0 else 1.0
        latency_ms = (time.perf_counter() - t0) * 1000

        log.debug(
            "PaddleOCR page complete",
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
            engine=OCREngine.PADDLEOCR,
            processing_time_ms=latency_ms,
        )
