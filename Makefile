.PHONY: help clean venv install test build format

# Variables
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest

help:
	@echo "Sarathi - Makefile Commands"
	@echo "============================"
	@echo "make venv      - Create a virtual environment"
	@echo "make install   - Install dependencies in venv"
	@echo "make test      - Run tests in venv"
	@echo "make format    - Format code with black and isort"
	@echo "make clean     - Remove build artifacts and venv"
	@echo "make build     - Clean, create venv, install deps, and run tests"

venv:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "Virtual environment created at $(VENV_DIR)"

install: venv
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]
	@echo "Dependencies installed"

test: install
	@echo "Running tests..."
	PYTHONPATH=src $(PYTEST) tests/ -v
	@echo "Tests completed"

format:
	@echo "Formatting code..."
	black src/ tests/
	isort src/ tests/
	@echo "Code formatted"

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete"

build: clean venv install test
	@echo "Build complete! All tests passed."
