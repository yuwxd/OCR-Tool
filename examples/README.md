# Examples

Place your test images in this folder and run:

```bash
# Single image
python main.py examples/sample.png

# All images in this folder
python main.py --dir examples/

# With debug output to see every preprocessing pass
python main.py examples/sample.png --debug

# Save result to txt
python main.py examples/sample.png --format txt
```

## Sample output

```
╭─────────────────────────────────────────╮
│  OCR Tool  — Advanced text extraction   │
╰─────────────────────────────────────────╯

──────────────── sample.png ────────────────
Engine: tesseract  |  Confidence: 91.4%  |  Words: 42  |  Chars: 218  |  312ms

╭─── Extracted text ──────────────────────╮
│                                         │
│  Hello World                            │
│  This is a sample OCR result.           │
│                                         │
╰─────────────────────────────────────────╯
```
