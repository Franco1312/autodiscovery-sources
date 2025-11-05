.PHONY: venv install test run-sync clean help

help:
	@echo "Available targets:"
	@echo "  venv      - Create virtual environment"
	@echo "  install   - Install package and dependencies"
	@echo "  test      - Run tests"
	@echo "  run-sync  - Run sync all sources (fast mode)"
	@echo "  clean     - Clean build artifacts"

venv:
	python3.11 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

install:
	pip install --upgrade pip setuptools wheel
	pip install -e ".[dev]"
	@echo "Package installed"

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

run-sync:
	ads sync --all --fast

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

