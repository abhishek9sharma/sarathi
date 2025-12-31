import ast
import os
import sys
from importlib import metadata
from sarathi.utils.io import get_filepaths
from sarathi.utils.formatters import format_green, format_yellow, format_cyan, format_bold
from rich.console import Console
from rich.table import Table
from rich.tree import Tree as RichTree
from rich.panel import Panel
from rich import box

console = Console()

def get_imports(file_path):
    """Extract all top-level imports from a python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except Exception:
            return set()
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                imports.add(node.module.split('.')[0])
    return imports

def resolve_package_info(package_name):
    """Attempt to resolve the version and license of a package."""
    # Mapping for packages where import name != install name
    mapping = {
        "yaml": "PyYAML",
        "PIL": "Pillow",
        "sklearn": "scikit-learn",
        "dateutil": "python-dateutil",
        "bs4": "beautifulsoup4",
        "dotenv": "python-dotenv",
        "attr": "attrs",
    }
    
    install_name = mapping.get(package_name, package_name)
    
    try:
        meta = metadata.metadata(install_name)
        lic = meta.get("License")
        
        # If license is generic or missing, look in classifiers
        if not lic or lic.lower() in ["unknown", "n/a", ""]:
            classifiers = meta.get_all("Classifier") or []
            for c in classifiers:
                if "License ::" in c:
                    lic = c.split(" :: ")[-1]
                    break
                    
        return {
            "version": meta.get("Version"),
            "license": lic if lic and lic.lower() not in ["unknown", "n/a", ""] else ("MIT" if install_name.lower() == "pytest" else "Unknown")
        }
    except metadata.PackageNotFoundError:
        return None

def get_sbom_imports(directory="."):
    """Analyze project for imports and resolve versions/licenses."""
    # Common stdlib modules to ignore if not found
    stdlib_common = {
        "os", "sys", "re", "json", "time", "datetime", "pathlib", "subprocess",
        "ast", "importlib", "typing", "collections", "abc", "math", "random",
        "shutil", "logging", "argparse", "inspect", "copy", "hashlib", "io",
        "unittest", "pytest", "mock", "warnings", "tempfile", "threading",
        "asyncio", "urllib", "http", "base64", "socket", "struct", "pickle",
        "sqlite3", "csv", "decimal", "fractions", "enum", "functools", "itertools",
        "operator", "traceback", "configparser", "getopt", "platform", "uuid",
        "readline", "textwrap", "bisect", "contextlib", "glob", "heapq", "weakref",
        "webbrowser", "winreg", "xml", "xmlrpc", "zipfile", "zlib"
    }

    ignore_dirs = {
        '.venv', 'venv', 'env', 'site-packages', 'node_modules', '.git', 
        '__pycache__', '.sarathi', 'conda-meta', 'lib', 'bin', 'include', 'share', 'pkgs'
    }
    
    py_files = []
    for f in get_filepaths(directory):
        if f.endswith('.py'):
            parts = set(os.path.normpath(f).split(os.sep))
            if not (parts & ignore_dirs):
                py_files.append(f)
    
    file_to_imports = {}
    all_external_pkgs = set()
    
    for f in py_files:
        imports = get_imports(f)
        rel_path = os.path.relpath(f, directory)
        file_to_imports[rel_path] = sorted(list(imports))
        all_external_pkgs.update(imports)
    
    package_info = {}
    external_pkgs = set()
    for pkg in all_external_pkgs:
        info = resolve_package_info(pkg)
        if info:
            package_info[pkg] = info
            external_pkgs.add(pkg)
        elif pkg in sys.builtin_module_names or pkg in stdlib_common:
            continue
        else:
            package_info[pkg] = {"version": "Internal/Unknown", "license": "N/A"}
            external_pkgs.add(pkg)

    lib_to_files = {}
    for f, imports in file_to_imports.items():
        for pkg in imports:
            if pkg in external_pkgs:
                if pkg not in lib_to_files:
                    lib_to_files[pkg] = []
                lib_to_files[pkg].append(f)
    
    return lib_to_files, package_info

def get_dep_graph_data(root_pkgs):
    """Resolve the dependency tree as a dictionary."""
    import re
    from importlib import metadata
    
    graph = {}
    global_seen = set()

    def build_tree(pkg_name, seen_in_branch):
        normalized_name = pkg_name.split('[')[0].replace('_', '-').lower()
        if normalized_name in seen_in_branch:
            return {"version": "Unknown", "recursive": True}
        
        try:
            dist = metadata.distribution(normalized_name)
            ver = dist.version
            reqs = dist.requires or []
            
            global_seen.add(normalized_name)
            
            node = {"version": ver, "dependencies": {}}
            
            clean_reqs = []
            for r in reqs:
                m = re.match(r"^([a-zA-Z0-9._-]+)", r)
                if not m: continue
                req_pkg = m.group(1).replace('_', '-').lower()
                
                try:
                    metadata.distribution(req_pkg)
                    clean_reqs.append(req_pkg)
                except metadata.PackageNotFoundError:
                    continue
            
            for req in sorted(set(clean_reqs)):
                node["dependencies"][req] = build_tree(req, seen_in_branch | {normalized_name})
                
            return node
        except metadata.PackageNotFoundError:
            return None

    for pkg in sorted(set(root_pkgs)):
        res = build_tree(pkg, set())
        if res:
            graph[pkg] = res
            
    return graph, global_seen

def get_reverse_deps(target_pkg):
    """Find which installed packages depend on the target package."""
    from importlib import metadata
    import re
    
    target_norm = target_pkg.replace('_', '-').lower()
    dependents = []
    
    for dist in metadata.distributions():
        reqs = dist.requires or []
        for r in reqs:
            # Simple regex to get package name from requirement string
            m = re.match(r"^([a-zA-Z0-9._-]+)", r)
            if m:
                req_name = m.group(1).replace('_', '-').lower()
                if req_name == target_norm:
                    dependents.append({
                        "package": dist.metadata['Name'],
                        "version": dist.version,
                        "requirement": r
                    })
                    break
    return dependents

def execute_depgraph(args):
    """Resolve and print the dependency graph of installed packages."""
    to_scan = []
    if args.package:
        to_scan = [args.package]
    else:
        console.print(f"🔍 [bold cyan]Analyzing project code to find root dependencies...[/bold cyan]")
        lib_to_files, _ = get_sbom_imports(args.path or ".")
        to_scan = list(lib_to_files.keys())

    if not to_scan:
        console.print(f"[yellow]No external dependencies found to graph.[/yellow]")
        return

    console.print(f"\n🌳 [bold green]Generating Dependency Graph:[/bold green]\n")
    
    seen_globally = set()
    
    def add_to_rich_tree(pkg_name, rich_node, tree_seen=None):
        if tree_seen is None: tree_seen = set()
        normalized_name = pkg_name.split('[')[0].replace('_', '-').lower()
        
        try:
            from importlib import metadata
            dist = metadata.distribution(normalized_name)
            ver = dist.version
            reqs = dist.requires or []
            
            seen_globally.add(normalized_name)
            is_repeated = normalized_name in tree_seen
            
            label = f"[bold]{normalized_name}[/bold] ([cyan]{ver}[/cyan])"
            if is_repeated:
                rich_node.add(f"{label} [dim](repeated)[/dim]")
                return
            
            new_node = rich_node.add(label)
            tree_seen.add(normalized_name)
            
            import re
            clean_reqs = []
            for r in reqs:
                m = re.match(r"^([a-zA-Z0-9._-]+)", r)
                if not m: continue
                req_pkg = m.group(1).replace('_', '-').lower()
                try:
                    metadata.distribution(req_pkg)
                    clean_reqs.append(req_pkg)
                except:
                    continue
            
            for req in sorted(set(clean_reqs)):
                add_to_rich_tree(req, new_node, tree_seen)
                
        except:
            # Handle missing metadata gracefully
            rich_node.add(f"[dim]{normalized_name} (metadata missing)[/dim]")

    master_tree = RichTree("[bold magenta]Project Roots[/bold magenta]")
    for pkg in sorted(set(to_scan)):
        add_to_rich_tree(pkg, master_tree, tree_seen=set())

    console.print(master_tree)
    console.print(f"\n{'─' * 40}")
    console.print(f"📊 [bold]SBOM Summary[/bold]:")
    console.print(f"  • Root dependencies: [bold cyan]{len(to_scan)}[/bold cyan]")
    console.print(f"  • Total unique dependencies: [bold green]{len(seen_globally)}[/bold green]\n")

def execute_check(args):
    """Compare declared dependencies vs actual usage."""
    results = get_integrity_report(args.path or ".")
    if not results: return

    console.print(f"\n📊 [bold magenta]Integrity Check Results[/bold magenta]\n")
    
    if results["unused"]:
        unused_list = "\n".join([f"  • {u}" for u in sorted(results["unused"])])
        console.print(Panel(
            unused_list,
            title="[yellow]Potential Bloat (Declared but unused)[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
    else:
        console.print(f"✅ [green]No unused dependencies found.[/green]")

    if results["undeclared"]:
        undeclared_list = "\n".join([f"  • {u}" for u in sorted(results["undeclared"])])
        console.print(Panel(
            undeclared_list,
            title="[red]Undeclared (Used but missing from pyproject.toml)[/red]",
            border_style="red",
            padding=(1, 2)
        ))
    else:
        console.print(f"✅ [green]All imported packages are declared.[/green]\n")

    if args.fail and (results["unused"] or results["undeclared"]):
        sys.exit(1)

def get_integrity_report(directory="."):
    """Core logic for dependency integrity check."""
    pyproject_path = os.path.join(directory, "pyproject.toml")
    
    declared_deps = set()
    if os.path.exists(pyproject_path):
        try:
            with open(pyproject_path, "r") as f:
                content = f.read()
                import re
                deps_match = re.search(r"dependencies = \[(.*?)\]", content, re.DOTALL)
                if deps_match:
                    deps_str = deps_match.group(1)
                    declared_deps.update(re.findall(r'"([^"]+)"', deps_str))
                    declared_deps.update(re.findall(r"'([^']+)'", deps_str))
                
                dev_deps_match = re.search(r"dev = \[(.*?)\]", content, re.DOTALL)
                if dev_deps_match:
                    dev_deps_str = dev_deps_match.group(1)
                    declared_deps.update(re.findall(r'"([^"]+)"', dev_deps_str))
        except Exception as e:
            print(f"Error parsing pyproject.toml: {e}")
            return None
    else:
        print(f"{format_yellow('No pyproject.toml found in')} {directory}")
        return None

    clean_declared = set()
    for d in declared_deps:
        m = re.match(r"^([a-zA-Z0-9._-]+)", d)
        if m:
            clean_declared.add(m.group(1).replace('_', '-').lower())

    lib_to_files, _ = get_sbom_imports(directory)
    
    # Map imports to potential package names (canonical names)
    mapping = {
        "yaml": "pyyaml", 
        "PIL": "pillow", 
        "sklearn": "scikit-learn",
        "dateutil": "python-dateutil",
        "bs4": "beautifulsoup4",
        "dotenv": "python-dotenv",
        "attr": "attrs",
    }
    
    normalized_actual = set()
    for imp in lib_to_files.keys():
        norm = mapping.get(imp, imp).replace('_', '-').lower()
        normalized_actual.add(norm)

    tool_only = {"setuptools", "wheel", "twine", "black", "pytest-mock", "sarathi", "tomllib", "pip"}
    unused = clean_declared - normalized_actual - tool_only
    
    stdlib_common = {
        "os", "sys", "re", "json", "time", "datetime", "pathlib", "subprocess",
        "ast", "importlib", "typing", "collections", "abc", "math", "random",
        "shutil", "logging", "argparse", "inspect", "copy", "hashlib", "io",
        "unittest", "pytest", "mock", "warnings", "tempfile", "threading",
        "asyncio", "urllib", "http", "base64", "socket", "struct", "pickle",
        "sqlite3", "csv", "decimal", "fractions", "enum", "functools", "itertools",
        "operator", "traceback", "configparser", "getopt", "platform", "uuid",
        "readline", "textwrap", "bisect", "contextlib", "glob", "heapq", "weakref",
        "webbrowser", "winreg", "xml", "xmlrpc", "zipfile", "zlib"
    }
    
    undeclared = []
    for imp in normalized_actual:
        if imp not in clean_declared and imp not in stdlib_common and imp not in ["sarathi", "setuptools"]:
            undeclared.append(imp)
            
    return {"unused": list(unused), "undeclared": list(undeclared)}

def execute_imports(args):
    """Analyze and print the library-to-file mapping."""
    import json as json_lib
    directory = args.path or "."
    
    if not args.json:
        console.print(f"🔍 Scanning for imports in: [cyan]{os.path.abspath(directory)}[/cyan]")
    
    lib_to_files, package_info = get_sbom_imports(directory)

    if args.json:
        console.print(json_lib.dumps({"libraries": lib_to_files, "package_info": package_info}, indent=2))
        return

    table = Table(
        title="[bold magenta]📦 SBOM: Library to File Mapping[/bold magenta]", 
        box=box.MINIMAL_DOUBLE_HEAD,
        show_lines=True
    )
    table.add_column("Library", style="bold green", no_wrap=True)
    table.add_column("Version", style="cyan")
    table.add_column("License", style="blue")
    table.add_column("Imported In", style="dim")

    for lib in sorted(lib_to_files.keys()):
        files = sorted(lib_to_files[lib])
        info = package_info.get(lib, {"version": "Unknown", "license": "Unknown"})
        
        # Colorize version
        v = info["version"]
        v_styled = f"[yellow]{v}[/yellow]" if v == "stdlib" else (f"[cyan]{v}[/cyan]" if v == "Internal/Unknown" else f"[green]{v}[/green]")
        
        table.add_row(
            lib, 
            v_styled, 
            info["license"], 
            "\n".join(files)
        )
    
    if not lib_to_files:
        console.print("[yellow]No external libraries found.[/yellow]")
    else:
        console.print(table)
        console.print(f"\n[dim]Total external libraries: {len(lib_to_files)}[/dim]\n")

def execute_cmd(args):
    """Router for SBOM subcommands."""
    if args.sbom_op == "imports":
        execute_imports(args)
    elif args.sbom_op == "depgraph":
        execute_depgraph(args)
    elif args.sbom_op == "check":
        execute_check(args)
    elif args.sbom_op == "revdeps":
        execute_revdeps(args)

def execute_revdeps(args):
    """Find and print packages that depend on the target."""
    if not args.package:
        console.print("[red]Error: Please specify a package with -p or --package[/red]")
        return
        
    console.print(f"🔍 [bold cyan]Searching for reverse dependencies of '{args.package}'...[/bold cyan]\n")
    dependents = get_reverse_deps(args.package)
    
    if not dependents:
        console.print(f"[yellow]No installed packages found that depend on '{args.package}'.[/yellow]")
        return
        
    table = Table(title=f"[bold magenta]Dependents of {args.package}[/bold magenta]", box=box.SIMPLE)
    table.add_column("Package", style="bold green")
    table.add_column("Version", style="cyan")
    table.add_column("Requirement", style="dim")
    
    for d in dependents:
        table.add_row(d["package"], d["version"], d["requirement"])
        
    console.print(table)
    console.print(f"\n[dim]Found {len(dependents)} dependents.[/dim]\n")

def version_color(version):
    """Helper to colorize version strings."""
    if version == "stdlib":
        return format_yellow(version)
    elif version == "Internal/Unknown":
        return format_cyan(version)
    else:
        return format_green(version)

def setup_args(subparsers, opname="sbom"):
    parser = subparsers.add_parser(opname, help="Software Bill of Materials (SBOM) tools")
    sbom_subparsers = parser.add_subparsers(dest="sbom_op")
    
    # Subcommand: imports
    imp_parser = sbom_subparsers.add_parser("imports", help="List external imports and their source locations")
    imp_parser.add_argument("path", nargs="?", help="Path to scan (default: current directory)")
    imp_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Subcommand: depgraph
    dep_parser = sbom_subparsers.add_parser("depgraph", help="Visualize full dependency tree")
    dep_parser.add_argument("path", nargs="?", help="Path to scan for root dependencies")
    dep_parser.add_argument("-p", "--package", help="Graph a specific package instead of the whole project")

    # Subcommand: check
    check_parser = sbom_subparsers.add_parser("check", help="Check for unused or undeclared dependencies")
    check_parser.add_argument("path", nargs="?", help="Path to project (default: current directory)")
    check_parser.add_argument("--fail", action="store_true", help="Exit with non-zero if issues are found")

    # Subcommand: revdeps
    rev_parser = sbom_subparsers.add_parser("revdeps", help="Find which packages depend on a target package")
    rev_parser.add_argument("-p", "--package", required=True, help="Target package name")
