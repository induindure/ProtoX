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