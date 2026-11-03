import re
from pathlib import Path
import os
import subprocess
import sys

SKIP_DIRS = {"node_modules", ".git", "dist"}
EXTS = {".js", ".jsx", ".ts", ".tsx", ".vue"}

BASE = "import.meta.env.BASE_URL"


def patch_router_basename(project_dir: str) -> list[str]:
    """Add the GitHub Pages base path to the router in frontend/src.
    Returns the list of files that were changed."""
    src = Path(project_dir) / "frontend" / "src"
    changed: list[str] = []
    if not src.exists():
        return changed

    for f in src.rglob("*"):
        if not f.is_file() or f.suffix not in EXTS:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue

        text = f.read_text(encoding="utf-8", errors="ignore")
        if "basename" in text and "BrowserRouter" in text:
            continue  # already handled by the generated code

        new = text
        # React Router: <BrowserRouter>
        new = re.sub(r"<BrowserRouter\s*>", f"<BrowserRouter basename={{{BASE}}}>", new)
        # React Router: createBrowserRouter(routes)
        new = re.sub(
            r"createBrowserRouter\(\s*([A-Za-z_]\w*)\s*\)",
            rf"createBrowserRouter(\1, {{ basename: {BASE} }})",
            new,
        )
        # Vue Router: createWebHistory()
        new = re.sub(r"createWebHistory\(\s*\)", f"createWebHistory({BASE})", new)

        if new != text:
            f.write_text(new, encoding="utf-8")
            changed.append(str(f.relative_to(project_dir)))

    return changed

VITE_VUE_CONFIG = """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
})
"""

POSTCSS_CONFIG = """export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
"""

TAILWIND_CONFIG = """export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
"""


def patch_vue_config(project_dir) -> list[str]:
    """Vue projects: make sure vite/postcss/tailwind configs exist."""
    fe = Path(project_dir) / "frontend"
    pkg = fe / "package.json"
    if not pkg.exists():
        return []
    text = pkg.read_text(encoding="utf-8", errors="ignore")
    if '"vue"' not in text:
        return []

    added = []

    def missing(stem):
        return not any((fe / f"{stem}{ext}").exists() for ext in (".js", ".ts", ".mjs", ".cjs"))

    if missing("vite.config") and "@vitejs/plugin-vue" in text:
        (fe / "vite.config.js").write_text(VITE_VUE_CONFIG, encoding="utf-8")
        added.append("frontend/vite.config.js")
    if "tailwindcss" in text:
        if missing("postcss.config"):
            (fe / "postcss.config.js").write_text(POSTCSS_CONFIG, encoding="utf-8")
            added.append("frontend/postcss.config.js")
        if missing("tailwind.config"):
            (fe / "tailwind.config.js").write_text(TAILWIND_CONFIG, encoding="utf-8")
            added.append("frontend/tailwind.config.js")
    return added

PSYCOPG_LINE = re.compile(r"^\s*psycopg(\[|[=<>~! ]|$)", re.IGNORECASE | re.MULTILINE)


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _listed(text: str) -> set:
    names = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        m = re.match(r"([A-Za-z0-9._-]+)", line)
        if m:
            names.add(_norm(m.group(1)))
    return names


def patch_requirements(project_dir) -> list[str]:
    """Fix wrong package names and add packages the backend imports
    (or Render needs) but requirements.txt forgot."""
    backend = Path(project_dir) / "backend"
    req = backend / "requirements.txt"
    if not req.exists():
        return []

    text = req.read_text(encoding="utf-8", errors="ignore")
    changed = []

    # 'rest_framework_simplejwt' on PyPI is an unrelated stub package
    if re.search(r"(?im)^\s*rest[-_]framework[-_]simplejwt\b", text):
        text = re.sub(r"(?im)^\s*rest[-_]framework[-_]simplejwt\b.*$",
                      "djangorestframework-simplejwt", text)
        changed.append("djangorestframework-simplejwt (fixed name)")

    listed = _listed(text)

    code = ""
    for f in backend.rglob("*.py"):
        if any(p in SKIP_DIRS | {"venv", ".venv"} for p in f.parts):
            continue
        code += f.read_text(encoding="utf-8", errors="ignore") + "\n"

    is_django = (backend / "manage.py").exists()
    needed = []

    def need(pkg: str, cond: bool):
        key = _norm(re.split(r"[\[=<>]", pkg)[0])
        if cond and key not in listed and pkg not in needed:
            needed.append(pkg)

    # Django
    need("django", is_django)
    need("djangorestframework", "rest_framework" in code)
    need("djangorestframework-simplejwt", "rest_framework_simplejwt" in code)
    need("django-cors-headers", "corsheaders" in code)
    need("whitenoise", "whitenoise" in code)
    need("dj-database-url", "dj_database_url" in code)
    need("gunicorn", is_django)
    need("psycopg2-binary",
         is_django and ("dj_database_url" in code or "postgres" in code.lower()))

    # FastAPI / SQLAlchemy
    if "sqlalchemy" in listed:
        need("psycopg[binary]", True)
        need("psycopg2-binary", True)
    need("email-validator", "EmailStr" in code)

    if needed or changed:
        text = text.rstrip() + "\n" + "\n".join(needed) + ("\n" if needed else "\n")
        req.write_text(text, encoding="utf-8")
    return changed + needed

ENV_KEY_RE = re.compile(r"KEY|SECRET|PASSWORD|TOKEN|DATABASE_URL|DB_URL", re.I)
ENV_SKIP_RE = re.compile(r"EXPIRE|ALGORITHM", re.I)
URL_CRED_RE = re.compile(r"(postgres(?:ql)?(?:\+\w+)?://[^:/\s\"']+:)[^@\s\"']+(@)")


def _scrub_env_text(text: str) -> str:
    out = []
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z0-9_]+)\s*=(.*)$", line)
        if m and ENV_KEY_RE.search(m.group(1)) and not ENV_SKIP_RE.search(m.group(1)):
            line = f"{m.group(1)}=CHANGE_ME"
        out.append(line)
    return "\n".join(out) + "\n"


def patch_secrets(project_dir) -> list[str]:
    """Delete real .env files, blank secrets in .env.example, and strip
    passwords from hardcoded database URLs in .py files."""
    root = Path(project_dir)
    changed = []
    for f in root.rglob("*"):
        if not f.is_file() or any(p in SKIP_DIRS | {"venv", ".venv"} for p in f.parts):
            continue
        rel = str(f.relative_to(root)).replace("\\", "/")
        if f.name == ".env" or (f.name.startswith(".env.") and f.name != ".env.example"):
            f.unlink()
            changed.append(f"removed {rel}")
        elif f.name == ".env.example":
            text = f.read_text(encoding="utf-8", errors="ignore")
            new = _scrub_env_text(text)
            if new != text:
                f.write_text(new, encoding="utf-8")
                changed.append(f"scrubbed {rel}")
        elif f.suffix == ".py":
            text = f.read_text(encoding="utf-8", errors="ignore")
            new = URL_CRED_RE.sub(r"\1PASSWORD\2", text)
            if new != text:
                f.write_text(new, encoding="utf-8")
                changed.append(f"scrubbed {rel}")
    return changed

def patch_django_migrations(project_dir) -> list[str]:
    """Django: if any local app has models but no migration files, regenerate
    them all together. Restores the originals if generation fails."""
    backend = Path(project_dir) / "backend"
    if not (backend / "manage.py").exists():
        return []

    skip = SKIP_DIRS | {"venv", ".venv", "staticfiles"}
    apps = []
    for d in sorted(backend.iterdir()):
        if not d.is_dir() or d.name in skip:
            continue
        has_models = (d / "models.py").exists() or (d / "models").is_dir()
        if (d / "__init__.py").exists() and has_models:
            apps.append(d)

    def has_migs(d):
        return bool(list((d / "migrations").glob("0*.py")))

    if not apps or all(has_migs(d) for d in apps):
        return []

    backup = {}
    for d in apps:
        mig = d / "migrations"
        mig.mkdir(exist_ok=True)
        (mig / "__init__.py").touch()
        for old in mig.glob("0*.py"):
            backup[old] = old.read_text(encoding="utf-8", errors="ignore")
            old.unlink()

    env = {
        **os.environ,
        "SECRET_KEY": "build-only-not-a-secret",
        "DEBUG": "True",
        "ALLOWED_HOSTS": "*",
        "CORS_ORIGINS": "http://localhost",
        "DATABASE_URL": "sqlite:///:memory:",
    }
    labels = [d.name for d in apps]
    r = None
    try:
        r = subprocess.run(
            [sys.executable, "manage.py", "makemigrations", *labels],
            cwd=backend, env=env, capture_output=True, text=True, timeout=180,
        )
    except Exception as e:
        print(f"[migrations] could not run: {e}", flush=True)

    new = sorted(p for d in apps for p in (d / "migrations").glob("0*.py"))
    if not new:
        if r is not None:
            print("[migrations] makemigrations FAILED:\n" + (r.stderr or r.stdout), flush=True)
        for path, text in backup.items():          # put the originals back
            path.write_text(text, encoding="utf-8")
        return ["makemigrations failed (see ProtoDeploy terminal)"]
    return [f"migration {p.relative_to(project_dir)}".replace("\\", "/") for p in new]

def detect_api_base(project_dir) -> str:
    """Return '/api' if the backend mounts its routes under /api but the
    frontend calls don't already include it, otherwise ''."""
    root = Path(project_dir)

    # frontend already writes /api/ in its own calls
    fe = root / "frontend" / "src"
    if fe.exists():
        for f in fe.rglob("*"):
            if f.is_file() and f.suffix in EXTS:
                if "/api/" in f.read_text(encoding="utf-8", errors="ignore"):
                    return ""

    # backend mounts under api/
    for f in (root / "backend").rglob("*.py"):
        if any(p in SKIP_DIRS | {"venv", ".venv"} for p in f.parts):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"""path\(\s*['"]api/['"]""", text) or \
           re.search(r"""prefix\s*=\s*['"]/api['"]""", text):
            return "/api"
    return ""