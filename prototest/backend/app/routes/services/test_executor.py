"""
Actually executes pytest/jest against a reconstructed project on disk,
and parses real pass/fail results — no LLM opinion involved here.
"""

import subprocess
import shutil
import sys
from pathlib import Path
import os


def run_pytest(project_dir: Path, test_code: str) -> dict:
    backend_dir = project_dir / "backend" if (project_dir / "backend").exists() else project_dir

    # ensure backend is a real importable package
    init_file = backend_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")

    # test file goes at project ROOT now, not inside backend/
    test_file = project_dir / "test_generated.py"
    test_file.write_text(test_code, encoding="utf-8")

    req_file = backend_dir / "requirements.txt"
    install_note = None
    install_error = None

    test_env = os.environ.copy()
    test_env["DATABASE_URL"] = "sqlite:///./test_generated.db"

    if req_file.exists():
        # Install into a scratch dir INSIDE this run's own temp project_dir, never into
        # the ProtoTest server's own venv (sys.executable is the live server process —
        # installing a generated project's requirements there would mutate/downgrade the
        # server's own fastapi/pydantic/etc mid-flight). Prepending it to PYTHONPATH makes
        # it take precedence over the base venv for this subprocess only.
        isolated_deps_dir = project_dir / ".protoTest_deps"
        isolated_deps_dir.mkdir(exist_ok=True)

        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file),
             "--target", str(isolated_deps_dir), "--quiet"],
            cwd=project_dir, capture_output=True, text=True, timeout=60,
        )
        if install.returncode != 0:
            install_note = "Dependency install failed, running with base environment."
            install_error = install.stderr[-2000:]
        else:
            existing_pythonpath = test_env.get("PYTHONPATH", "")
            test_env["PYTHONPATH"] = str(isolated_deps_dir) + (
                os.pathsep + existing_pythonpath if existing_pythonpath else ""
            )
    else:
        install_note = "No requirements.txt found, running with base environment."

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_generated.py", "-v", "--tb=short"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=test_env,
        )
        return {
            "runner": "pytest",
            "passed": result.returncode == 0,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-2000:],
            "install_note": install_note,
            "install_error": install_error,
        }
    except subprocess.TimeoutExpired:
        return {
            "runner": "pytest",
            "passed": False,
            "stdout": "",
            "stderr": "Test run timed out after 30 seconds.",
            "install_note": install_note,
            "install_error": install_error,
        }


def run_jest(project_dir: Path, test_code: str) -> dict:
    backend_dir = project_dir / "backend" if (project_dir / "backend").exists() else project_dir

    test_file = backend_dir / "generated.test.js"
    test_file.write_text(test_code, encoding="utf-8")

    pkg_file = backend_dir / "package.json"
    install_note = None

    if pkg_file.exists():
        install = subprocess.run(
            ["npm.cmd" if sys.platform == "win32" else "npm", "install", "--silent"],
            cwd=backend_dir, capture_output=True, text=True, timeout=90,
        )
        if install.returncode != 0:
            error_detail = (install.stderr or install.stdout or "").strip()[-800:]
            install_note = f"npm install failed: {error_detail}" if error_detail else "npm install failed, tests may not run correctly."
        else:
            # ensure jest itself is available, regardless of whether the
            # generated project's package.json happened to include it
            jest_install = subprocess.run(
                ["npm.cmd" if sys.platform == "win32" else "npm", "install", "--no-save", "--silent", "jest", "supertest"],
                cwd=backend_dir, capture_output=True, text=True, timeout=60,
            )
            if jest_install.returncode != 0:
                install_note = "Could not install jest for testing."
    else:
        install_note = "No package.json found, cannot install dependencies."
        return {
            "runner": "jest",
            "passed": False,
            "stdout": "",
            "stderr": "Skipped: no package.json in generated project.",
            "install_note": install_note,
        }

    test_env = os.environ.copy()
    test_env["DATABASE_URL"] = "postgres://test:test@localhost:5432/test_db"
    test_env["DB_URL"] = "postgres://test:test@localhost:5432/test_db"
    test_env["POSTGRES_USER"] = "test"
    test_env["POSTGRES_PASSWORD"] = "test"
    test_env["POSTGRES_HOST"] = "localhost"
    test_env["POSTGRES_PORT"] = "5432"
    test_env["POSTGRES_DB"] = "test_db"

    try:
        result = subprocess.run(
            ["npx.cmd" if sys.platform == "win32" else "npx", "jest", "generated.test.js", "--verbose"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=test_env,
        )
        return {
            "runner": "jest",
            "passed": result.returncode == 0,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-2000:],
            "install_note": install_note,
        }
    except subprocess.TimeoutExpired:
        return {
            "runner": "jest",
            "passed": False,
            "stdout": "",
            "stderr": "Test run timed out after 30 seconds.",
            "install_note": install_note,
        }


def cleanup(project_dir: Path):
    shutil.rmtree(project_dir, ignore_errors=True)