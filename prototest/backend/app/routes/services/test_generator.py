"""
Generates real pytest/jest test code for a reconstructed ProtoCode project.
Unlike ai_reviewer.py, this produces executable test files, not a text review.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
import re

from app.routes.services.llm_utils import strip_code_fences

load_dotenv()

PYTEST_SYSTEM_PROMPT = """
You are a senior backend engineer writing pytest tests for a FastAPI or Django project.
You will be given the full contents of a generated project's files, with paths like "backend/app/main.py".

Write ONE pytest test file that imports the real modules shown to you and tests the
main routes with realistic inputs. Include at least 3 test functions covering the
main functionality (registration/login and the main feature endpoints).

Return ONLY raw Python test code. No markdown, no explanation, no backticks.

TEST WHAT THE CODE ACTUALLY DOES:
- Read the route code before writing each assertion. Use the exact URL paths,
  HTTP methods, status codes (e.g. 200 vs 201), JSON field names and error
  messages that the code really uses. Never invent error messages; if unsure,
  assert only the status code.

TEST ISOLATION (both frameworks):
- Tests must not depend on each other. Every test creates its own data with
  unique usernames and emails (e.g. f"user_{uuid.uuid4().hex[:8]}").

=== FastAPI projects ===
- The test file runs from the project ROOT with "backend" as a Python package.
  Import with the full path, keeping the "backend." prefix
  (e.g. "from backend.app.main import app").
- Use a pytest fixture that, for EVERY test, creates a fresh in-memory SQLite engine:
    create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
  runs Base.metadata.create_all on it, and overrides the database dependency.
- Override the dependency with the REAL FUNCTION OBJECT that the routes use inside
  Depends(...), imported from the module the routes import it from:
    app.dependency_overrides[get_db] = override_get_db
  Never use strings as keys. Clear the overrides after each test.
- Create the TestClient inside the fixture, after the override is set.

=== Django projects ===
- The test file runs from the folder that contains manage.py, with pytest-django
  already configured and database access enabled. Do NOT use a "backend." prefix:
  import apps by their app name (e.g. "from core.models import Feed").
- Use rest_framework.test.APIClient. Use the URL paths defined in the project's
  urls.py files (or reverse() only with names that actually exist there).
- Use get_user_model() for users; create them with create_user(...).
- Override ONLY get_db. Never override other dependencies or access FastAPI internals
  (no __dependencies__).
- To check the database inside a test, open a session from the test's sessionmaker
  and use session.query(Model). Never use Model.query (that is Flask-SQLAlchemy).
"""

JEST_SYSTEM_PROMPT = """
You are a senior backend engineer writing jest tests for a Node/Express project.
You will be given the full contents of a generated project's files, with paths like "backend/models/User.js".

IMPORTANT: Your test file will be placed directly inside the "backend" folder,
at the same level as "models/", "routes/", "middleware/", etc. So if you see a
file at "backend/models/User.js", require/import it as "./models/User.js" —
NOT "../models/User.js". Strip the "backend/" prefix and treat paths as
relative to the backend folder itself, one level down (e.g. "./routes/auth.js",
"./models/User.js"), never one level up.

Write ONE jest test file that imports/requires the real modules shown to you
and tests the main routes/functions with realistic inputs.

Return ONLY raw JavaScript test code. No markdown, no explanation, no backticks.
Include at least 3 test cases covering the main functionality.

TEST WHAT THE CODE ACTUALLY DOES:
- Use the exact routes, status codes, JSON field names and error messages from the
  code. Never invent error messages; if unsure, assert only the status code.
- Every test creates its own data with unique usernames/emails
  (e.g. `user_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`),
  so tests never depend on each other.
"""

import re

def _strip_env_overrides(code: str) -> str:
    """
    Removes any 'process.env.DATABASE_URL = ...' or 'process.env.DB_URL = ...'
    lines the LLM writes into the test file — these override the real env vars
    our test harness sets, causing a mismatch between what the harness intends
    and what the test actually runs against.
    """
    code = re.sub(r'^\s*process\.env\.DATABASE_URL\s*=.*\n?', '', code, flags=re.MULTILINE)
    code = re.sub(r'^\s*process\.env\.DB_URL\s*=.*\n?', '', code, flags=re.MULTILINE)
    return code

def _strip_backend_prefix(code: str) -> str:
    """
    Deterministically removes 'backend.' prefixes from import statements,
    since tests are executed from inside the backend/ folder as the root.
    Catches: 'import backend.x', 'from backend.x import y', 'backend.x as y'
    """
    code = re.sub(r'\bfrom backend\.', 'from ', code)
    code = re.sub(r'\bimport backend\.', 'import ', code)
    return code

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
    raw = strip_code_fences(raw)

    if runner == "jest":
        raw = _strip_env_overrides(raw)

    return raw

def _is_backend_file(path: str, runner: str) -> bool:
    if runner == "pytest":
        return path.endswith(".py")
    return path.endswith(".js") or path.endswith(".jsx") or path.endswith(".ts")