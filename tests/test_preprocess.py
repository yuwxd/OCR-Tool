import numpy as np
import pytest

from ocr_tool.preprocess import _to_gray, _smart_upscale, build_variants


def _make_gray(h: int = 100, w: int = 200) -> np.ndarray:
    return np.random.randint(0, 256, (h, w), dtype=np.uint8)


def _make_color(h: int = 100, w: int = 200) -> np.ndarray:
    return np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)


def test_to_gray_already_gray():
    img = _make_gray()
    result = _to_gray(img)
    assert result.shape == (100, 200)
    assert result.dtype == np.uint8


def test_to_gray_color_image():
    img = _make_color()
    result = _to_gray(img)
    assert len(result.shape) == 2


def test_smart_upscale_small_image():
    small = _make_gray(50, 100)
    scaled, factor = _smart_upscale(small)
    assert factor > 1.0
    assert scaled.shape[0] > 50
    assert scaled.shape[1] > 100


def test_smart_upscale_large_image():
    large = _make_gray(1200, 1600)
    _, factor = _smart_upscale(large)
    assert factor == 1.0


def test_build_variants_returns_multiple():
    img = _make_color()
    variants = build_variants(img, debug=False)
    assert len(variants) >= 4
    names = [v[0] for v in variants]
    assert "otsu" in names
    assert "adaptive" in names
    assert "enhanced_gray" in names


def test_build_variants_all_grayscale():
    img = _make_color()
    variants = build_variants(img, debug=False)
    for name, arr in variants:
        assert len(arr.shape) == 2, f"Variant {name!r} is not grayscale"
        assert arr.dtype == np.uint8
