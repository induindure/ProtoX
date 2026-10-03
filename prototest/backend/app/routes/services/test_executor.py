"""
Actually executes pytest/jest against a reconstructed project on disk,
and parses real pass/fail results — no LLM opinion involved here.
"""

import subprocess
import shutil
import sys
from pathlib import Path
import os
import re

_DJANGO_SETTINGS_RE = re.compile(
    r"""DJANGO_SETTINGS_MODULE['"]\s*,\s*['"]([\w.]+)['"]"""
)

_DJANGO_CONFTEST = '''
import pytest


# Added by ProtoTest: let every generated test use the test database.
@pytest.fixture(autouse=True)
def _prototest_enable_db(db):
    pass
'''

# Packages Django projects commonly use but often leave out of requirements.txt.
_DJANGO_TEST_EXTRAS = [
    "pytest-django",
    "django",
    "djangorestframework",
    "djangorestframework-simplejwt",
    "django-cors-headers",
    "dj-database-url",
]

def _find_django(project_dir: Path):
    """Finds manage.py anywhere in the project. Returns (django_root, settings_module),
    or (None, None) if this isn't a Django project."""
    for manage in project_dir.rglob("manage.py"):
        if any(part in (".protoTest_deps", "node_modules", ".venv") for part in manage.parts):
            continue
        m = _DJANGO_SETTINGS_RE.search(manage.read_text(encoding="utf-8", errors="ignore"))
        if m:
            return manage.parent, m.group(1)
    return None, None


def run_pytest(project_dir: Path, test_code: str) -> dict:
    backend_dir = project_dir / "backend" if (project_dir / "backend").exists() else project_dir

    # ensure backend is a real importable package
    init_file = backend_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")

    # test file goes at project ROOT, not inside backend/
    test_file = project_dir / "test_generated.py"
    test_file.write_text(test_code, encoding="utf-8")

    req_file = backend_dir / "requirements.txt"
    django_root, settings_module = _find_django(project_dir)
    is_django = settings_module is not None

    install_note = None
    install_error = None

    test_env = os.environ.copy()
    test_env["DATABASE_URL"] = "sqlite:///./test_generated.db"
    pythonpath_parts = []

    if req_file.exists() or is_django:
        # Install into a scratch dir INSIDE this run's temp project_dir, never into
        # the ProtoTest server's own venv. Prepending it to PYTHONPATH makes it take
        # precedence over the base venv for this subprocess only.
        isolated_deps_dir = project_dir / ".protoTest_deps"
        isolated_deps_dir.mkdir(exist_ok=True)

        install_cmd = [
            sys.executable, "-m", "uv", "pip", "install", "-q",
            "--target", str(isolated_deps_dir),
            "--python", sys.executable,
        ]
        if req_file.exists():
            install_cmd += ["-r", str(req_file)]
        if is_django:
            install_cmd += _DJANGO_TEST_EXTRAS

        install = subprocess.run(
            install_cmd, cwd=project_dir, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=180,
        )
        if install.returncode != 0:
            install_note = "Dependency install failed, running with base environment."
            install_error = (install.stderr or install.stdout)[-2000:]
        else:
            pythonpath_parts.append(str(isolated_deps_dir))
    else:
        install_note = "No requirements.txt found, running with base environment."

    if is_django:
        # Make "app.settings" importable and tell Django to use it.
        pythonpath_parts.append(str(django_root))
        test_env["DJANGO_SETTINGS_MODULE"] = settings_module
        install_note = (install_note + " " if install_note else "") + \
            f"Django project detected (settings: {settings_module})."

        # Enable database access for all generated tests.
        conftest = project_dir / "conftest.py"
        existing = conftest.read_text(encoding="utf-8") if conftest.exists() else ""
        if "_prototest_enable_db" not in existing:
            conftest.write_text(existing + _DJANGO_CONFTEST, encoding="utf-8")

    existing_pythonpath = test_env.get("PYTHONPATH", "")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    if pythonpath_parts:
        test_env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    # Django needs extra time to build its test database.
    timeout = 90 if is_django else 30

    pytest_cmd = [sys.executable, "-m", "pytest", "test_generated.py", "-v", "--tb=short"]
    if is_django:
        pytest_cmd.append("--nomigrations")  # build test tables from models, skip AI-written migrations

    try:
        result = subprocess.run(
            pytest_cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
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
            "stderr": f"Test run timed out after {timeout} seconds.",
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