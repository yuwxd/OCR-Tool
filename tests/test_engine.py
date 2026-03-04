from ocr_tool.engine import OCRResult


def _make_result(text: str, confidence: float, word_count: int) -> OCRResult:
    return OCRResult(
        text=text,
        confidence=confidence,
        engine="tesseract",
        psm_mode=6,
        variant="otsu",
        word_count=word_count,
        char_count=len(text),
        elapsed_ms=50.0,
    )


def test_score_empty_text():
    r = _make_result("", 90.0, 0)
    assert r.score == 0.0


def test_score_higher_confidence_wins():
    low = _make_result("hello world", 40.0, 2)
    high = _make_result("hello world", 90.0, 2)
    assert high.score > low.score


def test_score_more_words_bonus():
    few = _make_result("hi", 80.0, 1)
    many = _make_result("the quick brown fox jumped over the lazy dog", 80.0, 9)
    assert many.score > few.score


def test_summary_contains_engine():
    r = _make_result("test", 75.0, 1)
    assert "tesseract" in r.summary()
    assert "75.0" in r.summary()
