"""
FastAPI: a dependency wrapper that returns Depends(...) hands routes the
placeholder object instead of a real session ('Depends' object has no
attribute 'query'). Rewrites
    def get_db_dep():
        return Depends(get_db)
into
    get_db_dep = get_db
"""

import re

from app.services.completeness_checker import _norm

_RETURN_DEPENDS = re.compile(
    r"^def\s+(\w+)\s*\(\s*\)\s*(?:->[^:]+)?:\s*\n\s+return\s+Depends\(\s*([\w.]+)\s*\)\s*$",
    re.MULTILINE,
)


def fix_depends_wrappers(files: list[dict]) -> list[dict]:
    for f in files:
        path = _norm(f["path"])
        if not path.startswith("backend/") or not path.endswith(".py"):
            continue
        new_text = _RETURN_DEPENDS.sub(
            lambda m: f"{m.group(1)} = {m.group(2)}", f["content"]
        )
        if new_text != f["content"]:
            f["content"] = new_text
            print(f"[fastapi-fixer] replaced Depends-returning wrapper in {path}")
    return files

# `form: OAuth2PasswordRequestForm = Depends()` and the Annotated[...] variant
_FORM_PARAM = re.compile(
    r"(\w+)\s*:\s*(?:OAuth2PasswordRequestForm\s*=\s*Depends\(\s*\)"
    r"|Annotated\[\s*OAuth2PasswordRequestForm\s*,\s*Depends\(\s*\)\s*\])"
)

_LOGIN_MODEL = '''

class LoginRequest(BaseModel):
    """JSON login body: {"username": "...", "password": "..."} (matches the frontend)."""
    username: str
    password: str
'''


def fix_login_form_to_json(files: list[dict]) -> list[dict]:
    """
    The auth contract says login takes JSON, but generated FastAPI code often
    uses OAuth2PasswordRequestForm, which only accepts form data, so the
    frontend's JSON login gets 422. Swap it for a JSON body model with the
    same .username / .password fields, so the route body keeps working.
    """
    for f in files:
        path = _norm(f["path"])
        if not path.startswith("backend/") or not path.endswith(".py"):
            continue
        text = f["content"]
        if not _FORM_PARAM.search(text):
            continue

        text = _FORM_PARAM.sub(lambda m: f"{m.group(1)}: LoginRequest", text)

        # Define LoginRequest after the imports, once.
        if "class LoginRequest" not in text:
            lines = text.split("\n")
            insert_at = 0
            for i, line in enumerate(lines[:80]):
                if line.startswith(("import ", "from ")):
                    insert_at = i + 1
                elif line.startswith(("def ", "class ", "@")):
                    break
            lines[insert_at:insert_at] = _LOGIN_MODEL.split("\n")
            text = "\n".join(lines)

        if not re.search(r"from pydantic import[^\n]*\bBaseModel\b", text):
            text = "from pydantic import BaseModel\n" + text

        f["content"] = text
        print(f"[fastapi-fixer] login now accepts JSON in {path}")

    return files

# Module-level aliases like:  db_dep = Depends(get_db)
_DEPENDS_ALIAS = re.compile(r"^(\w+)\s*=\s*Depends\(", re.MULTILINE)


def fix_double_depends(files: list[dict]) -> list[dict]:
    """
    `x = Depends(get_db)` is fine on its own, but `Depends(x)` then wraps the
    placeholder twice and FastAPI crashes ("Depends(...) is not a callable
    object"). Unwraps every Depends(<alias>) to just <alias>, across files.
    """
    backend = [
        f for f in files
        if _norm(f["path"]).startswith("backend/") and _norm(f["path"]).endswith(".py")
    ]

    aliases = set()
    for f in backend:
        aliases.update(m.group(1) for m in _DEPENDS_ALIAS.finditer(f["content"]))
    if not aliases:
        return files

    names = "|".join(re.escape(a) for a in sorted(aliases))
    # Depends(db_dep) or Depends(deps.db_dep) -> db_dep / deps.db_dep
    pattern = re.compile(rf"Depends\(\s*((?:[\w]+\.)*(?:{names}))\s*\)")

    for f in backend:
        new_text = pattern.sub(lambda m: m.group(1), f["content"])
        if new_text != f["content"]:
            f["content"] = new_text
            print(f"[fastapi-fixer] removed double Depends(...) in {_norm(f['path'])}")
    return files