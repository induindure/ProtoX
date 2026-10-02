"""
Fixes a common AI generation mistake: `from .. import x` (look one
package up) when x actually lives in the same folder. Rewrites it to
`from . import x` when the `..` version is guaranteed to fail.
"""

import re
from pathlib import PurePosixPath

_PARENT_IMPORT = re.compile(
    r"^(\s*)from \.\.(\w*) import (.+)$", re.MULTILINE
)


def _norm(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


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

        def repl(m, path=path, here=here, parent=parent):
            indent, module, names = m.groups()
            if module:
                targets = [module]
            else:
                targets = [
                    n.split(" as ")[0].strip()
                    for n in names.strip("() \r").split(",")
                    if n.strip()
                ]

            # If anything really exists one level up, leave it alone.
            if any(exists(parent, t) for t in targets):
                return m.group(0)

            # If nothing exists in this folder either, we can't help.
            if not any(exists(here, t) for t in targets):
                return m.group(0)

            print(f"[import_fixer] {path}: fixed 'from ..' -> 'from .'")
            return f"{indent}from .{module} import {names}"

        f["content"] = _PARENT_IMPORT.sub(repl, f["content"])

    return files