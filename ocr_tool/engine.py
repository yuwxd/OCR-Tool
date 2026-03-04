from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

PSM_MODES: dict[int, str] = {
    3:  "Fully automatic page segmentation",
    4:  "Single column of text",
    6:  "Uniform block of text",
    11: "Sparse text",
    12: "Sparse text + OSD",
    13: "Raw line",
}

TESSERACT_BASE_CONFIG = "--oem 3 --dpi 300"
CONFIDENCE_FALLBACK_THRESHOLD = 40.0


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str
    psm_mode: Optional[int]
    variant: str
    word_count: int
    char_count: int
    elapsed_ms: float
    warnings: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        if not self.text.strip():
            return 0.0
        return self.confidence * (1.0 + 0.05 * min(self.word_count, 50))

    def summary(self) -> str:
        return (
            f"[{self.engine}] psm={self.psm_mode} variant={self.variant} "
            f"conf={self.confidence:.1f}% words={self.word_count} "
            f"score={self.score:.1f} ({self.elapsed_ms:.0f}ms)"
        )


def _tesseract_single(
    image: np.ndarray,
    lang: str,
    psm: int,
    variant: str,
    debug: bool = False,
) -> OCRResult:
    t0 = time.perf_counter()
    pil_img = Image.fromarray(image)
    config = f"{TESSERACT_BASE_CONFIG} --psm {psm}"

    try:
        data = pytesseract.image_to_data(
            pil_img,
            lang=lang,
            config=config,
            output_type=pytesseract.Output.DICT,
        )
        text = pytesseract.image_to_string(pil_img, lang=lang, config=config)
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed or not in PATH.\n"
            "Install: https://github.com/tesseract-ocr/tesseract#installing-tesseract"
        )

    confidences = [
        int(c)
        for c, t in zip(data["conf"], data["text"])
        if str(c) not in ("-1", "") and str(t).strip()
    ]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    words = [w for w in text.split() if w.strip()]
    elapsed = (time.perf_counter() - t0) * 1000

    result = OCRResult(
        text=text.strip(),
        confidence=avg_conf,
        engine="tesseract",
        psm_mode=psm,
        variant=variant,
        word_count=len(words),
        char_count=len(text.replace(" ", "").replace("\n", "")),
        elapsed_ms=elapsed,
    )
    if debug:
        logger.debug("  %s", result.summary())
    return result


def run_tesseract_multipass(
    variants: list[tuple[str, np.ndarray]],
    lang: str = "eng",
    psm_modes: Optional[list[int]] = None,
    debug: bool = False,
) -> OCRResult:
    if psm_modes is None:
        psm_modes = list(PSM_MODES.keys())

    results: list[OCRResult] = []

    for variant_name, image in variants:
        for psm in psm_modes:
            result = _tesseract_single(image, lang, psm, variant_name, debug=debug)
            results.append(result)

    results.sort(key=lambda r: r.score, reverse=True)
    return results[0]


def run_easyocr(
    image: np.ndarray,
    lang: str = "en",
    debug: bool = False,
) -> Optional[OCRResult]:
    try:
        import easyocr
    except ImportError:
        return None

    t0 = time.perf_counter()
    easy_lang = lang[:2].lower()
    reader = easyocr.Reader([easy_lang], gpu=_gpu_available(), verbose=False)
    raw = reader.readtext(image)
    elapsed = (time.perf_counter() - t0) * 1000

    if not raw:
        return None

    lines: list[str] = []
    confidences: list[float] = []
    for (_, text, conf) in raw:
        lines.append(text)
        confidences.append(float(conf) * 100)

    combined = "\n".join(lines)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    words = combined.split()

    result = OCRResult(
        text=combined.strip(),
        confidence=avg_conf,
        engine="easyocr",
        psm_mode=None,
        variant="original",
        word_count=len(words),
        char_count=len(combined.replace(" ", "").replace("\n", "")),
        elapsed_ms=elapsed,
    )
    if debug:
        logger.debug("  %s", result.summary())
    return result


def extract(
    variants: list[tuple[str, np.ndarray]],
    lang: str = "eng",
    psm_modes: Optional[list[int]] = None,
    use_easyocr: bool = False,
    debug: bool = False,
) -> OCRResult:
    tess_result = run_tesseract_multipass(variants, lang=lang, psm_modes=psm_modes, debug=debug)

    if use_easyocr:
        original_image = variants[0][1] if variants else None
        if original_image is not None:
            easy_result = run_easyocr(original_image, lang=lang[:2], debug=debug)
            if easy_result is not None and easy_result.score > tess_result.score:
                return easy_result

    if tess_result.confidence < CONFIDENCE_FALLBACK_THRESHOLD and not use_easyocr:
        original_image = variants[0][1] if variants else None
        if original_image is not None:
            easy_result = run_easyocr(original_image, lang=lang[:2], debug=debug)
            if easy_result is not None and easy_result.score > tess_result.score:
                easy_result.warnings.append(
                    f"Tesseract confidence was low ({tess_result.confidence:.1f}%), "
                    "switched to EasyOCR"
                )
                return easy_result

    return tess_result


def _gpu_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
