"""
Fixes React context providers that were written but never used, e.g.
AuthProvider exists but <App /> isn't wrapped in it, so useAuth()
returns undefined and the page crashes.
"""

import posixpath
import re

from app.services.completeness_checker import _norm

_PROVIDER_EXPORT = re.compile(
    r"export\s+(default\s+)?(?:function|const)\s+(\w+Provider)\b"
)

ENTRY_CANDIDATES = [
    "frontend/src/main.jsx", "frontend/src/main.tsx",
    "frontend/src/main.js", "frontend/src/main.ts",
    "frontend/src/index.jsx", "frontend/src/index.tsx",
    "frontend/src/index.js",
]


def fix_missing_providers(files: list[dict]) -> list[dict]:
    by_path = {_norm(f["path"]): f for f in files}

    entry_path = next((p for p in ENTRY_CANDIDATES if p in by_path), None)
    if not entry_path:
        return files
    entry = by_path[entry_path]

    for path, f in by_path.items():
        if not path.startswith("frontend/") or not path.endswith((".js", ".jsx", ".ts", ".tsx")):
            continue

        for m in _PROVIDER_EXPORT.finditer(f["content"]):
            is_default, name = bool(m.group(1)), m.group(2)

            # Already used somewhere? Then it's fine.
            if any(f"<{name}" in g["content"] for p, g in by_path.items() if p != path):
                continue

            # Only wrap a plain <App /> so we never break a complex entry file.
            if not re.search(r"<App\s*/>", entry["content"]):
                continue

            rel = posixpath.relpath(posixpath.splitext(path)[0], posixpath.dirname(entry_path))
            if not rel.startswith("."):
                rel = "./" + rel

            import_line = (
                f'import {name} from "{rel}";' if is_default
                else f'import {{ {name} }} from "{rel}";'
            )

            content = re.sub(r"<App\s*/>", f"<{name}><App /></{name}>", entry["content"], count=1)
            entry["content"] = import_line + "\n" + content
            print(f"[provider-fixer] wrapped <App /> with <{name}> in {entry_path}")

    return files

_ROUTER_OPEN = re.compile(r"<(BrowserRouter|Router|HashRouter)(\s[^>]*)?>")
_ROUTER_CLOSE = re.compile(r"</(BrowserRouter|Router|HashRouter)>")
_ROUTER_HOOKS = ("useNavigate", "useLocation", "useParams")
_FRONTEND_EXTS = (".js", ".jsx", ".ts", ".tsx")


def fix_router_placement(files: list[dict]) -> list[dict]:
    """
    Providers that use router hooks (useNavigate etc.) must sit inside the
    router. Ensures <BrowserRouter> is the OUTERMOST wrapper in main.jsx and
    removes routers from deeper files (two routers would crash too).
    """
    by_path = {_norm(f["path"]): f for f in files}

    entry_path = next((p for p in ENTRY_CANDIDATES if p in by_path), None)
    if not entry_path:
        return files
    entry = by_path[entry_path]

    frontend = {
        p: f for p, f in by_path.items()
        if p.startswith("frontend/src/") and p.endswith(_FRONTEND_EXTS)
    }

    # Data routers (createBrowserRouter/RouterProvider) work differently; leave them.
    if any("RouterProvider" in f["content"] for f in frontend.values()):
        return files

    # Providers that need to be inside the router.
    needing = [
        m.group(2)
        for f in frontend.values()
        if any(h in f["content"] for h in _ROUTER_HOOKS)
        for m in _PROVIDER_EXPORT.finditer(f["content"])
    ]
    if not needing:
        return files

    text = entry["content"]
    router_match = _ROUTER_OPEN.search(text)
    if router_match:
        # Is any router-needing provider opened BEFORE (outside) the router?
        outside = [
            name for name in needing
            if 0 <= text.find(f"<{name}") < router_match.start()
        ]
        if not outside:
            return files  # router already wraps everything that needs it
        # Remove the misplaced router; we re-add it at the top below.
        text = _ROUTER_OPEN.sub("", text, count=1)
        text = _ROUTER_CLOSE.sub("", text, count=1)

    # Wrap everything inside .render( ... ) with <BrowserRouter>.
    start = text.find(".render(")
    if start == -1:
        return files
    open_paren = start + len(".render")
    depth, end = 0, -1
    for j in range(open_paren, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                end = j
                break
    if end == -1:
        return files

    inner = text[open_paren + 1:end]
    text = (
        text[:open_paren + 1]
        + "\n  <BrowserRouter>" + inner.rstrip() + "\n  </BrowserRouter>\n"
        + text[end:]
    )
    if not re.search(
        r"import\s*\{[^}]*\bBrowserRouter\b[^}]*\}\s*from\s*['\"]react-router-dom['\"]", text
    ):
        text = "import { BrowserRouter } from 'react-router-dom';\n" + text
    entry["content"] = text
    print(f"[router-fixer] made <BrowserRouter> the outermost wrapper in {entry_path}")

    # Remove any other router from deeper files (e.g. App.jsx).
    for p, f in frontend.items():
        if p == entry_path or not _ROUTER_OPEN.search(f["content"]):
            continue
        c = _ROUTER_OPEN.sub("<>", f["content"])
        f["content"] = _ROUTER_CLOSE.sub("</>", c)
        print(f"[router-fixer] removed inner router from {p}")

    return files