"""
Detects backend modules that import from main.py (which always causes a
circular import, because main.py imports the routers first) and asks the
LLM fixer to move the shared code into dependencies.py.
"""

import re

from app.services.code_fixer import fix_code
from app.services.completeness_checker import _norm

_FROM_MAIN = re.compile(r"^\s*from\s+(?:\.+|[\w.]+\.)main\s+import\s+", re.MULTILINE)


def fix_imports_from_main(files: list[dict]) -> list[dict]:
    by_path = {_norm(f["path"]): f for f in files}

    offenders = [
        p for p, f in by_path.items()
        if p.startswith("backend/") and p.endswith(".py")
        and not p.endswith("/main.py")
        and _FROM_MAIN.search(f["content"])
    ]
    if not offenders:
        return files

    print(f"[circular-import-fixer] modules importing from main.py: {offenders}")

    main_files = [p for p in by_path if p.startswith("backend/") and p.endswith("/main.py")]
    dep_files = [p for p in by_path if p.startswith("backend/")
                 and p.endswith(("/dependencies.py", "/deps.py"))]

    problem = (
        "Circular import: these modules import from main.py, but main.py imports "
        f"them first: {', '.join(offenders)}. Move every function or object they "
        "import from main.py (and anything those need, such as the OAuth2 scheme, "
        "settings and imports) into the app's dependencies.py (create it next to "
        "main.py if it doesn't exist). Then import it from dependencies.py in "
        "main.py and in these modules. After the fix, NO module may import from main.py."
    )

    to_send = [
        {"path": p, "content": by_path[p]["content"]}
        for p in offenders + main_files + dep_files
    ]

    try:
        result = fix_code(problem, to_send, sorted(by_path))
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

    return files