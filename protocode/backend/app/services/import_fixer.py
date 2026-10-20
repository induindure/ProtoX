"""
Fixes relative imports that point at the wrong package level:
- `from .. import x` when x is actually in the same folder  -> `from . import x`
- `from .x import y` when x is actually one folder up       -> `from ..x import y`
Only rewrites when the current form is guaranteed to fail and the
other form points at a file that really exists.
"""

import re
from pathlib import PurePosixPath

_PARENT_IMPORT = re.compile(r"^(\s*)from \.\.(\w*) import (.+)$", re.MULTILINE)
_SIBLING_IMPORT = re.compile(r"^(\s*)from \.(\w*) import (.+)$", re.MULTILINE)


def _norm(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def _targets(module: str, names: str) -> list[str]:
    if module:
        return [module]
    return [
        n.split(" as ")[0].strip()
        for n in names.strip("() \r").split(",")
        if n.strip()
    ]


def fix_relative_imports(files: list[dict]) -> list[dict]:
    paths = {_norm(f["path"]) for f in files}

    def exists(folder: PurePosixPath, name: str) -> bool:
        base = "" if str(folder) == "." else f"{folder}/"
        return (
            f"{base}{name}.py" in paths
            or f"{base}{name}/__init__.py" in paths
            or any(p.startswith(f"{base}{name}/") for p in paths)
        )

    for f in files:
        path = PurePosixPath(_norm(f["path"]))
        if path.suffix != ".py":
            continue

        here = path.parent
        parent = here.parent

        # `from .. import x` that should be `from . import x`
        def fix_parent(m, path=path, here=here, parent=parent):
            indent, module, names = m.groups()
            targets = _targets(module, names)
            if any(exists(parent, t) for t in targets):
                return m.group(0)
            if not any(exists(here, t) for t in targets):
                return m.group(0)
            print(f"[import_fixer] {path}: 'from ..' -> 'from .'")
            return f"{indent}from .{module} import {names}"

        # `from .x import y` that should be `from ..x import y`
        def fix_sibling(m, path=path, here=here, parent=parent):
            indent, module, names = m.groups()
            targets = _targets(module, names)
            if any(exists(here, t) for t in targets):
                return m.group(0)
            if str(parent) in (".", "") or not any(exists(parent, t) for t in targets):
                return m.group(0)
            print(f"[import_fixer] {path}: 'from .' -> 'from ..'")
            return f"{indent}from ..{module} import {names}"

        content = _PARENT_IMPORT.sub(fix_parent, f["content"])
        content = _SIBLING_IMPORT.sub(fix_sibling, content)
        f["content"] = content

    return files