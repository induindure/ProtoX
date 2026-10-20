"""
FastAPI/Pydantic settings consistency: code reads settings.SECRET_KEY but the
Settings class defines secret_key (or nothing). Fixes the case mismatch, or
adds the missing field with a safe default.
"""

import re

from app.services.completeness_checker import _norm

_SETTINGS_CLASS = re.compile(r"^class\s+(\w+)\s*\(\s*BaseSettings\s*\)\s*:", re.MULTILINE)
_USAGE = re.compile(r"\b(settings|Settings\(\)|get_settings\(\))\.([A-Za-z_]\w*)")
_SKIP = {"dict", "json", "copy"}


def _default_for(name: str) -> str:
    n = name.lower()
    if "secret" in n or n.endswith("key"):
        return 'str = "dev-secret-key-change-me-in-production-0123456789"'
    if "algorithm" in n:
        return 'str = "HS256"'
    if any(w in n for w in ("expire", "minutes", "hours", "days")):
        return "int = 60"
    if "database" in n or ("db" in n and n.endswith("url")):
        return 'str = "sqlite:///./app.db"'
    if n.startswith(("debug", "enable")):
        return "bool = False"
    return 'str = ""'


def fix_settings_consistency(files: list[dict]) -> list[dict]:
    backend = [
        f for f in files
        if _norm(f["path"]).startswith("backend/") and _norm(f["path"]).endswith(".py")
    ]

    settings_file = next((f for f in backend if _SETTINGS_CLASS.search(f["content"])), None)
    if settings_file is None:
        return files  # no Pydantic Settings class (e.g. Django)

    def read_fields(text: str):
        m = _SETTINGS_CLASS.search(text)
        lines = text.split("\n")
        idx = text[:m.start()].count("\n")
        end = idx + 1
        while end < len(lines) and (lines[end].strip() == "" or lines[end].startswith((" ", "\t"))):
            end += 1
        fields = set()
        for line in lines[idx + 1:end]:
            fm = re.match(r"^\s{4}(\w+)\s*[:=]", line)
            if fm and fm.group(1) != "model_config":
                fields.add(fm.group(1))
        return fields, idx

    fields, _ = read_fields(settings_file["content"])
    lower_map = {f.lower(): f for f in fields}

    renames, to_add = {}, []
    for f in backend:
        for um in _USAGE.finditer(f["content"]):
            attr = um.group(2)
            if attr in fields or attr.startswith("model_") or attr in _SKIP:
                continue
            if attr.lower() in lower_map:
                renames[attr] = lower_map[attr.lower()]
            elif attr not in to_add:
                to_add.append(attr)

    if renames:
        for f in backend:
            new = _USAGE.sub(
                lambda u: f"{u.group(1)}.{renames.get(u.group(2), u.group(2))}", f["content"]
            )
            f["content"] = new
        print(f"[settings-fixer] fixed setting names: {renames}")

    if to_add:
        _, idx = read_fields(settings_file["content"])
        lines = settings_file["content"].split("\n")
        lines[idx + 1:idx + 1] = [f"    {a}: {_default_for(a)}" for a in to_add]
        settings_file["content"] = "\n".join(lines)
        print(f"[settings-fixer] added missing settings: {to_add}")

    return files