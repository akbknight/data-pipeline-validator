# Makefile — data-pipeline-validator
# ====================================
# Convenience targets for development and CI.

.PHONY: install run test lint clean help

## install   : install Python dependencies
install:
	pip install -r requirements.txt

## run        : execute the validation pipeline (generates validation_report.json)
run:
	python validate.py

## test       : run the test suite
test:
	python -m pytest tests/ -v

## lint       : check code style with flake8 (install separately if needed)
lint:
	python -m flake8 src/ tests/ validate.py --max-line-length=100

## clean      : remove Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

## help       : list all available make targets
help:
	@grep -E '^## ' Makefile | sed 's/## /  /'
