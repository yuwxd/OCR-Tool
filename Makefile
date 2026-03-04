.PHONY: install install-dev test lint clean build dist

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt pytest flake8 black mypy pyinstaller

install-easyocr:
	pip install easyocr torch

test:
	pytest tests/ -v --tb=short

lint:
	flake8 ocr_tool/ --max-line-length=100 --ignore=E501
	black --check ocr_tool/

format:
	black ocr_tool/ main.py

clean:
	rm -rf build/ dist/ *.spec __pycache__ ocr_tool/__pycache__ .pytest_cache

build:
	pyinstaller \
		--onefile \
		--name ocr \
		--clean \
		main.py

dist: clean build
	@echo "Binary ready: dist/ocr"

run:
	python main.py $(ARGS)
