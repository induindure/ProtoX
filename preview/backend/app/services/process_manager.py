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
import venv

from app.services.stack_launcher import (
    split_stack,
    get_frontend_commands,
    get_backend_commands,
)

_registry: dict[str, dict] = {}
_lock = threading.Lock()

LOG_MAXLEN = 300
INSTALL_TIMEOUT_SECONDS = 180  # 3 minutes


def _ensure_project_venv(backend_dir: Path) -> Path:
    """
    Creates an isolated venv for the generated project and
    makes sure pip is installed inside it.
    """
    venv_dir = backend_dir / ".preview_venv"
    python_exe = venv_dir / "Scripts" / "python.exe"

    if not python_exe.exists():
        venv.create(venv_dir, with_pip=False)

    # Install pip into the project venv using ensurepip.
    result = subprocess.run(
        [str(python_exe), "-m", "ensurepip", "--upgrade"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Could not install pip into project venv:\n{result.stderr}"
        )

    return python_exe


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

def _run_side(name: str, cwd: Path, cmds: dict, state: dict):
    log = state["log"]

    env = os.environ.copy()
    env.update(cmds["env"])

    install_cmd = cmds["install"]
    run_cmd = cmds["run"]
        # For Python backends, create/use an isolated project venv.
    if name == "backend" and install_cmd and any("pip" in part.lower() for part in install_cmd):
        project_python = _ensure_project_venv(cwd)

        install_cmd = [
            str(project_python),
            "-m",
            "pip",
            "install",
            "-q",
            "-r",
            "requirements.txt",
        ]

        # FastAPI: run uvicorn using the project's venv.
        if run_cmd and run_cmd[0] == "uvicorn":
            run_cmd = [
                str(project_python),
                "-m",
                "uvicorn",
            ] + run_cmd[1:]

        # Django: run manage.py using the project's venv.
        elif run_cmd and run_cmd[0] == "python":
            run_cmd = [
                str(project_python)
            ] + run_cmd[1:]

        # Ensure "backend" is a real importable package (needed for
        # relative imports like "from .routes import ...").
        init_file = cwd / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")

        # Run from the project ROOT, not inside backend/, so
        # "backend.main:app" resolves and relative imports work.
        cwd = cwd.parent

        log.append(
            f"[{name}] using project venv: {project_python}"
        )


def start_preview(
    project_id: str,
    project_dir: Path,
    tech_stack: str,
    database_url: str | None = None,
) -> dict:

    with _lock:
        existing = _registry.get(project_id)

        if (
            existing
            and existing["frontend"]["status"] == "running"
            and existing["backend"]["status"] == "running"
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

    if database_url:
        backend_cmds["env"]["DATABASE_URL"] = database_url

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