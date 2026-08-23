"""
Uses the same Groq LLM that writes tests to patch broken code: either a single
file that failed check_syntax, or the set of application files a failing
pytest/jest run points at.
"""

import os
import json
from dotenv import load_dotenv

from app.routes.services.llm_utils import strip_code_fences
from app.routes.services.test_generator import _is_backend_file

load_dotenv()


def _client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    from groq import Groq
    return Groq(api_key=api_key)


async def fix_syntax_error(path: str, content: str, error_message: str) -> str:
    """
    Fixes a single file that failed check_syntax. The error is self-contained
    to this file, so no other project context is needed.
    """
    client = _client()

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior engineer fixing a syntax error in a generated project file. "
                    "Return ONLY the full corrected file content. No markdown, no explanation, no backticks."
                ),
            },
            {
                "role": "user",
                "content": f"File: {path}\n\nSyntax error: {error_message}\n\nFile content:\n{content}",
            },
        ],
        max_tokens=3000,
        reasoning_effort="low",
    )

    raw = response.choices[0].message.content.strip()
    return strip_code_fences(raw)


async def fix_test_failure(files: list, stdout: str, stderr: str, test_code: str, runner: str) -> list[dict] | None:
    """
    files: request.files-style objects with .path / .content
    Returns a list of {"path": ..., "content": ...} patches to apply, or
    None if the LLM couldn't determine a fix (empty/unparseable response).
    """
    client = _client()

    relevant = [f for f in files if _is_backend_file(f.path, runner)]
    file_dump = "\n\n".join(f"--- {f.path} ---\n{f.content[:2000]}" for f in relevant)

    system_prompt = (
        "You are a senior engineer. A test file was written and run against the application "
        "files below, and it failed. Diagnose the failure from the test output and fix the "
        "APPLICATION code (never the test file) so the tests pass.\n\n"
        'Return ONLY raw JSON: an array of objects with "path" and "content" keys, one per '
        "file you changed, containing that file's FULL corrected content. Omit files you didn't "
        "change. No markdown, no explanation, no backticks."
    )

    user_prompt = (
        f"Test file (do not modify):\n{test_code}\n\n"
        f"Test run stdout:\n{stdout[-3000:]}\n\n"
        f"Test run stderr:\n{stderr[-1500:]}\n\n"
        f"Application files:\n{file_dump}"
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=4000,
        reasoning_effort="low",
    )

    raw = response.choices[0].message.content.strip()
    raw = strip_code_fences(raw)

    try:
        patches = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(patches, list) or not patches:
        return None

    valid = [p for p in patches if isinstance(p, dict) and "path" in p and "content" in p]
    return valid or None
