"""
Deterministically scans generated Python files for imports and builds a
requirements.txt — doesn't rely on the LLM to remember/list dependencies correctly.
"""

import ast

# Map import name -> actual pip package name, for cases where they differ
IMPORT_TO_PACKAGE = {
    "jose": "python-jose[cryptography]",
    "jwt": "pyjwt",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "bcrypt": "bcrypt",
    "passlib": "passlib[bcrypt]",
    "bson": "pymongo",
    "rest_framework": "djangorestframework",
}

# Python stdlib modules — skip these, they don't go in requirements.txt
STDLIB_MODULES = {
    "os", "sys", "json", "re", "typing", "datetime", "time", "pathlib",
    "collections", "functools", "itertools", "uuid", "random", "math",
    "logging", "asyncio", "subprocess", "tempfile", "shutil", "enum",
}


def scan_python_dependencies(files: list) -> set:
    """
    files: list of {"path": str, "content": str} dicts (backend .py files)
    Returns a set of pip package names actually imported in the code.
    """
    local_names = _collect_local_module_names(files)
    packages = set()

    for file in files:
        if not file["path"].endswith(".py"):
            continue
        try:
            tree = ast.parse(file["content"])
        except SyntaxError:
            continue  # skip files that don't parse; syntax_checker already flags these

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split(".")[0]
                    _add_package(top_level, packages, local_names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level = node.module.split(".")[0]
                    _add_package(top_level, packages, local_names)

    return packages


def _collect_local_module_names(files: list) -> set:
    """
    Names that resolve to the project's own code, not an installable package:
    the stem of every .py file (database.py -> "database") and every folder
    that contains one (routers/auth.py -> "routers"). Generated projects
    routinely import their own files with absolute imports (`import database`,
    `from routers import auth`), which otherwise look identical to a real
    third-party import to an AST-based scanner.
    """
    names = set()
    for file in files:
        if not file["path"].endswith(".py"):
            continue
        parts = file["path"].split("/")
        stem = parts[-1][:-3]  # strip ".py"
        if stem != "__init__":
            names.add(stem)
        for part in parts[:-1]:
            if part not in ("backend", "frontend"):
                names.add(part)
    return names


def _add_package(module_name: str, packages: set, local_names: set):
    if module_name in STDLIB_MODULES:
        return
    if module_name.startswith("."):
        return
    if module_name in local_names:
        return
    packages.add(IMPORT_TO_PACKAGE.get(module_name, module_name))


def build_requirements_txt(files: list, backend_framework: str) -> str:
    """
    Returns full requirements.txt content, always including the base framework
    packages plus anything actually detected via import scanning.
    """
    base = {
        "FastAPI": {"fastapi", "uvicorn[standard]", "pydantic"},
        "Django": {"django", "djangorestframework"},
    }.get(backend_framework, set())

    detected = scan_python_dependencies(files)
    all_packages = sorted(base | detected)
    return "\n".join(all_packages) + "\n"
