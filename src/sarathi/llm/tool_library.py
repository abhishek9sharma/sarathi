"""
Enhanced tool library for code editing agents.

Provides tools for file operations, code analysis, AST parsing,
command execution, and test generation.
"""
import subprocess
import os
import ast
import json
from pathlib import Path
from typing import List, Dict, Optional
from sarathi.llm.tools import registry


# --- File System Tools ---

@registry.register(
    name="read_file",
    description="Read the complete contents of a file. Returns the file content as a string."
)
def read_file(filepath: str) -> str:
    """Read file contents."""
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@registry.register(
    name="write_file",
    description="Write content to a file. Creates the file if it doesn't exist, overwrites if it does."
)
def write_file(filepath: str, content: str) -> str:
    """Write content to a file."""
    try:
        # Create parent directories if needed
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@registry.register(
    name="list_files",
    description="List all files in a directory. Returns a JSON array of filenames."
)
def list_files(directory: str = ".") -> str:
    """List files in a directory."""
    try:
        if not os.path.isdir(directory):
            return f"Error listing files: Directory {directory} does not exist."
        files = os.listdir(directory)
        return json.dumps(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


@registry.register(
    name="find_python_files",
    description="Recursively find all Python files in a directory. Returns paths relative to the directory."
)
def find_python_files(directory: str = ".") -> str:
    """Find all Python files in directory tree."""
    try:
        if not os.path.isdir(directory):
            return f"Error finding Python files: Directory {directory} does not exist."
        py_files = []
        for root, dirs, files in os.walk(directory):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.venv', 'node_modules']]
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), directory)
                    py_files.append(rel_path)
        return json.dumps(py_files)
    except Exception as e:
        return f"Error finding Python files: {str(e)}"


# --- Git Tools ---

@registry.register(
    name="get_git_diff",
    description="Get staged changes in the current git repository."
)
def get_git_diff() -> str:
    """Get git diff for staged changes."""
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True, text=True
    )
    return result.stdout


@registry.register(
    name="get_git_status",
    description="Get git status showing modified, staged, and untracked files."
)
def get_git_status() -> str:
    """Get git status."""
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True
    )
    return result.stdout


# --- Code Analysis Tools ---

@registry.register(
    name="parse_python_ast",
    description="Parse a Python file and return AST information including classes, functions, and their signatures."
)
def parse_python_ast(filepath: str) -> str:
    """Parse Python file and extract structure."""
    try:
        with open(filepath, "r") as f:
            code = f.read()
        
        tree = ast.parse(code)
        structure = {
            "classes": [],
            "functions": [],
            "imports": []
        }
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                structure["classes"].append({
                    "name": node.name,
                    "methods": methods,
                    "lineno": node.lineno
                })
            elif isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                structure["functions"].append({
                    "name": node.name,
                    "args": args,
                    "lineno": node.lineno
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(alias.name)
                else:
                    module = node.module or ""
                    for alias in node.names:
                        structure["imports"].append(f"{module}.{alias.name}")
        
        return json.dumps(structure, indent=2)
    except Exception as e:
        return f"Error parsing AST: {str(e)}"


@registry.register(
    name="get_function_code",
    description="Extract the source code of a specific function from a Python file."
)
def get_function_code(filepath: str, function_name: str) -> str:
    """Get source code of a specific function."""
    try:
        with open(filepath, "r") as f:
            code = f.read()
        
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return ast.unparse(node)
        
        return f"Function '{function_name}' not found in {filepath}"
    except Exception as e:
        return f"Error extracting function: {str(e)}"


# --- Command Execution Tools ---

@registry.register(
    name="run_command",
    description="Run a shell command and return stdout, stderr, and exit code. Use for running tests, linters, etc."
)
def run_command(command: str) -> str:
    """Run a shell command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        response = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        if result.returncode != 0:
            response["error"] = f"Command failed with exit code {result.returncode}"
        return json.dumps(response)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Command timed out after 30 seconds"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@registry.register(
    name="run_pytest",
    description="Run pytest on a specific test file or directory. Returns test results."
)
def run_pytest(path: str) -> str:
    """Run pytest on a file or directory."""
    try:
        result = subprocess.run(
            ["pytest", path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60
        )
        return json.dumps({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "passed": result.returncode == 0
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Tests timed out after 60 seconds"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- Test Generation Helpers ---

@registry.register(
    name="check_test_exists",
    description="Check if a test file exists for a given source file. Returns the test file path if it exists."
)
def check_test_exists(source_file: str) -> str:
    """Check if test file exists for source file."""
    try:
        # Common test patterns
        path = Path(source_file)
        possible_test_paths = [
            path.parent / f"test_{path.name}",
            path.parent / "tests" / f"test_{path.name}",
            Path("tests") / path.parent / f"test_{path.name}",
            Path("tests") / f"test_{path.name}",
        ]
        
        for test_path in possible_test_paths:
            if test_path.exists():
                return json.dumps({
                    "exists": True,
                    "path": str(test_path)
                })
        
        return json.dumps({
            "exists": False,
            "suggested_path": str(Path("tests") / f"test_{path.name}")
        })
    except Exception as e:
        return f"Error checking test file: {str(e)}"


@registry.register(
    name="get_project_structure",
    description="Get an overview of the project structure including directories and Python files."
)
def get_project_structure(root_dir: str = ".") -> str:
    """Get project structure."""
    try:
        if not os.path.isdir(root_dir):
            return f"Error getting project structure: Directory {root_dir} does not exist."
        structure = {
            "root": root_dir,
            "directories": [],
            "python_files": []
        }
        
        for root, dirs, files in os.walk(root_dir):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.venv', 'node_modules', '.pytest_cache']]
            
            rel_root = os.path.relpath(root, root_dir)
            if rel_root != ".":
                structure["directories"].append(rel_root)
            
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                    structure["python_files"].append(rel_path)
        
        return json.dumps(structure, indent=2)
    except Exception as e:
        return f"Error getting project structure: {str(e)}"
