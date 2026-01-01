.PHONY: help clean venv install test build format

# Variables
VENV_DIR = .venv
UV := $(shell command -v uv 2> /dev/null)

# Logic to use uv for faster execution/installation if available
ifneq ($(UV),)
    PYTHON_CMD = uv run python
    PIP_CMD = uv pip install --python $(VENV_DIR)
    VENV_CMD = uv venv
else
    PYTHON_CMD = $(VENV_DIR)/bin/python
    PIP_CMD = $(VENV_DIR)/bin/pip install
    VENV_CMD = python3 -m venv
endif

PYTEST = $(VENV_DIR)/bin/pytest
BLACK = $(VENV_DIR)/bin/black
ISORT = $(VENV_DIR)/bin/isort

help:
	@echo "Sarathi - Makefile Commands"
	@echo "============================"
	@echo "make venv      - Create a virtual environment"
	@echo "make install   - Install dependencies (uses uv if available)"
	@echo "make test      - Run tests"
	@echo "make format    - Format code"
	@echo "make clean     - Remove artifacts"
	@echo "make build     - Full clean, install, and test cycle"

venv:
	@echo "Creating virtual environment..."
	$(VENV_CMD) $(VENV_DIR)

install: venv
	@echo "Installing dependencies..."
ifneq ($(UV),)
	@echo "Using system uv..."
	$(PIP_CMD) -e .[dev]
else
	@echo "System uv not found. Installing uv in venv for faster setup..."
	$(VENV_DIR)/bin/pip install uv
	$(VENV_DIR)/bin/uv pip install -e .[dev]
endif

test:
	@echo "Running tests..."
	$(PYTHON_CMD) -m pytest tests/ -v

format:
	@echo "Formatting code..."
	$(PYTHON_CMD) -m black src/ tests/
	$(PYTHON_CMD) -m isort src/ tests/
	@echo "Formatting complete"

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
build: clean install test
	@echo "Build complete!"
