from setuptools import setup, find_packages
from pathlib import Path

README = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="ocr-tool",
    version="1.0.0",
    description="Advanced OCR — extract text from images with multi-pass Tesseract preprocessing",
    long_description=README,
    long_description_content_type="text/markdown",
    author="o9q",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "pytesseract>=0.3.10",
        "Pillow>=10.0.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "typer>=0.9.0",
        "rich>=13.5.0",
        "pyperclip>=1.8.2",
    ],
    extras_require={
        "easyocr": [
            "easyocr>=1.7.0",
            "torch>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ocr=ocr_tool.cli:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
)
