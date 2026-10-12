"""
Django REST Framework: register/login/token views must be reachable without
being logged in. AI-generated projects often set a global "login required"
default and forget to exempt these views, causing 401 on registration.
"""

import re
from pathlib import PurePosixPath
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

_CUSTOM_USER = re.compile(
    r"^class\s+(\w+)\s*\(\s*(?:[\w.]*\.)?(?:AbstractUser|AbstractBaseUser)\b",
    re.MULTILINE,
)


def fix_django_user_model(files: list[dict]) -> list[dict]:
    """
    If the project defines a custom User model but settings.py doesn't set
    AUTH_USER_MODEL, Django uses two different user tables: register saves to
    one, login and token checks read the other, so every login returns 401.
    """
    by_path = {_norm(f["path"]): f for f in files}
    if not any(p.endswith("manage.py") for p in by_path):
        return files  # not a Django project

    custom = None
    settings_file = None

    for path, f in by_path.items():
        if not path.startswith("backend/") or not path.endswith(".py"):
            continue
        text = f["content"]

        if settings_file is None and "INSTALLED_APPS" in text and "MIDDLEWARE" in text:
            settings_file = f

        if custom is None and (path.endswith("/models.py") or "/models/" in path):
            m = _CUSTOM_USER.search(text)
            if m:
                parts = PurePosixPath(path).parts
                app_label = parts[-2] if path.endswith("/models.py") else parts[-3]
                custom = f"{app_label}.{m.group(1)}"

    if not custom or settings_file is None:
        return files
    if "AUTH_USER_MODEL" in settings_file["content"]:
        return files

    settings_file["content"] = (
        settings_file["content"].rstrip() + f'\n\nAUTH_USER_MODEL = "{custom}"\n'
    )
    print(f'[django-user-fixer] set AUTH_USER_MODEL = "{custom}"')
    return files

_CONFIRM_FIELDS = ("password2", "confirm_password", "password_confirm")


def _fix_register_serializer_text(text: str):
    lines = text.split("\n")

    for idx, line in enumerate(lines):
        m = re.match(r"^class\s+(\w+)\s*\(([^)]*)\)\s*:", line)
        if not m or "Serializer" not in m.group(2):
            continue
        if not re.search(r"regist|signup|sign_up", m.group(1), re.IGNORECASE):
            continue

        # The class body: indented lines after the class line.
        end = idx + 1
        while end < len(lines) and (lines[end].strip() == "" or lines[end].startswith((" ", "\t"))):
            end += 1
        body = "\n".join(lines[idx + 1:end])

        if "create_user" in body or "set_password" in body:
            return text, False  # already hashes passwords

        if "def create" in body:
            # Has its own create(); make it hash the password.
            new_body = re.sub(r"\.objects\.create\(", ".objects.create_user(", body)
            if new_body == body:
                return text, False
            lines[idx + 1:end] = new_body.split("\n")
        else:
            # Plain ModelSerializer: add a create() that hashes the password.
            if "class Meta" not in body or "model" not in body:
                return text, False
            insert_at = end
            while insert_at > idx + 1 and lines[insert_at - 1].strip() == "":
                insert_at -= 1
            pops = [f'        validated_data.pop("{f}", None)' for f in _CONFIRM_FIELDS]
            lines[insert_at:insert_at] = (
                ["", "    def create(self, validated_data):"]
                + pops
                + ["        return self.Meta.model.objects.create_user(**validated_data)"]
            )
        return "\n".join(lines), True

    return text, False


def fix_register_password_hashing(files: list[dict]) -> list[dict]:
    """
    Registration serializers often save the password as plain text, so the
    user can register but never log in. Makes them use create_user(), which
    hashes the password.
    """
    for f in files:
        path = _norm(f["path"])
        if not path.startswith("backend/") or not path.endswith("serializers.py"):
            continue
        new_text, changed = _fix_register_serializer_text(f["content"])
        if changed:
            f["content"] = new_text
            print(f"[django-password-fixer] made registration hash passwords in {path}")
    return files