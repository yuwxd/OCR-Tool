#!/usr/bin/env python3
"""
OCR Tool — entry point.

Usage:
    python main.py image.png
    python main.py image.png --lang pol --format txt --debug
    python main.py --dir ./screenshots/ --recursive
"""

import sys

# Drag-and-drop on Windows: strip surrounding quotes from all args
sys.argv = [sys.argv[0]] + [a.strip('"').strip("'") for a in sys.argv[1:]]

from ocr_tool.cli import app

if __name__ == "__main__":
    app()
