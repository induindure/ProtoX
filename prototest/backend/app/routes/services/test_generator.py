"""
Generates real pytest/jest test code for a reconstructed ProtoCode project.
Unlike ai_reviewer.py, this produces executable test files, not a text review.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

PYTEST_SYSTEM_PROMPT = """
You are a senior backend engineer writing pytest tests for a FastAPI/Django project.
You will be given the full contents of a generated project's files.

Write ONE pytest test file that imports the real modules/functions shown to you
(use the exact file paths and names given — do not invent filenames) and tests
the main routes/functions with realistic inputs.

Return ONLY raw Python test code. No markdown, no explanation, no backticks.
Include at least 3 test functions covering the main functionality.
"""

JEST_SYSTEM_PROMPT = """
You are a senior backend engineer writing jest tests for a Node/Express project.
You will be given the full contents of a generated project's files.

Write ONE jest test file that imports/requires the real modules shown to you
(use the exact file paths and names given — do not invent filenames) and tests
the main routes/functions with realistic inputs.

Return ONLY raw JavaScript test code. No markdown, no explanation, no backticks.
Include at least 3 test cases covering the main functionality.
"""


async def generate_test_file(files: list, runner: str) -> str:
    """
    files: request.files (list of objects with .path and .content)
    runner: "pytest" or "jest"
    Returns raw test file content as a string.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    from groq import Groq
    client = Groq(api_key=api_key)

    system_prompt = PYTEST_SYSTEM_PROMPT if runner == "pytest" else JEST_SYSTEM_PROMPT

    # only send backend-relevant files, keep prompt size sane
    relevant = [f for f in files if _is_backend_file(f.path, runner)]

    file_dump = "\n\n".join(
        f"--- {f.path} ---\n{f.content[:2000]}" for f in relevant
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Project files:\n\n{file_dump}"},
        ],
        max_tokens=3000,
        reasoning_effort="low",
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("python") or raw.startswith("javascript") or raw.startswith("js"):
            raw = raw.split("\n", 1)[1]
    return raw.strip()


def _is_backend_file(path: str, runner: str) -> bool:
    if runner == "pytest":
        return path.endswith(".py")
    return path.endswith(".js") or path.endswith(".jsx") or path.endswith(".ts")