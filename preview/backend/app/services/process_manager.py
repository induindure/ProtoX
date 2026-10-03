"""
Owns the actual subprocesses for a preview session: one for the frontend
dev server, one for the backend dev server.

v2 fixes a real problem from v1: install steps ran via subprocess.run()
(blocking, silent until finished) and the project wasn't added to the
registry until BOTH install+run had fully succeeded. That meant: no live
log output while installing, no way to see progress, and no way to even
hit "Stop preview" if install hung — which it can, e.g. pip's dependency
resolver backtracking forever on a bad requirements.txt, or npm install
stalling on a flaky registry connection.

Now: the project is registered the moment start_preview is called (status
"pending" -> "installing" -> "running"/"install_failed"/"install_timeout"/
"crashed"), install output streams into the log live, and there's a hard
timeout so a hang surfaces as a clear error instead of spinning forever.

Python backends also get their own isolated virtual environment inside
the generated project's backend directory. This prevents generated
project dependencies from modifying or conflicting with Preview's own
virtual environment.
"""

import os
import socket
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
import sys
import re
import secrets
import shutil
import json

from app.services.stack_launcher import (
    split_stack,
    get_frontend_commands,
    get_backend_commands,
)

_registry: dict[str, dict] = {}
_lock = threading.Lock()

LOG_MAXLEN = 300
INSTALL_TIMEOUT_SECONDS = 180  # 3 minutes

# Only these system variables are passed to uv, so nothing from
# Preview's own environment can leak into the dependency install.
_INSTALL_ENV_KEEP = {
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC",
    "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
    "HOMEDRIVE", "HOMEPATH", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE",
}

# Packages generated backends often use but forget to list in
# requirements.txt. Installed for every Python backend; uv's cache
# makes this nearly free after the first time.
EXTRA_PYTHON_PACKAGES = [
    "psycopg2-binary",    # Postgres driver
    "psycopg[binary]",    # Postgres driver (new, psycopg 3)
    "email-validator",    # needed for EmailStr fields
    "python-multipart",   # needed for form data and file uploads
    "python-dotenv",      # loading .env files
    "pydantic-settings",  # Settings classes
    "greenlet",           # needed by async SQLAlchemy
    "asyncpg",            # async Postgres driver
    "aiosqlite",          # async SQLite driver (for the fallback)
    "bcrypt==4.0.1",      # newer bcrypt breaks passlib
    "dj-database-url",
]

# Extra packages for Django backends only.
EXTRA_DJANGO_PACKAGES = [
    "django",
    "djangorestframework",
    "djangorestframework-simplejwt",
    "django-cors-headers",
    "dj-database-url",
]

CREATE_TABLES_SCRIPT = r'''
import importlib
import os
import sys
from pathlib import Path

from sqlalchemy import MetaData, create_engine

metadatas, seen = [], set()

for py in Path("backend").rglob("*.py"):
    if ".preview_venv" in py.parts or "__pycache__" in py.parts:
        continue
    mod_name = ".".join(py.with_suffix("").parts)
    if mod_name.endswith(".__init__"):
        mod_name = mod_name[: -len(".__init__")]
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        print(f"[create-tables] skipped {mod_name}: {e}")
        continue
    for obj in list(vars(mod).values()):
        try:
            md = obj if isinstance(obj, MetaData) else getattr(obj, "metadata", None)
        except Exception:
            continue
        if isinstance(md, MetaData) and md.tables and id(md) not in seen:
            seen.add(id(md))
            metadatas.append(md)

url = os.environ.get("DATABASE_URL", "")
for old, new in (("+asyncpg", ""), ("+aiosqlite", ""), ("+psycopg_async", "+psycopg")):
    url = url.replace(old, new)

if not metadatas or not url:
    print("[create-tables] nothing to create")
    sys.exit(0)

engine = create_engine(url)
for md in metadatas:
    md.create_all(engine)
    print(f"[create-tables] tables ready: {', '.join(sorted(md.tables))}")
'''

def _ensure_project_venv(backend_dir: Path) -> Path:
    """
    Creates an isolated venv for the generated project using uv.
    Retries if Windows temporarily locks a file (antivirus scanning),
    wiping any half-created folder before each attempt.
    """
    venv_dir = backend_dir / ".preview_venv"
    python_exe = venv_dir / "Scripts" / "python.exe"

    if python_exe.exists():
        return python_exe

    last_error = ""
    for attempt in range(4):
        # Remove leftovers from a failed attempt so uv starts clean.
        if venv_dir.exists():
            shutil.rmtree(venv_dir, ignore_errors=True)

        result = subprocess.run(
            [sys.executable, "-m", "uv", "venv", str(venv_dir),
             "--python", sys.executable],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            return python_exe

        last_error = result.stderr
        time.sleep(2)

    raise RuntimeError(f"Could not create project venv:\n{last_error}")

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _stream_output(
    proc: subprocess.Popen,
    log: deque,
    state: dict,
    on_exit_status: str,
):
    for line in iter(proc.stdout.readline, b""):
        if not line:
            break

        log.append(line.decode(errors="ignore").rstrip())

    proc.wait()

    if state["status"] not in ("install_timeout", "stopped"):
        state["status"] = (
            on_exit_status
            if proc.returncode == 0
            else "crashed"
        )

def _pump(proc: subprocess.Popen, log: deque):
    for line in iter(proc.stdout.readline, b""):
        log.append(line.decode("utf-8", errors="replace").rstrip())

_PARENT_IMPORT = re.compile(
    r"^(\s*)from \.\.(\w*) import (.+)$", re.MULTILINE
)

SKIP_DIRS = {".preview_venv", "__pycache__", "node_modules", ".git"}


def _fix_parent_imports_on_disk(backend_dir: Path, log: deque):
    """
    Rewrites `from .. import x` to `from . import x` when x doesn't
    exist one folder up but does exist in the same folder.
    """

    def exists(folder: Path, name: str) -> bool:
        return (folder / f"{name}.py").exists() or (folder / name).is_dir()

    for root, dirs, filenames in os.walk(backend_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue

            py = Path(root) / fname
            here = py.parent
            parent = here.parent

            try:
                text = py.read_text(encoding="utf-8")
            except Exception:
                continue

            changed = False

            def repl(m):
                nonlocal changed
                indent, module, names = m.groups()
                if module:
                    targets = [module]
                else:
                    targets = [
                        n.split(" as ")[0].strip()
                        for n in names.strip("() ").split(",")
                        if n.strip()
                    ]

                if any(exists(parent, t) for t in targets):
                    return m.group(0)
                if not any(exists(here, t) for t in targets):
                    return m.group(0)

                changed = True
                return f"{indent}from .{module} import {names}"

            new_text = _PARENT_IMPORT.sub(repl, text)

            if changed:
                py.write_text(new_text, encoding="utf-8")
                log.append(
                    f"[backend] fixed imports in {py.relative_to(backend_dir)}"
                )

ROUTER_DIR_NAMES = {"routers", "routes", "api", "endpoints"}

def _ensure_router_packages(backend_dir: Path, log: deque):
    """
    Makes sure routers/__init__.py imports its own modules, so code like
    `from . import routers` then `routers.auth.router` works.
    """
    for root, dirs, files in os.walk(backend_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        folder = Path(root)
        if folder.name not in ROUTER_DIR_NAMES:
            continue

        modules = sorted(
            f[:-3] for f in files if f.endswith(".py") and f != "__init__.py"
        )
        if not modules:
            continue

        init = folder / "__init__.py"
        text = init.read_text(encoding="utf-8") if init.exists() else ""
        missing = [m for m in modules if not re.search(rf"\b{re.escape(m)}\b", text)]
        if not missing:
            continue

        if text and not text.endswith("\n"):
            text += "\n"
        init.write_text(text + f"from . import {', '.join(missing)}\n", encoding="utf-8")
        log.append(
            f"[backend] added imports to {init.relative_to(backend_dir)}: {', '.join(missing)}"
        )

def _clean_requirements(backend_dir: Path, log: deque):
    """
    Removes lines from requirements.txt that are actually the project's
    own modules (e.g. 'database', 'models'), not real packages.
    """
    req = backend_dir / "requirements.txt"
    if not req.exists():
        return

    local = set()
    for root, dirs, files in os.walk(backend_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        local.update(d.lower().replace("_", "-") for d in dirs)
        local.update(
            f[:-3].lower().replace("_", "-")
            for f in files if f.endswith(".py")
        )

    kept = []
    for line in req.read_text(encoding="utf-8").splitlines():
        name = re.split(r"[<>=!~\[;\s]", line.strip(), maxsplit=1)[0]
        name = name.lower().replace("_", "-")

        if name and name in local:
            log.append(
                f"[backend] removed '{name}' from requirements.txt (it's a project file, not a package)"
            )
            continue

        kept.append(line)

    req.write_text("\n".join(kept) + "\n", encoding="utf-8")

_UNKNOWN_PKG = [
    re.compile(r"no versions of ([A-Za-z0-9_.\-]+)"),
    re.compile(r"([A-Za-z0-9_.\-]+) was not found in the package registry"),
]


def _req_name(line: str) -> str:
    name = re.split(r"[<>=!~\[;\s]", line.strip(), maxsplit=1)[0]
    return name.lower().replace("_", "-")


def _drop_unknown_package(backend_dir: Path, install_cmd: list, log: deque) -> bool:
    """
    If uv says a package doesn't exist, remove it from requirements.txt
    AND from the install command. Returns True if something was removed.
    """
    bad = None
    for line in reversed(list(log)[-30:]):
        for pattern in _UNKNOWN_PKG:
            m = pattern.search(line)
            if m:
                bad = m.group(1).lower().replace("_", "-")
                break
        if bad:
            break

    if not bad:
        return False

    def simple(s: str) -> str:
        # keep only letters and digits, so hidden characters can't block a match
        return re.sub(r"[^a-z0-9]", "", _req_name(s))

    target = re.sub(r"[^a-z0-9]", "", bad)
    removed = False

    # 1. requirements.txt
    req = backend_dir / "requirements.txt"
    lines = []
    if req.exists():
        lines = req.read_text(encoding="utf-8-sig").splitlines()
        kept = [l for l in lines if simple(l) != target]
        if len(kept) != len(lines):
            req.write_text("\n".join(kept) + "\n", encoding="utf-8")
            log.append(f"[backend] removed '{bad}' from requirements.txt")
            removed = True

    # 2. the install command (EXTRA_PYTHON_PACKAGES ends up here)
    for i in range(len(install_cmd) - 1, -1, -1):
        if simple(str(install_cmd[i])) == target:
            del install_cmd[i]
            log.append(
                f"[backend] removed '{bad}' from the install command "
                f"(delete it from EXTRA_PYTHON_PACKAGES)"
            )
            removed = True

    if removed:
        log.append("[backend] retrying install...")
        return True

    # Still not found: show exactly what we're looking at.
    log.append(f"[backend] couldn't locate '{bad}'. requirements.txt lines:")
    for l in lines:
        log.append(f"    {l!r}")
    log.append(f"[backend] install command: {[str(c) for c in install_cmd]!r}")
    return False

def _ensure_frontend_index(frontend_dir: Path, log: deque):
    """
    Creates the index.html a frontend needs if the AI forgot it:
    public/index.html for Create React App, index.html for Vite.
    """
    pkg_file = frontend_dir / "package.json"
    if not pkg_file.exists():
        return
    try:
        pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
    except Exception:
        return

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    title = pkg.get("name", "App")

    if "react-scripts" in deps:
        index = frontend_dir / "public" / "index.html"
        if index.exists():
            return
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(
            f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
""",
            encoding="utf-8",
        )
        log.append("[frontend] public/index.html was missing — created a default one")
        return

    if "vite" in deps:
        index = frontend_dir / "index.html"
        if index.exists():
            return
        mount = "app" if "vue" in deps else "root"
        candidates = [
            "src/main.ts", "src/main.js", "src/main.tsx", "src/main.jsx",
            "src/index.tsx", "src/index.jsx", "src/index.js",
        ]
        entry = next((c for c in candidates if (frontend_dir / c).exists()), "src/main.js")
        index.write_text(
            f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body>
    <div id="{mount}"></div>
    <script type="module" src="/{entry}"></script>
  </body>
</html>
""",
            encoding="utf-8",
        )
        log.append("[frontend] index.html was missing — created a default one")

def _run_setup_step(cmd, cwd, env, log, label, timeout=120):
    """Runs a one-off setup command (like creating tables) and logs the result.
    Never stops the preview: if it fails, the server still starts."""
    log.append(f"[backend] {label}...")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, env=env,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=timeout,
        )
        for line in (result.stdout + result.stderr).splitlines()[-15:]:
            log.append(f"    {line}")
        if result.returncode != 0:
            log.append(f"[backend] {label} failed (exit {result.returncode}) — starting anyway")
    except Exception as e:
        log.append(f"[backend] {label} could not run: {e}")

def _mark_running_when_ready(state: dict, proc: subprocess.Popen, timeout: int = 180):
    """Switch status from 'starting' to 'running' once the port accepts connections."""
    port = state["port"]
    deadline = time.time() + timeout
    while time.time() < deadline and proc.poll() is None:
        if state["status"] != "starting":
            return
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                state["status"] = "running"
                return
        except OSError:
            time.sleep(0.5)
    if state["status"] == "starting" and proc.poll() is None:
        state["status"] = "running"

_CUSTOM_USER = re.compile(
    r"^class\s+(\w+)\s*\(\s*(?:[\w.]*\.)?(?:AbstractUser|AbstractBaseUser)\b",
    re.MULTILINE,
)


def _fix_django_user_model(backend_dir: Path, log: deque):
    """Adds AUTH_USER_MODEL to settings when the app defines a custom User
    model but forgot to tell Django about it."""
    custom = None
    settings_file = None

    for root, dirs, files in os.walk(backend_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            path = Path(root) / fname
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue

            if settings_file is None and "INSTALLED_APPS" in text:
                settings_file = path

            if custom is None and (fname == "models.py" or path.parent.name == "models"):
                m = _CUSTOM_USER.search(text)
                if m:
                    app_dir = path.parent if fname == "models.py" else path.parent.parent
                    custom = f"{app_dir.name}.{m.group(1)}"

    if not custom or not settings_file:
        return

    settings_text = settings_file.read_text(encoding="utf-8")
    if "AUTH_USER_MODEL" in settings_text:
        return

    settings_file.write_text(
        settings_text.rstrip() + f'\n\nAUTH_USER_MODEL = "{custom}"\n',
        encoding="utf-8",
    )
    log.append(f'[backend] set AUTH_USER_MODEL = "{custom}" in {settings_file.name}')

def _run_side(name: str, cwd: Path, cmds: dict, state: dict):
    log = state["log"]

    env = os.environ.copy()
    env.update(cmds["env"])
    env["PYTHONIOENCODING"] = "utf-8"

    install_env = env
    if name == "backend":
        install_env = {
            k: v for k, v in os.environ.items() if k.upper() in _INSTALL_ENV_KEEP
        }
        suspicious = sorted(
            k for k in os.environ
            if k.upper().startswith(("UV_", "PIP_", "VIRTUAL_ENV", "CONDA"))
        )
        if suspicious:
            log.append(f"[backend] note: Preview's environment contains {suspicious}")

    install_cmd = cmds["install"]
    run_cmd = cmds["run"]
    install_cwd = cwd
    run_cwd = cwd
    create_tables = False
    django_migrate = False

    state["status"] = "installing"

    if name == "frontend":
        _ensure_frontend_index(cwd, log)

    # ---------- Python backend preparation ----------
    if name == "backend" and any("pip" in str(p).lower() for p in install_cmd):
        _fix_parent_imports_on_disk(cwd, log)
        _ensure_router_packages(cwd, log)
        req_file = cwd / "requirements.txt"
        if not req_file.exists():
            root_req = cwd.parent / "requirements.txt"
            if root_req.exists():
                # ProtoCode put it in the project root instead of backend/
                shutil.copy(root_req, req_file)
                log.append("[backend] using requirements.txt from the project root")
            else:
                # No requirements at all: fall back to a sensible default set
                if run_cmd and run_cmd[0] == "uvicorn":
                    defaults = [
                        "fastapi", "uvicorn[standard]", "sqlalchemy", "pydantic",
                        "passlib[bcrypt]", "python-jose[cryptography]", "pyjwt",
                    ]
                else:
                    defaults = ["django", "djangorestframework", "django-cors-headers"]
                req_file.write_text("\n".join(defaults) + "\n", encoding="utf-8")
                log.append("[backend] no requirements.txt found — using a default package set")
        _clean_requirements(cwd, log)

        try:
            project_python = _ensure_project_venv(cwd)
        except Exception as e:
            log.append(f"[{name}] {e}")
            state["status"] = "install_failed"
            return

        install_cmd = [
            sys.executable, "-m", "uv", "pip", "install",
            "-r", "requirements.txt",
            *EXTRA_PYTHON_PACKAGES,
            "--python", str(project_python),
        ]

        if run_cmd and run_cmd[0] == "uvicorn":
            # FastAPI. Run from the project ROOT so "backend.main:app" works,
            # and add backend/ to the import path (--app-dir + PYTHONPATH)
            # so "from app.routes import ..." works too.
            run_cmd = (
                [str(project_python), "-m", "uvicorn"]
                + run_cmd[1:]
                + ["--app-dir", str(cwd)]
            )
            init_file = cwd / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
            run_cwd = cwd.parent
            env["PYTHONPATH"] = str(cwd) + os.pathsep + env.get("PYTHONPATH", "")
            create_tables = True

        elif run_cmd and run_cmd[0] == "python":
            # Django. manage.py lives in backend/, so stay there.
            run_cmd = [str(project_python)] + run_cmd[1:]
            django_migrate = True
            install_cmd[-2:-2] = EXTRA_DJANGO_PACKAGES
            _fix_django_user_model(cwd, log)

        log.append(f"[{name}] using project venv: {project_python}")

    # ---------- Install (retries if requirements.txt has fake packages) ----------
    for attempt in range(6):
        log.append(f"[{name}] installing dependencies...")
        try:
            proc = subprocess.Popen(
                install_cmd,
                cwd=install_cwd,
                env=install_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            log.append(f"[{name}] install could not start: {e}")
            state["status"] = "install_failed"
            return

        state["proc"] = proc
        pump = threading.Thread(target=_pump, args=(proc, log), daemon=True)
        pump.start()

        try:
            proc.wait(timeout=INSTALL_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            log.append(f"[{name}] install timed out after {INSTALL_TIMEOUT_SECONDS}s")
            state["status"] = "install_timeout"
            return

        pump.join(timeout=5)

        if state["status"] == "stopped":
            return

        if proc.returncode == 0:
            break

        if name == "backend" and _drop_unknown_package(install_cwd, install_cmd, log):
            continue

        if name == "frontend" and any(
            "EBUSY" in l or "EPERM" in l for l in list(log)[-10:]
        ):
            log.append("[frontend] Windows locked a file — retrying install...")
            time.sleep(2)
            continue

        log.append(f"[{name}] install failed (exit code {proc.returncode})")
        state["status"] = "install_failed"
        return
    else:
        log.append(f"[{name}] install failed after several retries")
        state["status"] = "install_failed"
        return

    # ---------- Django: create tables ----------
    if name == "backend" and django_migrate:
        _run_setup_step([str(project_python), "manage.py", "makemigrations"],
                        run_cwd, env, log, "preparing migrations (Django)")
        _run_setup_step([str(project_python), "manage.py", "migrate", "--run-syncdb"],
                        run_cwd, env, log, "creating database tables (Django)")

    # ---------- Node/Express: create tables ----------
    if name == "backend" and str(install_cmd[0]).startswith("pnpm"):
        npx = "npx.cmd" if os.name == "nt" else "npx"
        if (cwd / "prisma" / "schema.prisma").exists():
            _run_setup_step([npx, "prisma", "db", "push"],
                            cwd, env, log, "creating database tables (Prisma)")
        elif any((cwd / f).exists() for f in ("knexfile.js", "knexfile.ts")):
            _run_setup_step([npx, "knex", "migrate:latest"],
                            cwd, env, log, "creating database tables (Knex)")

    # ---------- Run dev server ----------
    # ---------- Create database tables the app forgot to create ----------
    if name == "backend" and create_tables:
        script = run_cwd / "_preview_create_tables.py"
        script.write_text(CREATE_TABLES_SCRIPT, encoding="utf-8")
        try:
            result = subprocess.run(
                [str(project_python), str(script)],
                cwd=run_cwd,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            for line in (result.stdout + result.stderr).splitlines()[-15:]:
                log.append(f"    {line}")
        except Exception as e:
            log.append(f"[backend] could not create tables: {e}")
    log.append(f"[{name}] starting: {' '.join(str(c) for c in run_cmd)}")
    try:
        proc = subprocess.Popen(
            run_cmd,
            cwd=run_cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except Exception as e:
        log.append(f"[{name}] server could not start: {e}")
        state["status"] = "crashed"
        return

    state["proc"] = proc
    state["status"] = "starting"
    threading.Thread(
        target=_mark_running_when_ready, args=(state, proc), daemon=True
    ).start()
    _stream_output(proc, log, state, on_exit_status="stopped")

def _uses_async_db(backend_dir: Path) -> bool:
    """True if the generated backend uses async SQLAlchemy."""
    for f in backend_dir.rglob("*.py"):
        if ".preview_venv" in f.parts:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "create_async_engine" in text or "AsyncEngine" in text:
            return True
    return False


def _to_async_url(url: str) -> str:
    """Convert a normal database URL into its async-driver form."""
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("sqlite:///"):
        return "sqlite+aiosqlite:///" + url[len("sqlite:///"):]
    return url


def start_preview(
    project_id: str,
    project_dir: Path,
    tech_stack: str,
    database_url: str | None = None,
) -> dict:

    with _lock:
        existing = _registry.get(project_id)

        # If this project is already starting or running, don't start it
        # a second time. Two copies in the same folder fight over files.
        if existing and any(
            existing[side]["status"] in ("pending", "installing", "starting", "running")
            for side in ("frontend", "backend")
        ):
            return existing

        frontend_name, backend_name = split_stack(tech_stack)

        entry = {
            "frontend": {
                "proc": None,
                "port": None,
                "log": deque(maxlen=LOG_MAXLEN),
                "status": "pending",
            },
            "backend": {
                "proc": None,
                "port": None,
                "log": deque(maxlen=LOG_MAXLEN),
                "status": "pending",
            },
            "dir": project_dir,
            "stack": tech_stack,
        }

        _registry[project_id] = entry

    # ---------------------------------------------------------
    # Backend
    # ---------------------------------------------------------
    backend_dir = project_dir / "backend"

    backend_port = _find_free_port()
    entry["backend"]["port"] = backend_port

    backend_cmds = get_backend_commands(
        backend_name,
        backend_port,
        backend_dir,
    )

    # Use the user's database if given; otherwise fall back to a local
    # SQLite file so the backend can start without a real database.
    db_url = database_url or "sqlite:///./preview.db"

    if _uses_async_db(backend_dir):
        db_url = _to_async_url(db_url)

    for key in ("DATABASE_URL", "POSTGRES_URL", "DB_URL", "SQLALCHEMY_DATABASE_URL"):
        backend_cmds["env"][key] = db_url
    # Common settings generated apps require. Random secret per preview.
    default_settings = {
        "SECRET_KEY": secrets.token_hex(32),
        "JWT_SECRET": secrets.token_hex(32),
        "JWT_SECRET_KEY": secrets.token_hex(32),
        "ALGORITHM": "HS256",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    }
    for key, value in default_settings.items():
        backend_cmds["env"].setdefault(key, value)

    # ---------------------------------------------------------
    # Frontend
    # ---------------------------------------------------------
    frontend_dir = project_dir / "frontend"

    backend_url = f"http://localhost:{backend_port}"

    frontend_port = _find_free_port()
    entry["frontend"]["port"] = frontend_port

    frontend_cmds = get_frontend_commands(
        frontend_name,
        frontend_port,
        backend_url,
        frontend_dir,
    )

    # ---------------------------------------------------------
    # Start backend and frontend concurrently
    # ---------------------------------------------------------
    threading.Thread(
        target=_run_side,
        args=(
            "backend",
            backend_dir,
            backend_cmds,
            entry["backend"],
        ),
        daemon=True,
    ).start()

    threading.Thread(
        target=_run_side,
        args=(
            "frontend",
            frontend_dir,
            frontend_cmds,
            entry["frontend"],
        ),
        daemon=True,
    ).start()

    return entry


def get_status(project_id: str) -> dict | None:
    entry = _registry.get(project_id)

    if not entry:
        return None

    return {
        "frontend": {
            "status": entry["frontend"]["status"],
            "port": entry["frontend"]["port"],
            "url": (
                f"http://localhost:{entry['frontend']['port']}"
                if entry["frontend"]["port"]
                else None
            ),
            "log": list(entry["frontend"]["log"])[-40:],
        },
        "backend": {
            "status": entry["backend"]["status"],
            "port": entry["backend"]["port"],
            "url": (
                f"http://localhost:{entry['backend']['port']}"
                if entry["backend"]["port"]
                else None
            ),
            "log": list(entry["backend"]["log"])[-40:],
        },
    }


def stop_preview(project_id: str):
    entry = _registry.pop(project_id, None)

    if not entry:
        return

    for side in ("frontend", "backend"):
        entry[side]["status"] = "stopped"

        proc = entry[side]["proc"]

        if proc and proc.poll() is None:
            proc.terminate()

            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()