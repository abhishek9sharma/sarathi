#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "Sarathi Package Build Script"
echo "=========================================="

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Ensure build dependencies are installed
echo "Installing build dependencies..."
python -m pip install --upgrade pip
python -m pip install build wheel twine

# Run tests first
echo "Running tests..."
PYTHONPATH=src python -m pytest tests/ -v

# Build the package using pyproject.toml
echo "Building package..."
python -m build

# List built artifacts
echo ""
echo "Build complete! Artifacts:"
ls -lh dist/

echo ""
echo "To upload to PyPI:"
echo "  python -m twine upload dist/*"
echo ""
echo "To upload to TestPyPI:"
echo "  python -m twine upload --repository testpypi dist/*"