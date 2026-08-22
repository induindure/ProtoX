"""
Actually executes pytest/jest against a reconstructed project on disk,
and parses real pass/fail results — no LLM opinion involved here.
"""

import subprocess
import shutil
from pathlib import Path


def run_pytest(project_dir: Path, test_code: str) -> dict:
    test_file = project_dir / "test_generated.py"
    test_file.write_text(test_code, encoding="utf-8")

    req_file = project_dir / "requirements.txt"
    install_note = None

    if req_file.exists():
        install = subprocess.run(
            ["pip", "install", "-r", "requirements.txt", "--quiet"],
            cwd=project_dir, capture_output=True, text=True, timeout=60,
        )
        if install.returncode != 0:
            install_note = "Dependency install failed, running with base environment."
    else:
        install_note = "No requirements.txt found, running with base environment."

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "test_generated.py", "-v", "--tb=short"],
            cwd=project_dir, capture_output=True, text=True, timeout=30,
        )
        return {
            "runner": "pytest",
            "passed": result.returncode == 0,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-2000:],
            "install_note": install_note,
        }
    except subprocess.TimeoutExpired:
        return {
            "runner": "pytest",
            "passed": False,
            "stdout": "",
            "stderr": "Test run timed out after 30 seconds.",
            "install_note": install_note,
        }


def run_jest(project_dir: Path, test_code: str) -> dict:
    test_file = project_dir / "generated.test.js"
    test_file.write_text(test_code, encoding="utf-8")

    pkg_file = project_dir / "package.json"
    install_note = None

    if pkg_file.exists():
        install = subprocess.run(
            ["python", "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
            cwd=project_dir, capture_output=True, text=True, timeout=60,
        )
        if install.returncode != 0:
            install_note = "npm install failed, tests may not run correctly."
    else:
        install_note = "No package.json found, cannot install dependencies."
        return {
            "runner": "jest",
            "passed": False,
            "stdout": "",
            "stderr": "Skipped: no package.json in generated project.",
            "install_note": install_note,
        }

    try:
        result = subprocess.run(
            ["npx", "jest", "generated.test.js", "--verbose"],
            cwd=project_dir, capture_output=True, text=True, timeout=30,
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