# OCR Tool

[![CI](https://github.com/o9q/ocr-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/o9q/ocr-tool/actions/workflows/ci.yml)
[![Release](https://github.com/o9q/ocr-tool/actions/workflows/release.yml/badge.svg)](https://github.com/o9q/ocr-tool/actions/workflows/release.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Advanced command-line OCR (Optical Character Recognition) tool.  
Extracts text from images using a multi-pass preprocessing pipeline built on top of Tesseract — reliably detects even very small details without producing false text.

---

## Features

- **Multi-pass OCR** — tests 6 preprocessing variants × 6 PSM modes per image, selects the best result automatically
- **Fine detail detection** — smart upscaling, CLAHE contrast enhancement, adaptive binarization and deskew for small or low-quality text
- **No false positives** — results are scored by confidence × word count; low-confidence output is suppressed or flagged
- **Drag-and-drop support** — drop an image onto the terminal window or binary
- **Multi-format input** — PNG, JPEG, TIFF, BMP, GIF, WebP, ICO, PPM and more
- **Batch processing** — process entire directories with `--dir`
- **Multiple output formats** — print to terminal, save as `.txt` or `.json`
- **Clipboard copy** — `--clipboard` to instantly paste the result
- **Language selection** — any Tesseract language pack (`eng`, `pol`, `deu`, `fra`, …)
- **Optional EasyOCR** — deep-learning fallback for curved, handwritten, or very complex text
- **Clean debug mode** — `--debug` shows every preprocessing step and per-pass confidence scores
- **Cross-platform** — Windows, Linux, macOS

---

## How it works

```
Image file
    │
    ▼
 Load & decode ──── supports 13+ formats, handles transparency
    │
    ▼
 Grayscale conversion
    │
    ▼
 Smart upscaling ─── scales up images smaller than 800 px (up to 4×, Lanczos)
    │
    ▼
 Deskew ────────────── detects text angle, corrects rotation
    │
    ▼
 Denoising ─────────── fastNlMeansDenoising (strong) or Gaussian blur (large images)
    │
    ▼
 CLAHE ─────────────── adaptive histogram equalization for local contrast
    │
    ▼
 Build 6 variants:
    ├── Otsu binarization         (global threshold, clean backgrounds)
    ├── Adaptive threshold        (uneven lighting, shadows)
    ├── Inverted Otsu             (white text on dark background)
    ├── Enhanced grayscale        (Tesseract auto-binarize)
    ├── Morphological close       (connects broken characters)
    └── Sharpened                 (fine hairline text)
    │
    ▼
 Tesseract OCR (each variant × 6 PSM modes = up to 36 passes)
    │
    ├── Score each pass: confidence% × word_count_weight
    └── Select highest-scoring result
    │
    ▼  (optional)
 EasyOCR fallback ─── if Tesseract confidence < 40%, deep-learning model runs
    │
    ▼
 Output: terminal / .txt / .json / clipboard
```

---

## Quick start

### 1. Install Tesseract

Tesseract is the OCR engine. Install it for your OS:

**Windows:**
```
https://github.com/UB-Mannheim/tesseract/wiki
```
Download and run the installer. During setup, select any additional languages you need.  
Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**Linux (Debian/Ubuntu):**
```bash
sudo apt install tesseract-ocr
# Add language packs:
sudo apt install tesseract-ocr-pol   # Polish
sudo apt install tesseract-ocr-deu   # German
```

**Linux (Arch):**
```bash
sudo pacman -S tesseract tesseract-data-eng tesseract-data-pol
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang   # all languages
```

### 2. Install Python dependencies

```bash
git clone https://github.com/o9q/ocr-tool.git
cd ocr-tool
pip install -r requirements.txt
```

Or install as a package:
```bash
pip install -e .
```

### 3. Run it

```bash
python main.py screenshot.png
```

---

## Usage

```
ocr [OPTIONS] [IMAGES]...
```

### Arguments

| Argument | Description |
|----------|-------------|
| `IMAGES` | One or more image files. Supports drag-and-drop. |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--dir PATH` | `-d` | — | Process all images in a directory |
| `--recursive` | `-r` | off | Search `--dir` recursively |
| `--lang CODE` | `-l` | `eng` | Tesseract language (e.g. `pol`, `deu`, `fra`) |
| `--psm MODES` | | all | PSM modes to test, comma-separated (e.g. `6,11`) |
| `--format` | `-f` | `none` | Output: `none` \| `txt` \| `json` \| `both` |
| `--output-dir PATH` | `-o` | same dir | Where to write output files |
| `--clipboard` | `-c` | off | Copy result to clipboard |
| `--easyocr` | `-e` | off | Enable EasyOCR deep-learning fallback |
| `--no-meta` | | off | Hide engine/confidence metadata |
| `--debug` | | off | Show preprocessing steps and per-pass scores |
| `--version` | `-v` | | Print version and exit |

---

## Examples

### Basic usage

```bash
# Read a single image
python main.py receipt.jpg

# Polish text
python main.py dokument.png --lang pol

# Multiple files
python main.py scan1.png scan2.png scan3.tiff
```

### Drag-and-drop

**Windows:** Drag an image file from Explorer and drop it onto the CMD window.  
**Linux/macOS:** Drag a file into the terminal — the path is pasted automatically.

```bash
python main.py C:\Users\you\Desktop\screenshot.png
```

### Batch directory processing

```bash
# All images in folder
python main.py --dir ./scans/

# All images recursively, save results as JSON
python main.py --dir ./archive/ --recursive --format json --output-dir ./results/
```

### Save output

```bash
# Save as plain text
python main.py image.png --format txt

# Save as JSON with metadata
python main.py image.png --format json

# Save both
python main.py image.png --format both

# Custom output location
python main.py image.png --format txt --output-dir ~/Documents/
```

### Clipboard

```bash
python main.py screenshot.png --clipboard
# → result instantly available in Ctrl+V
```

### Debug / verbose mode

```bash
python main.py difficult.png --debug
```

Shows:
- Image dimensions before and after upscaling
- Each preprocessing variant name
- Tesseract pass results (PSM mode, variant, confidence, word count, score)
- Which variant was selected and why

### Fine-tune PSM

PSM (Page Segmentation Mode) controls how Tesseract analyses the image layout.  
By default, all modes are tested. You can restrict to specific ones for speed:

```bash
# Single column of text
python main.py scan.png --psm 4

# Sparse text (labels, captions)
python main.py label.jpg --psm 11,12

# Raw single line
python main.py line.png --psm 13
```

| PSM | Description |
|-----|-------------|
| 3 | Fully automatic (default) |
| 4 | Single column |
| 6 | Uniform block of text |
| 11 | Sparse text |
| 12 | Sparse text + OSD |
| 13 | Raw line |

### EasyOCR (deep learning)

EasyOCR provides better accuracy for curved text, handwriting, and complex fonts.  
It activates automatically when Tesseract confidence falls below 40%, or manually:

```bash
# Install first (large download, ~1.5 GB)
pip install easyocr torch

# Enable
python main.py handwritten.jpg --easyocr
```

---

## JSON output format

```json
{
  "source": "receipt.jpg",
  "timestamp": "2025-03-01T12:00:00Z",
  "engine": "tesseract",
  "confidence": 91.4,
  "psm_mode": 6,
  "variant": "adaptive",
  "word_count": 42,
  "char_count": 218,
  "elapsed_ms": 312.5,
  "warnings": [],
  "text": "Total: $24.99\nThank you for your purchase."
}
```

---

## Build standalone binary

Create a single executable file (no Python required to run):

```bash
pip install pyinstaller
pyinstaller --onefile --name ocr main.py
# Result: dist/ocr  (or dist/ocr.exe on Windows)
```

Or use the Makefile:

```bash
make build
```

---

## Supported image formats

| Format | Extension |
|--------|-----------|
| PNG | `.png` |
| JPEG | `.jpg`, `.jpeg` |
| TIFF | `.tiff`, `.tif` |
| Bitmap | `.bmp` |
| GIF | `.gif` |
| WebP | `.webp` |
| ICO | `.ico` |
| Portable bitmap | `.ppm`, `.pgm`, `.pbm`, `.pnm` |

---

## Language support

List installed Tesseract languages:

```bash
tesseract --list-langs
```

Common codes:

| Code | Language |
|------|----------|
| `eng` | English |
| `pol` | Polish |
| `deu` | German |
| `fra` | French |
| `spa` | Spanish |
| `ita` | Italian |
| `rus` | Russian |
| `chi_sim` | Chinese Simplified |
| `jpn` | Japanese |

Install additional packs:
- **Linux:** `sudo apt install tesseract-ocr-<code>`
- **Windows:** re-run the Tesseract installer and select additional languages
- **macOS:** `brew install tesseract-lang`

---

## Troubleshooting

**`TesseractNotFoundError`**  
Tesseract is not in PATH.  
- Windows: add `C:\Program Files\Tesseract-OCR` to your system PATH  
- Or set the path in code: `pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`

**Low confidence / empty output**  
- Try `--debug` to see which variants and PSM modes were attempted  
- Try `--easyocr` for complex or unusual images  
- Ensure the image is not heavily blurred or extremely low resolution (< 50px)

**Wrong language characters**  
- Specify the correct language with `--lang`  
- Check installed packs: `tesseract --list-langs`

---

## Development

```bash
# Install dev dependencies
make install-dev

# Run tests
make test

# Lint and format
make lint
make format
```

---

## License

MIT — see [LICENSE](LICENSE).

---

*Created by [yuw](https://github.com/yuwxd)*

