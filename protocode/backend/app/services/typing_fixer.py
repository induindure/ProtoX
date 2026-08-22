"""
Deterministically detects typing constructs (Optional, List, Dict, etc.) used
in generated code without being imported, and injects the missing import.
Doesn't rely on the LLM to remember every 'from typing import ...' line.
"""

import ast

TYPING_NAMES = {
    "Optional", "List", "Dict", "Union", "Tuple", "Any", "Callable",
    "Set", "FrozenSet", "Iterable", "Iterator", "Sequence", "Mapping",
    "Type", "TypeVar", "Generic", "Literal", "ClassVar", "Final",
}


def fix_missing_typing_imports(files: list) -> list:
    """
    files: list of {"path": str, "content": str} dicts
    Mutates and returns the same list, patching any .py file that uses
    a typing construct without importing it.
    """
    for file in files:
        if not file["path"].endswith(".py"):
            continue

        content = file["content"]
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue  # already flagged elsewhere, skip

        used_names = {
            node.id for node in ast.walk(tree)
            if isinstance(node, ast.Name) and node.id in TYPING_NAMES
        }
        # also catch typing constructs used as attribute access target isn't relevant here,
        # Name nodes cover `Optional[str]` since `Optional` itself is a Name node

        if not used_names:
            continue

        imported_names = _get_imported_names(tree, "typing")
        missing = used_names - imported_names

        if missing:
            import_line = f"from typing import {', '.join(sorted(missing))}\n"
            file["content"] = import_line + content

    return files


def _get_imported_names(tree: ast.AST, module: str) -> set:
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    return imported