"""
Maps a ProtoCode tech_stack string (e.g. "React + FastAPI") to the actual
commands needed to install dependencies and boot a live dev server for both
halves of the project.
"""

from pathlib import Path
import json
import sys
import os
import re
from urllib.parse import urlparse

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


_API_ENV_NAMES = (
    "VITE_API_URL", "VITE_API_BASE_URL", "VITE_BACKEND_URL",
    "REACT_APP_API_URL", "REACT_APP_API_BASE_URL",
    "NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_API_BASE_URL",
)


def _api_path_suffix(frontend_dir: Path) -> str:
    """
    Finds the path part the frontend expects on the API address, e.g. '/api'
    from VITE_API_URL=http://localhost:8000/api, so Preview can keep it.
    """
    # 1. The frontend's own .env files
    for name in (".env", ".env.local", ".env.development", ".env.example"):
        env_file = frontend_dir / name
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"\s*(\w+)\s*=\s*['\"]?([^'\"\s]+)", line)
            if m and m.group(1) in _API_ENV_NAMES:
                return urlparse(m.group(2)).path.rstrip("/")

    # 2. A fallback address written in the code, e.g. || "http://localhost:8000/api"
    src = frontend_dir / "src"
    if src.exists():
        for f in src.rglob("*"):
            if f.suffix not in (".js", ".jsx", ".ts", ".tsx", ".vue"):
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"https?://(?:localhost|127\.0\.0\.1):\d+(/[^'\"`\s]*)", text)
            if m:
                return m.group(1).rstrip("/")

    return ""

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

    api_url = backend_api_url
    if frontend_dir is not None:
        api_url = backend_api_url + _api_path_suffix(frontend_dir)

    env = {name: api_url for name in _API_ENV_NAMES}
    env["PORT"] = str(port)
    env["BROWSER"] = "none"

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
            "pnpm.cmd",
            "install",
            "--shamefully-hoist",
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

        entry = _detect_backend_entry(backend_dir, backend)

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
                entry,
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
            "pnpm.cmd",
            "install",
            "--shamefully-hoist",
            "--config.dangerously-allow-all-builds=true",
            "--config.strict-dep-builds=false",
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