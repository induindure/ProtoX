"""
Finds names used but never imported in generated backend Python files
(e.g. `models.User` without `from .. import models`) using pyflakes,
and adds the missing import when the name is a project module or a
common library name.
"""

import ast
from pathlib import PurePosixPath

from pyflakes import checker, messages

from app.services.completeness_checker import _norm
import difflib
import re

# Common library names the AI forgets to import.
_KNOWN_IMPORTS = {
    "Depends": "from fastapi import Depends",
    "HTTPException": "from fastapi import HTTPException",
    "APIRouter": "from fastapi import APIRouter",
    "status": "from fastapi import status",
    "Session": "from sqlalchemy.orm import Session",
    "BaseModel": "from pydantic import BaseModel",
    "Optional": "from typing import Optional",
    "List": "from typing import List",
    "Dict": "from typing import Dict",
    "Any": "from typing import Any",
    "datetime": "from datetime import datetime",
    "timedelta": "from datetime import timedelta",
    "os": "import os",
}

def _insert_imports(source: str, import_lines: list[str]) -> str:
    """Adds import lines after the last top-level import near the top."""
    lines = source.split("\n")
    insert_at = 0
    for i, line in enumerate(lines[:80]):
        if line.startswith(("import ", "from ")):
            insert_at = i + 1
        elif line.startswith(("def ", "class ", "@")):
            break
    lines[insert_at:insert_at] = import_lines
    return "\n".join(lines)

def _analyze(source: str, filename: str):
    """Returns (undefined_names, defined_names), or (set(), set()) on syntax errors."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return set(), set()

    result = checker.Checker(tree, filename=filename)
    undefined = {
        m.message_args[0]
        for m in result.messages
        if isinstance(m, messages.UndefinedName)
    }

    defined = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            defined.add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                defined.add((alias.asname or alias.name).split(".")[0])
    return undefined, defined


def fix_undefined_names(files: list[dict]) -> list[dict]:
    paths = {_norm(f["path"]) for f in files}

    def module_exists(folder: PurePosixPath, name: str) -> bool:
        return f"{folder}/{name}.py" in paths or f"{folder}/{name}/__init__.py" in paths

    for f in files:
        path = _norm(f["path"])
        if not path.startswith("backend/") or not path.endswith(".py"):
            continue
        if "import *" in f["content"]:
            continue

        undefined, defined = _analyze(f["content"], path)
        if not undefined:
            continue

        here = PurePosixPath(path).parent
        parent = here.parent
        new_imports = []
        renames = {}

        for name in sorted(undefined):
            if module_exists(here, name):
                new_imports.append(f"from . import {name}")
            elif module_exists(parent, name) and str(parent) != "backend":
                new_imports.append(f"from .. import {name}")
            elif name in _KNOWN_IMPORTS:
                new_imports.append(_KNOWN_IMPORTS[name])
            else:
                # A typo of a name defined in this file? (auth2_scheme -> oauth2_scheme)
                match = difflib.get_close_matches(name, sorted(defined), n=1, cutoff=0.8)
                if match:
                    renames[name] = match[0]

        content = f["content"]
        for wrong, right in renames.items():
            content = re.sub(rf"\b{re.escape(wrong)}\b", right, content)
        if renames:
            print(f"[undefined-name-fixer] {path}: fixed typos {renames}")

        if new_imports:
            content = _insert_imports(content, new_imports)
            print(f"[undefined-name-fixer] {path}: added {', '.join(new_imports)}")

        f["content"] = content

    return files