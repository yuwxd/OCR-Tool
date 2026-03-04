#!/usr/bin/env python3

import sys

sys.argv = [sys.argv[0]] + [a.strip('"').strip("'") for a in sys.argv[1:]]

from ocr_tool.cli import app

if __name__ == "__main__":
    app()
