"""
Removes imports of names that don't exist in well-known libraries
(e.g. `from sqlalchemy import create_all`), when the file never uses them.
If the invented name IS used, it's left for the AI fixer.
"""

import ast
import importlib
import re

from app.services.completeness_checker import _norm

# Libraries safe to import inside ProtoCode for checking.
_CHECKABLE = {
    "sqlalchemy", "fastapi", "pydantic", "pydantic_settings", "starlette",
    "passlib", "jose", "jwt", "typing", "datetime", "os", "pathlib", "uuid", "json",
}


def fix_nonexistent_imports(files: list[dict]) -> list[dict]:
    for f in files:
        path = _norm(f["path"])
        if not path.startswith("backend/") or not path.endswith(".py"):
            continue
        try:
            tree = ast.parse(f["content"])
        except SyntaxError:
            continue

        lines = f["content"].split("\n")
        edits = []  # (start_line, end_line, replacement_or_None)

        for node in tree.body:
            if not (isinstance(node, ast.ImportFrom) and node.level == 0 and node.module):
                continue
            if node.module.split(".")[0] not in _CHECKABLE:
                continue
            try:
                module = importlib.import_module(node.module)
            except Exception:
                continue

            keep, removed = [], []
            for alias in node.names:
                name = alias.asname or alias.name
                exists = alias.name == "*" or hasattr(module, alias.name)
                used = len(re.findall(rf"\b{re.escape(name)}\b", f["content"])) > 1
                if exists or used:
                    keep.append(alias)
                else:
                    removed.append(alias.name)

            if not removed:
                continue
            if keep:
                names = ", ".join(
                    f"{a.name} as {a.asname}" if a.asname else a.name for a in keep
                )
                replacement = f"from {node.module} import {names}"
            else:
                replacement = None
            edits.append((node.lineno, node.end_lineno, replacement))
            print(f"[bad-import-fixer] {path}: removed non-existent {node.module}.{removed}")

        # Apply bottom-up so line numbers stay valid.
        for start, end, replacement in sorted(edits, reverse=True):
            lines[start - 1:end] = [replacement] if replacement else []
        if edits:
            f["content"] = "\n".join(lines)

    return files