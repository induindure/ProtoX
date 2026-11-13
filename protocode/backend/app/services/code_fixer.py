"""
Fixes a generated project that crashes when it runs. Preview sends the error
output and the relevant files; the LLM returns only the files it changed.
"""

import json
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.services.completeness_checker import _norm
from app.services.llm_provider import get_llm, message_text, parse_json_loose

import json_repair

def _parse(text: str):
    data = parse_json_loose(text)
    if data is None:
        try:
            data = json_repair.loads(text)   # fixes bad escapes, trailing commas, truncated JSON
        except Exception:
            data = None
    return data if isinstance(data, dict) and "files" in data else None

_SYSTEM = """You are fixing a generated full-stack project that fails when it runs.
You get the error output, the list of all project files, and the contents of the relevant files.

Find the ROOT CAUSE and fix it with the smallest correct change.
- Return ONLY the files you changed, each with its COMPLETE new content.
- Keep the project's framework, structure and style. Do not rewrite unrelated code.
- If a package is missing, add it to requirements.txt or package.json.
- Never use pydantic in Django projects. Never use Django features in FastAPI projects.

Respond with ONLY a JSON object, no explanation outside it, no markdown fences:
{"explanation": "<one sentence describing the fix>",
 "files": [{"path": "<exact path as given>", "content": "<full file content>"}]}
"""


def _llm():
    return get_llm(max_tokens=16000, temperature=0.2, small=True)


def fix_code(error_log: str, files: list[dict], all_paths: list[str], tech_stack: str = "") -> dict:
    context = "\n\n".join(
        f"### {_norm(f['path'])}\n{f['content']}" for f in files
    )
    prompt = (
        f"Tech stack: {tech_stack or 'unknown'}\n\n"
        f"Error output:\n{error_log[-16000:]}\n\n"
        f"All files in the project:\n" + "\n".join(all_paths[:400]) + "\n\n"
        f"Relevant files:\n\n{context}"
    )

    data = None
    for attempt in range(2):
        response = _llm().invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
        text = message_text(response).strip()
        data = _parse(text)
        if data is not None:
            break
        print(f"[code-fixer] attempt {attempt + 1}: invalid JSON. Start of reply: {text[:300]!r}")
    if data is None:
        return {"explanation": "AI returned an unreadable fix", "files": []}
    fixed = []
    for f in data.get("files", []):
        path = _norm(f.get("path", ""))
        if path.startswith(("backend/", "frontend/")) and f.get("content"):
            fixed.append({"path": path, "content": f["content"]})

    print(f"[code-fixer] {data.get('explanation', '')} -> {[f['path'] for f in fixed]}")
    return {"explanation": data.get("explanation", ""), "files": fixed}