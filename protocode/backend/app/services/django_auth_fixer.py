"""
Django REST Framework: register/login/token views must be reachable without
being logged in. AI-generated projects often set a global "login required"
default and forget to exempt these views, causing 401 on registration.
"""

import re

from app.services.completeness_checker import _norm

_AUTH_NAME = re.compile(r"(register|signup|sign_up|login|token)", re.IGNORECASE)
_CLASS_LINE = re.compile(r"^class\s+(\w+)\s*\(([^)]*)\)\s*:")
_DEF_LINE = re.compile(r"^def\s+(\w+)\s*\(")


def _fix_views_text(text: str):
    lines = text.split("\n")
    out = []
    changed = False
    need_decorator_import = False

    for i, line in enumerate(lines):
        cm = _CLASS_LINE.match(line)
        if cm and _AUTH_NAME.search(cm.group(1)) and "View" in cm.group(2):
            # Collect the class body (indented lines that follow).
            body = []
            for nxt in lines[i + 1:]:
                if nxt.strip() == "" or nxt.startswith((" ", "\t")):
                    body.append(nxt)
                else:
                    break
            out.append(line)
            if "permission_classes" not in "\n".join(body):
                indent = next(
                    (re.match(r"^(\s+)", b).group(1) for b in body if b.strip()), "    "
                )
                out.append(f"{indent}permission_classes = [AllowAny]")
                out.append(f"{indent}authentication_classes = []")
                changed = True
            continue

        fm = _DEF_LINE.match(line)
        if fm and _AUTH_NAME.search(fm.group(1)):
            # Decorators directly above this function (already in `out`).
            decorators = []
            k = len(out) - 1
            while k >= 0 and out[k].startswith("@"):
                decorators.append(out[k])
                k -= 1
            if any(d.startswith("@api_view") for d in decorators) and not any(
                "permission_classes" in d for d in decorators
            ):
                out.append("@permission_classes([AllowAny])")
                out.append("@authentication_classes([])")
                need_decorator_import = True
                changed = True

        out.append(line)

    if not changed:
        return text, False

    header = []
    new_text = "\n".join(out)
    if not re.search(r"import[^\n]*\bAllowAny\b", new_text):
        header.append("from rest_framework.permissions import AllowAny")
    if need_decorator_import:
        header.append(
            "from rest_framework.decorators import permission_classes, authentication_classes"
        )
    if header:
        new_text = "\n".join(header) + "\n" + new_text
    return new_text, True


def fix_django_auth_views(files: list[dict]) -> list[dict]:
    for f in files:
        path = _norm(f["path"])
        if not path.startswith("backend/") or not path.endswith(".py"):
            continue
        if not (path.endswith("views.py") or "/views/" in path):
            continue
        if "rest_framework" not in f["content"]:
            continue

        new_text, changed = _fix_views_text(f["content"])
        if changed:
            f["content"] = new_text
            print(f"[django-auth-fixer] opened register/login views in {path}")

    return files