# =============================================================================
# PaperMind AI — Image Preprocessing Engine
# =============================================================================
# Implements advanced computer vision techniques to clean and align page images
# prior to running OCR. Handles rotation (deskew), contrast alignment,
# and noise filtering.
# =============================================================================

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from papermind.core.logging.logger import get_logger

log = get_logger(__name__)


class ImagePreprocessor:
    """Preprocesses scanned document page images to optimize OCR results."""

    @staticmethod
    def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
        """Convert a PIL Image to an OpenCV BGR numpy array."""
        # Convert RGB to BGR
        open_cv_image = np.array(pil_img.convert("RGB"))
        return cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv2_to_pil(cv2_img: np.ndarray) -> Image.Image:
        """Convert an OpenCV BGR numpy array to a PIL Image."""
        rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def preprocess(
        self,
        pil_img: Image.Image,
        apply_deskew: bool = True,
        apply_denoise: bool = True,
        apply_clahe: bool = True,
        apply_binarization: bool = False,
    ) -> Image.Image:
        """
        Applies the standard CV preprocessing pipeline on an image.

        Args:
            pil_img: Input PIL Image.
            apply_deskew: Rotate back to 0 degrees if skewed.
            apply_denoise: Clean high-frequency scanner noise.
            apply_clahe: Equalize local contrast boundaries.
            apply_binarization: Convert to hard binary (Otsu). Generally False
                                for modern OCR models like PaddleOCR, which
                                perform better on clean grayscale/color.

        Returns:
            Preprocessed PIL Image.
        """
        img = self.pil_to_cv2(pil_img)

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Deskew
        if apply_deskew:
            gray = self.deskew(gray)

        # 3. Local Contrast Alignment (CLAHE)
        if apply_clahe:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

        # 4. Denoise
        if apply_denoise:
            # Fast Non-Local Means Denoising for single-channel grayscale
            gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

        # 5. Binarization
        if apply_binarization:
            # Otsu's thresholding after Gaussian filtering
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, gray = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Convert grayscale back to BGR for uniform channel interfaces
        color_out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return self.cv2_to_pil(color_out)

    def deskew(self, gray: np.ndarray) -> np.ndarray:
        """
        Detects skew angle of text blocks and rotates image to align.
        Uses Radon/Hough Transform logic for high precision.
        """
        # Threshold the image to invert colors (text becomes white on black background)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Dilate to merge words/lines into continuous bars
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilate = cv2.dilate(thresh, kernel, iterations=2)

        # Find coordinate boxes of dilated text blocks
        coords = np.column_stack(np.where(dilate > 0))
        if len(coords) == 0:
            return gray

        # Compute min area bounding box around all text pixels
        angle = cv2.minAreaRect(coords)[-1]

        # OpenCV minAreaRect returns angle in [-90, 0)
        # We need to compute correction angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # If angle is negligible, don't rotate to avoid interpolating quality loss
        if abs(angle) < 0.1 or abs(angle) > 45:
            return gray

        log.debug("Deskewing image", skew_angle=round(angle, 2))

        # Rotate the image
        h, w = gray.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Determine new bounds to prevent text clipping
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        # Adjust the translation components of rotation matrix
        rotation_matrix[0, 2] += (new_w / 2) - center[0]
        rotation_matrix[1, 2] += (new_h / 2) - center[1]

        # Perform rotation with white background padding
        rotated = cv2.warpAffine(
            gray,
            rotation_matrix,
            (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )

        return rotated
