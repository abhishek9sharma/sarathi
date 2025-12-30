import pytest
import os
import json
from unittest import mock
from pathlib import Path
from sarathi.llm.tool_library import (
    read_file,
    write_file,
    list_files,
    find_python_files,
    get_git_diff,
    get_git_status,
    parse_python_ast,
    get_function_code,
    run_command,
    run_pytest,
    check_test_exists,
    get_project_structure
)


# --- Fixtures ---
@pytest.fixture
def sample_directory(tmp_path):
    # Create a temporary directory with some files
    (tmp_path / "file1.py").write_text("print('Hello World')")
    (tmp_path / "file2.txt").write_text("Just a text file")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir/file3.py").write_text("print('Subdirectory file')")
    return tmp_path


# --- Tests for File System Tools ---

def test_read_file(tmp_path):
    """Test reading a file successfully."""
    file_path = tmp_path / "test.txt"
    content = "Hello, world!"
    file_path.write_text(content)
    assert read_file(str(file_path)) == content


def test_read_file_error():
    """Test reading a non-existent file."""
    assert "Error reading file" in read_file("non_existent_file.txt")


def test_write_file(tmp_path):
    """Test writing content to a file."""
    file_path = tmp_path / "test.txt"
    content = "Hello, world!"
    response = write_file(str(file_path), content)
    assert response == f"Successfully wrote to {file_path}"
    assert file_path.read_text() == content


def test_write_file_error(mocker):
    """Test writing to a file with an invalid path."""
    mocker.patch("pathlib.Path.mkdir", side_effect=Exception("Mocked error"))
    response = write_file("/invalid_path/test.txt", "content")
    assert "Error writing file" in response


def test_list_files(sample_directory):
    """Test listing files in a directory."""
    files = json.loads(list_files(str(sample_directory)))
    assert set(files) == {"file1.py", "file2.txt", "subdir"}


def test_list_files_error():
    """Test listing files in a non-existent directory."""
    assert "Error listing files" in list_files("/non_existent_directory")


def test_find_python_files(sample_directory):
    """Test finding Python files recursively."""
    py_files = json.loads(find_python_files(str(sample_directory)))
    assert set(py_files) == {"file1.py", "subdir/file3.py"}


def test_find_python_files_error():
    """Test finding Python files in a non-existent directory."""
    assert "Error finding Python files" in find_python_files("/non_existent_directory")


# --- Tests for Git Tools ---

def test_get_git_diff(mocker):
    """Test getting git diff for staged changes."""
    mocker.patch("subprocess.run", return_value=mock.Mock(stdout="diff --git a/file b/file"))
    assert "diff --git a/file b/file" in get_git_diff()


def test_get_git_status(mocker):
    """Test getting git status."""
    mocker.patch("subprocess.run", return_value=mock.Mock(stdout=" M file.py"))
    assert " M file.py" in get_git_status()


# --- Tests for Code Analysis Tools ---

def test_parse_python_ast(tmp_path):
    """Test parsing a Python file to extract AST structure."""
    file_path = tmp_path / "test.py"
    file_path.write_text("""
class TestClass:
    def method(self):
        pass

def function():
    pass
""")
    structure = json.loads(parse_python_ast(str(file_path)))
    assert structure == {
        "classes": [{"name": "TestClass", "methods": ["method"], "lineno": 2}],
        "functions": [{"name": "function", "args": [], "lineno": 6}],
        "imports": []
    }


def test_parse_python_ast_error():
    """Test parsing a non-existent file for AST."""
    assert "Error parsing AST" in parse_python_ast("/non_existent_file.py")


def test_get_function_code(tmp_path):
    """Test extracting source code of a specific function."""
    file_path = tmp_path / "test.py"
    file_path.write_text("""
def function():
    return True
""")
    function_code = get_function_code(str(file_path), "function")
    assert "def function():\n    return True" in function_code


def test_get_function_code_not_found(tmp_path):
    """Test extracting source code of a non-existent function."""
    file_path = tmp_path / "test.py"
    file_path.write_text("")
    assert "Function 'non_existent' not found" in get_function_code(str(file_path), "non_existent")


# --- Tests for Command Execution Tools ---

def test_run_command(mocker):
    """Test running a shell command."""
    mocker.patch("subprocess.run", return_value=mock.Mock(stdout="output", stderr="", returncode=0))
    result = json.loads(run_command("echo 'hello'"))
    assert result == {"stdout": "output", "stderr": "", "returncode": 0}


def test_run_command_error():
    """Test running an invalid shell command."""
    result = json.loads(run_command("invalid_command"))
    assert "error" in result


# --- Tests for Test Generation Helpers ---

def test_check_test_exists(mocker):
    """Test checking if a test file exists."""
    mocker.patch("pathlib.Path.exists", return_value=True)
    result = json.loads(check_test_exists("/path/to/source.py"))
    assert result["exists"] is True


def test_check_test_exists_not_found(mocker):
    """Test checking if a test file does not exist."""
    mocker.patch("pathlib.Path.exists", return_value=False)
    result = json.loads(check_test_exists("/path/to/source.py"))
    assert result["exists"] is False


def test_get_project_structure(tmp_path):
    """Test getting project structure."""
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1/file1.py").write_text("")
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2/file2.py").write_text("")
    structure = json.loads(get_project_structure(str(tmp_path)))
    assert "dir1" in structure["directories"]
    assert "dir2" in structure["directories"]
    assert "dir1/file1.py" in structure["python_files"]
    assert "dir2/file2.py" in structure["python_files"]


def test_get_project_structure_error():
    """Test getting project structure for a non-existent directory."""
    assert "Error getting project structure" in get_project_structure("/non_existent_directory")
