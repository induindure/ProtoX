"""
Uses the same Groq LLM that writes tests to patch broken code: either a single
file that failed check_syntax, or the set of application files a failing
pytest/jest run points at.
"""

import os
import json
from dotenv import load_dotenv
from app.routes.services.llm_provider import complete
from app.routes.services.llm_utils import strip_code_fences

from app.routes.services.llm_utils import strip_code_fences

import asyncio
import urllib.request
from app.routes.services.llm_provider import complete
from app.routes.services.test_generator import _is_backend_file, ensure_stdlib_imports, fix_known_import_mistakes

load_dotenv()

async def fix_syntax_error(path: str, content: str, error_message: str) -> str:
    """
    Fixes a single file that failed check_syntax. The error is self-contained
    to this file, so no other project context is needed.
    """
    raw = (await asyncio.to_thread(
        complete,
        "You are a senior engineer fixing a syntax error in a generated project file. "
        "Return ONLY the full corrected file content. No markdown, no explanation, no backticks.",
        f"File: {path}\n\nSyntax error: {error_message}\n\nFile content:\n{content}",
        8000,
    )).strip()

    return strip_code_fences(raw)

PROTOCODE_FIX_URL = "http://localhost:8001/api/fix-code"

# Files that often hold the real cause even when the error doesn't name them.
_KEY_FILES = {
    "main.py", "models.py", "schemas.py", "crud.py", "database.py", "config.py",
    "security.py", "deps.py", "dependencies.py", "settings.py", "urls.py",
    "views.py", "serializers.py", "requirements.txt", "package.json",
    "app.js", "server.js", "index.js",
}


def _norm_path(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def _post_fix(payload: dict) -> dict:
    request = urllib.request.Request(
        PROTOCODE_FIX_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.loads(response.read().decode("utf-8"))


async def fix_test_failure(files: list, stdout: str, stderr: str, test_code: str, runner: str) -> list[dict] | None:
    """
    Sends the failing test output and the relevant project files to ProtoCode's
    shared fixer (/api/fix-code). Returns [{"path", "content"}] patches, or None.
    """
    output = f"{stdout[-6000:]}\n{stderr[-2000:]}"
    contents = {_norm_path(f.path): f.content for f in files}
    paths = list(contents)

    # Files named in the traceback first, then key files, all in FULL.
    mentioned = [p for p in paths if p in output or p.replace("/", "\\") in output]
    key = [
        p for p in paths
        if p not in mentioned and (
            p.rsplit("/", 1)[-1] in _KEY_FILES
            or "/routers/" in p
            or "/routes/" in p
        )
    ]
    selected, budget = [], 150_000
    for p in mentioned + key:
        content = contents[p]
        if len(content) > budget:
            continue
        budget -= len(content)
        selected.append({"path": p, "content": content})

    error_log = (
        f"Test output:\n{output}\n\n"
        f"Test file (NOT part of the project, do not change it):\n{test_code[:3000]}\n\n"
        "These automated tests were run against the application and FAILED. "
        "Fix the APPLICATION code so the tests pass. Never change the test file."
    )

    try:
        result = await asyncio.to_thread(
            _post_fix,
            {"error_log": error_log, "files": selected, "all_paths": paths},
        )
    except Exception as e:
        print(f"[auto-fix] could not reach ProtoCode: {e}")
        return None

    if result.get("explanation"):
        print(f"[auto-fix] {result['explanation']}")

    patches = [
        {"path": f["path"], "content": f["content"]}
        for f in result.get("files", [])
        if f.get("path") and f.get("content")
    ]
    return patches or None

async def fix_wrong_test(files: list, output: str, test_code: str) -> str | None:
    """Ask the LLM to correct the TEST when failures show it used the wrong
    field names/types. Returns the new test code, or None."""
    schema_files = [
        f for f in files
        if any(k in f.path.lower() for k in ("schema", "model", "database", "depend"))
    ]
    context = "\n\n".join(f"--- {f.path} ---\n{f.content}" for f in schema_files)[:9000]

    system = (
        "You fix pytest files. You are given the project's schema/model files, a pytest "
        "test file, and its failure output. If the test sends wrong field names, types, "
        "or missing required fields (for example a 422), correct the TEST so it matches "
        "the schemas exactly. Return ONLY the full corrected Python test file, with no "
        "markdown, no explanation and no backticks."
    )
    user = (
        f"Schemas and models:\n{context}\n\n"
        f"Failure output:\n{output[-2500:]}\n\n"
        f"Test file:\n{test_code}"
    )
    try:
        out = await asyncio.to_thread(complete, system, user, 3500)
    except Exception as e:
        print(f"[auto-fix] test repair failed: {e}")
        return None
    code = strip_code_fences(out.strip())
    return fix_known_import_mistakes(ensure_stdlib_imports(code)) if "def test_" in code else None