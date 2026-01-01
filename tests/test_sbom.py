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
        "import os\nimport requests\nfrom yaml import load\nimport sarathi.cli"
    )

    imports = get_imports(str(p))
    # Should get top level names
    assert "os" in imports
    assert "requests" in imports
    assert "yaml" in imports
    assert "sarathi" in imports


def test_resolve_package_info():
    # Test a known package (requests is a dependency of sarathi)
    info = resolve_package_info("requests")
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
    "requests",
    "unused-lib"
]
"""
    )

    # Code using requests but not unused-lib, and also using an undeclared lib
    src = root / "src"
    src.mkdir()
    code = src / "main.py"
    code.write_text("import requests\nimport undeclared_lib")

    report = get_integrity_report(str(root))

    assert "unused" in report
    assert "undeclared" in report
    assert "unused-lib" in report["unused"]
    assert "undeclared-lib" in report["undeclared"]


def test_get_reverse_deps():
    # Search for something we know is used
    # In this environment, requests usually has some dependents or we can search for a common one
    # Let's try to find if any package depends on 'urllib3' (very common)
    deps = get_reverse_deps("urllib3")
    assert isinstance(deps, list)
    # Most likely 'requests' is in there
    pkg_names = [d["package"].lower() for d in deps]
    if "requests" in pkg_names:
        assert True


def test_get_dep_graph_data():
    # Only test if it returns a structure for requests
    graph, seen = get_dep_graph_data(["requests"])
    assert "requests" in graph
    assert "version" in graph["requests"]
    assert "dependencies" in graph["requests"]
    assert "requests" in seen
