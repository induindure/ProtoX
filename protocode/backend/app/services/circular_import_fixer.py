"""
Detects import cycles between backend modules (a -> b -> a at module level),
which crash with "partially initialized module", and asks the LLM fixer to
restructure ONLY the files involved, following a fixed layering.
Detection is deterministic (an import graph + cycle search); the AI is only
called when a real cycle exists.
"""

import ast
from pathlib import PurePosixPath

from app.services.code_fixer import fix_code
from app.services.completeness_checker import _norm

_LAYERING = (
    "config.py (settings, SECRET_KEY, ALGORITHM) -> database.py (engine, SessionLocal, "
    "Base, get_db) -> models.py -> schemas.py -> security.py (password hashing, token "
    "creation) -> crud.py -> dependencies.py (get_current_user) -> routers/* -> main.py"
)


def _resolve(base: PurePosixPath, parts: list[str], paths: set):
    target = base.joinpath(*parts) if parts else base
    for cand in (f"{target}.py", f"{target}/__init__.py"):
        if cand in paths:
            return cand
    return None


def _imports_of(path: str, text: str, paths: set) -> set:
    """Project modules that `path` imports at module level."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()

    here = PurePosixPath(path).parent
    stmts = []
    for node in tree.body:
        stmts += node.body if isinstance(node, ast.Try) else [node]

    found = set()
    for node in stmts:
        if isinstance(node, ast.ImportFrom):
            mod_parts = node.module.split(".") if node.module else []
            if node.level:
                base = here
                for _ in range(node.level - 1):
                    base = base.parent
                bases = [base]
            else:
                if not node.module:
                    continue
                bases = [PurePosixPath("."), PurePosixPath("backend")]

            for b in bases:
                target = _resolve(b, mod_parts, paths)
                pkg = b.joinpath(*mod_parts) if mod_parts else b
                subs = [s for a in node.names if (s := _resolve(pkg, [a.name], paths))]
                if target or subs:
                    if target:
                        found.add(target)
                    found.update(subs)
                    break

        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                for b in (PurePosixPath("."), PurePosixPath("backend")):
                    target = _resolve(b, parts, paths)
                    if target:
                        found.add(target)
                        break

    # Importing your own (already loading) package __init__ never re-runs it.
    own = {str(here)} | {str(p) for p in here.parents}
    return {
        t for t in found
        if t != path and not (t.endswith("__init__.py") and str(PurePosixPath(t).parent) in own)
    }


def _find_cycles(graph: dict) -> list[list[str]]:
    """Tarjan's algorithm: groups of modules that import each other in a loop."""
    index, low, stack, on_stack, groups = {}, {}, [], set(), []
    counter = [0]

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in graph.get(v, ()):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            group = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                group.append(w)
                if w == v:
                    break
            if len(group) > 1:
                groups.append(sorted(group))

    for v in graph:
        if v not in index:
            visit(v)
    return groups


def _graph(files: list[dict]) -> dict:
    by_path = {_norm(f["path"]): f for f in files}
    paths = set(by_path)
    return {
        p: _imports_of(p, by_path[p]["content"], paths)
        for p in paths if p.startswith("backend/") and p.endswith(".py")
    }


def fix_circular_imports(files: list[dict]) -> list[dict]:
    cycles = _find_cycles(_graph(files))
    if not cycles:
        return files

    described = "; ".join(" <-> ".join(c) for c in cycles)
    print(f"[circular-import-fixer] import cycles found: {described}")

    by_path = {_norm(f["path"]): f for f in files}
    involved = sorted({p for c in cycles for p in c})
    helpers = sorted(
        p for p in by_path
        if p.startswith("backend/") and p not in involved
        and PurePosixPath(p).name in (
            "config.py", "database.py", "security.py", "dependencies.py", "main.py"
        )
    )

    problem = (
        "Circular imports: each of these groups of backend modules import each other at "
        f"module level, so one is only partially loaded when the other needs it: {described}. "
        "Restructure so imports only go one way, following these layers (a module may only "
        f"import modules to its LEFT): {_LAYERING}. Move shared constants and functions down "
        "into the right lower-layer module (create it if needed). Routes belong only in "
        "routers/. Keep all existing behaviour, URLs and names. Nothing imports from main.py."
    )

    try:
        result = fix_code(
            problem,
            [{"path": p, "content": by_path[p]["content"]} for p in involved + helpers],
            sorted(by_path),
        )
    except Exception as e:
        print(f"[circular-import-fixer] could not fix: {e}")
        return files

    for nf in result.get("files", []):
        path = _norm(nf["path"])
        if path in by_path:
            by_path[path]["content"] = nf["content"]
        else:
            files.append({"path": path, "content": nf["content"]})
        print(f"[circular-import-fixer] updated {path}")

    remaining = _find_cycles(_graph(files))
    if remaining:
        print(f"[circular-import-fixer] cycles still present: {remaining}")
    return files