"""
Fixes `module.name` references where the project module doesn't define
`name`, e.g. security.oauth2_scheme when oauth2_scheme lives in
dependencies.py. Either corrects a typo (close match in the same module)
or points the reference at the one module that does define it.
"""

import ast
import difflib
import re
from pathlib import PurePosixPath

from app.services.completeness_checker import _norm
from app.services.undefined_name_fixer import _insert_imports


def _top_level_names(tree: ast.Module) -> set[str]:
    names = set()
    for node in tree.body:
        nodes = list(ast.walk(node)) if isinstance(node, (ast.If, ast.Try)) else [node]
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(n.name)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    names.update(x.id for x in ast.walk(t) if isinstance(x, ast.Name))
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                names.add(n.target.id)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                names.update((a.asname or a.name).split(".")[0] for a in n.names)
    return names


def _module_aliases(path: str, tree: ast.Module, paths: set) -> dict:
    """{alias: module_path} for `from . import x` / `from .. import x` style imports."""
    here = PurePosixPath(path).parent
    aliases = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level:
            base = here
            for _ in range(node.level - 1):
                base = base.parent
            if node.module:
                base = base.joinpath(*node.module.split("."))
            for a in node.names:
                for cand in (f"{base}/{a.name}.py", f"{base}/{a.name}/__init__.py"):
                    if cand in paths:
                        aliases[a.asname or a.name] = cand
                        break
    return aliases


def fix_module_attributes(files: list[dict]) -> list[dict]:
    by_path = {_norm(f["path"]): f for f in files}
    paths = set(by_path)
    py = {p: f for p, f in by_path.items() if p.startswith("backend/") and p.endswith(".py")}

    trees = {}
    for p, f in py.items():
        try:
            trees[p] = ast.parse(f["content"])
        except SyntaxError:
            continue
    defined = {p: _top_level_names(t) for p, t in trees.items()}

    for p, tree in trees.items():
        aliases = _module_aliases(p, tree, paths)
        if not aliases:
            continue

        here = PurePosixPath(p).parent
        content = py[p]["content"]
        new_imports, seen = [], set()

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)):
                continue
            alias, attr = node.value.id, node.attr
            target = aliases.get(alias)
            if not target or target not in defined or attr in defined[target]:
                continue
            if (alias, attr) in seen:
                continue
            seen.add((alias, attr))
            ref = re.compile(rf"\b{re.escape(alias)}\.{re.escape(attr)}\b")

            # 1. A typo of something the module does define?
            match = difflib.get_close_matches(attr, sorted(defined[target]), n=1, cutoff=0.8)
            if match:
                content = ref.sub(f"{alias}.{match[0]}", content)
                print(f"[attribute-fixer] {p}: {alias}.{attr} -> {alias}.{match[0]}")
                continue

            # 2. Exactly one other module defines it? Point there.
            owners = [
                m for m, names in defined.items()
                if attr in names and m != p and m != target
                and not m.endswith(("/main.py", "__init__.py"))
            ]
            if len(owners) != 1:
                print(f"[attribute-fixer] {p}: can't resolve {alias}.{attr}")
                continue

            owner = PurePosixPath(owners[0])
            mod = owner.stem
            if owner.parent == here:
                imp = f"from . import {mod}"
            elif owner.parent == here.parent:
                imp = f"from .. import {mod}"
            else:
                continue

            content = ref.sub(f"{mod}.{attr}", content)
            already = re.search(rf"^\s*from\s+\.+\s+import\s+[^\n]*\b{mod}\b", content, re.MULTILINE)
            if not already and imp not in new_imports:
                new_imports.append(imp)
            print(f"[attribute-fixer] {p}: {alias}.{attr} -> {mod}.{attr}")

        if new_imports:
            content = _insert_imports(content, new_imports)
        py[p]["content"] = content

    return files