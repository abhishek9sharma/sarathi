import os
import tempfile
from unittest.mock import MagicMock

import pytest

from sarathi.utils.io import get_filepaths, is_valid_directory, is_valid_file, read_file


@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Test content\nLine 2")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with files"""
    temp_dir = tempfile.mkdtemp()

    # Create some test files
    with open(os.path.join(temp_dir, "file1.py"), "w") as f:
        f.write("# Python file 1")

    with open(os.path.join(temp_dir, "file2.py"), "w") as f:
        f.write("# Python file 2")

    with open(os.path.join(temp_dir, "__init__.py"), "w") as f:
        f.write("# Init file")

    with open(os.path.join(temp_dir, "test.pyc"), "w") as f:
        f.write("# Compiled file")

    yield temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)


def test_read_file(temp_file):
    """Test reading file content"""
    content = read_file(temp_file)
    assert content == "Test content\nLine 2"


def test_read_file_nonexistent():
    """Test reading non-existent file raises error"""
    with pytest.raises(FileNotFoundError):
        read_file("/nonexistent/path/file.txt")


def test_is_valid_file_success(temp_file):
    """Test validation of existing file"""
    mock_parser = MagicMock()
    result = is_valid_file(mock_parser, temp_file)
    assert result == temp_file
    mock_parser.error.assert_not_called()


def test_is_valid_file_failure():
    """Test validation of non-existent file"""
    mock_parser = MagicMock()
    is_valid_file(mock_parser, "/nonexistent/file.txt")
    mock_parser.error.assert_called_once()


def test_is_valid_directory_success(temp_dir):
    """Test validation of existing directory"""
    mock_parser = MagicMock()
    result = is_valid_directory(mock_parser, temp_dir)
    assert result == temp_dir
    mock_parser.error.assert_not_called()


def test_is_valid_directory_failure():
    """Test validation of non-existent directory"""
    mock_parser = MagicMock()
    is_valid_directory(mock_parser, "/nonexistent/directory")
    mock_parser.error.assert_called_once()


def test_get_filepaths_default(temp_dir):
    """Test getting file paths with default ignores"""
    paths = get_filepaths(temp_dir)

    # Should include file1.py and file2.py
    # Should exclude __init__.py and test.pyc
    assert len(paths) == 2

    filenames = [os.path.basename(p) for p in paths]
    assert "file1.py" in filenames
    assert "file2.py" in filenames
    assert "__init__.py" not in filenames
    assert "test.pyc" not in filenames


def test_get_filepaths_custom_ignore(temp_dir):
    """Test getting file paths with custom ignore patterns"""
    paths = get_filepaths(temp_dir, ignore_files=[], ignore_extensions=[])

    # Should include all files when no ignores
    assert len(paths) >= 3

    filenames = [os.path.basename(p) for p in paths]
    assert "__init__.py" in filenames


def test_get_filepaths_empty_directory():
    """Test getting file paths from empty directory"""
    temp_dir = tempfile.mkdtemp()
    try:
        paths = get_filepaths(temp_dir)
        assert paths == []
    finally:
        os.rmdir(temp_dir)
