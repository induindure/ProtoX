import json
from pathlib import Path

def detect_stack(root: Path) -> dict:
    fe, be = root / "frontend", root / "backend"
    if not (fe / "package.json").exists() or not be.exists():
        raise ValueError("Expected frontend/ (with package.json) and backend/ folders")

    pkg = json.loads((fe / "package.json").read_text())
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    frontend = "vue" if "vue" in deps else "react"

    if (be / "manage.py").exists():
        settings = next(be.rglob("settings.py"), None)
        if not settings:
            raise ValueError("Django project found but settings.py missing")
        return {"frontend": frontend, "backend": "django",
                "django_project": settings.parent.name}

    if (be / "main.py").exists():
        entry = "main:app"
    elif (be / "app" / "main.py").exists():
        entry = "app.main:app"
    else:
        raise ValueError("FastAPI entry (main.py or app/main.py) not found")
    return {"frontend": frontend, "backend": "fastapi", "entry": entry}