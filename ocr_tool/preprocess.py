"""
Image preprocessing pipeline for maximum OCR accuracy.

Multi-pass approach: each image is processed into multiple variants
(binarized, adaptive, enhanced, morphological) and the OCR engine
picks the best result from each pass.
"""

import os
import logging
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tiff", ".tif",
    ".bmp", ".gif", ".webp", ".ico", ".ppm",
    ".pgm", ".pbm", ".pnm"
}

MIN_DIMENSION = 800
MAX_UPSCALE = 4.0


def load_image(path: str) -> np.ndarray:
    """
    Load image from disk, supporting all major formats.
    Handles drag-and-drop paths (quoted strings).
    """
    path = path.strip('"').strip("'").strip()

    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported format: {ext!r}\n"
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is not None:
        if len(img.shape) == 2:
            return img
        if img.shape[2] == 4:
            alpha = img[:, :, 3]
            mask = alpha == 0
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img[mask] = [255, 255, 255]
        return img

    pil_img = Image.open(path)
    if pil_img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", pil_img.size, (255, 255, 255))
        try:
            bg.paste(pil_img, mask=pil_img.split()[-1])
        except Exception:
            bg.paste(pil_img)
        pil_img = bg
    else:
        pil_img = pil_img.convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _to_gray(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 2:
        return image.copy()
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _smart_upscale(gray: np.ndarray, debug: bool = False) -> tuple[np.ndarray, float]:
    h, w = gray.shape
    short_side = min(h, w)
    if short_side >= MIN_DIMENSION:
        return gray, 1.0

    scale = min(MAX_UPSCALE, MIN_DIMENSION / short_side)
    new_w, new_h = int(w * scale), int(h * scale)

    if debug:
        logger.debug("Upscaling %dx%d → %dx%d (×%.2f)", w, h, new_w, new_h, scale)

    upscaled = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    return upscaled, scale


def _denoise(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape
    if h * w > 4_000_000:
        return cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.fastNlMeansDenoising(gray, h=8, templateWindowSize=7, searchWindowSize=21)


def _enhance_contrast(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _deskew(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) < 10:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90
    if abs(angle) < 0.3:
        return gray
    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )


def build_variants(image: np.ndarray, debug: bool = False) -> list[tuple[str, np.ndarray]]:
    """
    Build multiple preprocessed variants of the image.
    The OCR engine will test each and select the best result.

    Returns list of (name, grayscale_ndarray) tuples.
    """
    gray = _to_gray(image)
    gray, _ = _smart_upscale(gray, debug=debug)
    gray = _deskew(gray)
    denoised = _denoise(gray)
    enhanced = _enhance_contrast(denoised)

    variants: list[tuple[str, np.ndarray]] = []

    _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("otsu", otsu))

    adaptive = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 8
    )
    variants.append(("adaptive", adaptive))

    _, otsu_inv = cv2.threshold(
        255 - enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    variants.append(("otsu_inv", 255 - otsu_inv))

    variants.append(("enhanced_gray", enhanced))

    kernel = np.ones((1, 1), np.uint8)
    morphed = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
    variants.append(("morphological", morphed))

    sharpened = cv2.filter2D(
        enhanced, -1,
        np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    )
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
    variants.append(("sharpened", sharpened))

    return variants
