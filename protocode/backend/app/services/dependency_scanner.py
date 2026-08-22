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
                    _add_package(top_level, packages)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level = node.module.split(".")[0]
                    _add_package(top_level, packages)

    return packages


def _add_package(module_name: str, packages: set):
    if module_name in STDLIB_MODULES:
        return
    if module_name.startswith("."):
        return  # relative import, part of the project itself
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