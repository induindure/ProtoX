import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.file_builder import build_file_tree
from app.services.dependency_scanner import build_requirements_txt
from app.services.typing_fixer import fix_missing_typing_imports
from app.services.pydantic_fixer import fix_pydantic_v2_settings_import
from app.services.env_builder import apply_database_url

load_dotenv()


SYSTEM_PROMPT = """
You are a senior software engineer. Given an app idea and a tech stack, generate a complete, realistic starter project.

Return ONLY a valid JSON object with this exact structure, no extra text, no markdown:
{
  "project_name": "snake_case_name",
  "description": "one line description",
  "files": [
    {
      "path": "relative/path/to/file.ext",
      "content": "full file content as a string"
    }
  ]
}

Requirements:
- Generate between 12 and 18 files
- Include: README.md, proper config files, folder structure matching the tech stack
- For React frontend: include App.jsx, at least 4 components, routing with react-router-dom, one API service file, basic CSS
- For backend: include main entry point, at least 3 routes, 2 data models, database config, requirements.txt or package.json
- Write real, working code with actual logic — not placeholder comments
- Include at least one authentication-related file (login route or auth middleware)
- Include a .env.example file
- If a specific Database URL is given in the user message, use that exact connection string
  in the database config file and .env.example — do not invent a different one. If none is
  given, default to a local SQLite database for simplicity.
- Use Pydantic v2 syntax. For settings/config classes, import BaseSettings from the
  "pydantic_settings" package (`from pydantic_settings import BaseSettings`), NOT from
  "pydantic" directly — BaseSettings was removed from the main pydantic package in v2.
- Do not generate the same boilerplate for every project — tailor code specifically to the described app
"""


def fix_react_package_json(files: list[dict]) -> list[dict]:
    """
    Deterministically fixes React package.json files.

    The LLM sometimes generates:
        "start": "react-scripts start"

    without adding react-scripts to dependencies.

    This function ensures CRA projects always have the dependency they need.
    """

    for file in files:
        path = file.get("path", "")

        if not path.endswith("package.json"):
            continue

        try:
            package_data = json.loads(file.get("content", "{}"))
        except (json.JSONDecodeError, TypeError):
            continue

        dependencies = package_data.setdefault("dependencies", {})
        scripts = package_data.get("scripts", {})

        # If the generated project uses react-scripts,
        # make sure react-scripts is actually installed.
        uses_react_scripts = any(
            "react-scripts" in str(command)
            for command in scripts.values()
        )

        if uses_react_scripts:
            dependencies["react-scripts"] = "5.0.1"

        # Write the corrected package.json back.
        file["content"] = json.dumps(
            package_data,
            indent=2
        )

    return files


async def generate_code(
    idea: str,
    tech_stack: str,
    database_url: str | None = None
):
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="openai/gpt-oss-120b",
        temperature=0.5,
        max_tokens=7000,
        reasoning_effort="low",
    )

    user_content = f"App idea:\n{idea}\n\nTech stack: {tech_stack}"

    if database_url:
        user_content += (
            f"\n\nDatabase URL to use exactly as given "
            f"(do not invent a different one): {database_url}"
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]

    response = await llm.ainvoke(messages)

    print(
        "RAW RESPONSE CONTENT:",
        repr(response.content)
    )

    print(
        "RESPONSE METADATA:",
        response.response_metadata
    )

    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]

        if raw.startswith("json"):
            raw = raw[4:]

    raw = raw.strip()

    print("RAW LENGTH:", len(raw))
    print("RAW PREVIEW:", raw[:300])

    try:
        parsed = json.loads(raw)

    except json.JSONDecodeError:

        repair_messages = [
            SystemMessage(
                content=(
                    "You output broken JSON. "
                    "Return ONLY the corrected, valid JSON — "
                    "no markdown, no explanation."
                )
            ),
            HumanMessage(content=raw),
        ]

        repair_response = await llm.ainvoke(
            repair_messages
        )

        repaired = repair_response.content.strip()

        if repaired.startswith("```"):
            repaired = repaired.split("```")[1]

            if repaired.startswith("json"):
                repaired = repaired[4:]

        parsed = json.loads(
            repaired.strip()
        )

    print(
        "PARSED KEYS:",
        list(parsed.keys())
    )

    # ---------------------------------------------------------
    # Deterministic Python fixes
    # ---------------------------------------------------------

    parsed["files"] = fix_missing_typing_imports(
        parsed["files"]
    )

    parsed["files"] = fix_pydantic_v2_settings_import(
        parsed["files"]
    )

    # Fix React package.json dependencies.
    #
    # This catches the exact problem we just encountered:
    # "react-scripts" being used in scripts but missing
    # from dependencies.
    if "React" in tech_stack:
        parsed["files"] = fix_react_package_json(
            parsed["files"]
        )

    # ---------------------------------------------------------
    # Backend requirements
    # ---------------------------------------------------------

    if "FastAPI" in tech_stack or "Django" in tech_stack:

        backend_framework = (
            "FastAPI"
            if "FastAPI" in tech_stack
            else "Django"
        )

        req_content = build_requirements_txt(
            parsed["files"],
            backend_framework
        )

        existing_req = next(
            (
                f
                for f in parsed["files"]
                if f["path"].endswith(
                    "requirements.txt"
                )
            ),
            None
        )

        if existing_req:
            existing_req["content"] = req_content

        else:
            # Find the backend folder prefix from
            # an existing backend file.
            backend_file = next(
                (
                    f
                    for f in parsed["files"]
                    if f["path"].startswith(
                        "backend/"
                    )
                ),
                None
            )

            req_path = (
                "backend/requirements.txt"
                if backend_file
                else "requirements.txt"
            )

            parsed["files"].append(
                {
                    "path": req_path,
                    "content": req_content
                }
            )

    # ---------------------------------------------------------
    # Database URL
    # ---------------------------------------------------------

    parsed["files"] = apply_database_url(
        parsed["files"],
        database_url
    )

    # ---------------------------------------------------------
    # File tree
    # ---------------------------------------------------------

    parsed["file_tree"] = build_file_tree(
        parsed["files"]
    )

    return parsed