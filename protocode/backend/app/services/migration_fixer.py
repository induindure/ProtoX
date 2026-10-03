"""
Django projects: drop AI-written migration files (keeping migrations/__init__.py)
so Django generates correct ones from the models with makemigrations.
"""

import re
from pathlib import PurePosixPath

from app.services.completeness_checker import _norm

_MIGRATION_FILE = re.compile(r"(^|/)migrations/(?!__init__\.py$)[^/]+\.py$")


def drop_generated_migrations(files: list[dict]) -> list[dict]:
    paths = {_norm(f["path"]) for f in files}
    if not any(p.endswith("manage.py") for p in paths):
        return files  # not a Django project

    kept, dropped, migration_dirs = [], [], set()
    for f in files:
        p = _norm(f["path"])
        if p.startswith("backend/") and _MIGRATION_FILE.search(p):
            dropped.append(p)
            migration_dirs.add(str(PurePosixPath(p).parent))
            continue
        kept.append(f)

    # Keep each migrations folder as a package so makemigrations fills it in.
    existing = {_norm(f["path"]) for f in kept}
    for d in migration_dirs:
        init = f"{d}/__init__.py"
        if init not in existing:
            kept.append({"path": init, "content": ""})

    if dropped:
        print(f"[migration-fixer] dropped AI-written migrations: {dropped}")
    return kept