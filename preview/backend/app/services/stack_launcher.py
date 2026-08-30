"""
Maps a ProtoCode tech_stack string (e.g. "React + FastAPI") to the actual
commands needed to install dependencies and boot a live dev server for both
halves of the project.
"""

from pathlib import Path
import json
import sys
import os


FRONTENDS = ["React", "Vue", "Next.js"]
BACKENDS = ["FastAPI", "Django", "Node/Express"]


def split_stack(tech_stack: str) -> tuple[str, str]:
    """'React + FastAPI' -> ('React', 'FastAPI')."""
    frontend = next((f for f in FRONTENDS if f in tech_stack), "React")
    backend = next((b for b in BACKENDS if b in tech_stack), "FastAPI")
    return frontend, backend


def _detect_backend_entry(backend_dir: Path, backend: str) -> str:
    if (backend_dir / "main.py").exists():
        return "backend.main:app"

    if (backend_dir / "app" / "main.py").exists():
        return "backend.app.main:app"

    for py_file in backend_dir.rglob("*.py"):
        try:
            text = py_file.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            continue

        if "FastAPI(" in text:
            rel = py_file.relative_to(backend_dir).with_suffix("")
            module = ".".join(rel.parts)
            return f"backend.{module}:app"

    return "backend.main:app"


def _detect_node_entry(backend_dir: Path) -> str:
    """
    Determines how a Node/Express backend should be started.
    """

    pkg_json = backend_dir / "package.json"

    if pkg_json.exists():
        try:
            pkg = json.loads(
                pkg_json.read_text(encoding="utf-8")
            )

            scripts = pkg.get("scripts", {})

            if "dev" in scripts:
                return "npm run dev"

            if "start" in scripts:
                return "npm start"

            if pkg.get("main"):
                return f"node {pkg['main']}"

        except Exception:
            pass

    for candidate in ("server.js", "index.js", "app.js"):
        if (backend_dir / candidate).exists():
            return f"node {candidate}"

    return "node index.js"


def _detect_frontend_run_command(
    frontend_dir: Path,
    frontend: str,
    port: int
) -> list[str]:
    """
    Detects whether the generated frontend uses:

    - Vite       -> npm run dev
    - CRA        -> npm start
    - Next.js    -> npm run dev
    """

    pkg_file = frontend_dir / "package.json"

    scripts = {}

    if pkg_file.exists():
        try:
            pkg = json.loads(
                pkg_file.read_text(encoding="utf-8")
            )
            scripts = pkg.get("scripts", {})
        except Exception:
            pass

    # Next.js
    if frontend == "Next.js":

        if "dev" in scripts:
            return [
                "npm.cmd",
                "run",
                "dev",
                "--",
                "-p",
                str(port),
                "-H",
                "0.0.0.0",
            ]

        if "start" in scripts:
            return [
                "npm.cmd",
                "start",
                "--",
                "-p",
                str(port),
                "-H",
                "0.0.0.0",
            ]

    # Vite / other projects with dev script
    if "dev" in scripts:
        return [
            "npm.cmd",
            "run",
            "dev",
            "--",
            "--port",
            str(port),
            "--host",
            "0.0.0.0",
        ]

    # Create React App
    if "start" in scripts:
        return [
            "npm.cmd",
            "start",
        ]

    # Fallback
    return [
        "npm.cmd",
        "start",
    ]


def get_frontend_commands(
    frontend: str,
    port: int,
    backend_api_url: str,
    frontend_dir: Path | None = None,
) -> dict:
    """
    Returns:

        {
            "install": [...],
            "run": [...],
            "env": {...}
        }
    """

    env = {
        "VITE_API_URL": backend_api_url,
        "NEXT_PUBLIC_API_URL": backend_api_url,
        "REACT_APP_API_URL": backend_api_url,
    }

    if frontend_dir is not None:
        run_command = _detect_frontend_run_command(
            frontend_dir,
            frontend,
            port,
        )
    else:
        if frontend == "Next.js":
            run_command = [
                "npm.cmd",
                "run",
                "dev",
                "--",
                "-p",
                str(port),
                "-H",
                "0.0.0.0",
            ]
        else:
            run_command = [
                "npm.cmd",
                "run",
                "dev",
                "--",
                "--port",
                str(port),
                "--host",
                "0.0.0.0",
            ]

    return {
        "install": [
            "npm.cmd",
            "install",
        ],
        "run": run_command,
        "env": env,
    }


def get_backend_commands(
    backend: str,
    port: int,
    backend_dir: Path
) -> dict:

    # -------------------------
    # FastAPI
    # -------------------------

    if backend == "FastAPI":

        entry = "app.main:app"

        return {
            "install": [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "-r",
                "requirements.txt",
            ],
            "run": [
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(port),
            ],
            "env": {},
        }

    # -------------------------
    # Django
    # -------------------------

    if backend == "Django":

        return {
            "install": [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "-r",
                "requirements.txt",
            ],
            "run": [
                "python",
                "manage.py",
                "runserver",
                f"0.0.0.0:{port}",
            ],
            "env": {},
        }

    # -------------------------
    # Node / Express
    # -------------------------

    if backend == "Node/Express":

        entry_cmd = _detect_node_entry(
            backend_dir
        )

        run_cmd = entry_cmd.split()

        # Windows needs npm.cmd
        if run_cmd and run_cmd[0] == "npm":
            run_cmd[0] = "npm.cmd"

        # Pass the dynamically selected port
        # when using an npm script.
        if entry_cmd.startswith("npm"):
            run_cmd += [
                "--",
                str(port),
            ]

        # IMPORTANT:
        # Pass DATABASE_URL from the ProtoPreview
        # environment to the generated Node backend.
        database_url = os.environ.get(
            "DATABASE_URL",
            ""
        )

        return {
            "install": [
                "npm.cmd",
                "install",
            ],
            "run": run_cmd,
            "env": {
                "PORT": str(port),
                "DATABASE_URL": database_url,
            },
        }

    raise ValueError(
        f"Unsupported backend: {backend}"
    )