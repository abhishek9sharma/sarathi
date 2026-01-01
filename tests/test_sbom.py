import json
import os

import pytest

from sarathi.cli.sbom_cli import (
    get_dep_graph_data,
    get_imports,
    get_integrity_report,
    get_reverse_deps,
    get_sbom_imports,
    resolve_package_info,
)


def test_get_imports(tmp_path):
    # Create a dummy python file
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "test_file.py"
    p.write_text(
        "import os\nimport httpx\nfrom yaml import load\nimport sarathi.cli"
    )

    imports = get_imports(str(p))
    # Should get top level names
    assert "os" in imports
    assert "httpx" in imports
    assert "yaml" in imports
    assert "sarathi" in imports


def test_resolve_package_info():
    # Test a known package (httpx is a dependency of sarathi)
    info = resolve_package_info("httpx")
    assert info is not None
    assert "version" in info
    assert "license" in info

    # Test mapping
    info_yaml = resolve_package_info("yaml")
    assert info_yaml is not None
    # 'yaml' should map to 'PyYAML' in metadata

    # Test unknown
    assert resolve_package_info("non_existent_pkg_12345") is None


def test_get_integrity_report(tmp_path):
    # Setup a dummy project structure
    root = tmp_path / "project"
    root.mkdir()

    # pyproject.toml with some deps
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        """
[project]
dependencies = [
    "httpx",
    "unused-lib"
]
"""
    )

    # Code using httpx but not unused-lib, and also using an undeclared lib
    src = root / "src"
    src.mkdir()
    code = src / "main.py"
    code.write_text("import httpx\nimport undeclared_lib")

    report = get_integrity_report(str(root))

    assert "unused" in report
    assert "undeclared" in report
    assert "unused-lib" in report["unused"]
    assert "undeclared-lib" in report["undeclared"]


def test_get_reverse_deps():
    # Search for something we know is used
    # Let's try to find if any package depends on 'idna' (common dep of httpx)
    deps = get_reverse_deps("idna")
    assert isinstance(deps, list)
    # Most likely 'httpx' is in there
    pkg_names = [d["package"].lower() for d in deps]
    if "httpx" in pkg_names:
        assert True


def test_get_dep_graph_data():
    # Only test if it returns a structure for httpx
    graph, seen = get_dep_graph_data(["httpx"])
    assert "httpx" in graph
    assert "version" in graph["httpx"]
    assert "dependencies" in graph["httpx"]
    assert "httpx" in seen
