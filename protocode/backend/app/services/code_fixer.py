"""
Fixes a generated project that crashes when it runs. Preview sends the error
output and the relevant files; the LLM returns only the files it changed.
"""

import json
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.services.completeness_checker import _norm

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
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="openai/gpt-oss-120b",
        temperature=0.2,
        max_tokens=16000,
        reasoning_effort="medium",
    )


def fix_code(error_log: str, files: list[dict], all_paths: list[str], tech_stack: str = "") -> dict:
    context = "\n\n".join(
        f"### {_norm(f['path'])}\n{f['content'][:12000]}" for f in files
    )
    prompt = (
        f"Tech stack: {tech_stack or 'unknown'}\n\n"
        f"Error output:\n{error_log[-8000:]}\n\n"
        f"All files in the project:\n" + "\n".join(all_paths[:400]) + "\n\n"
        f"Relevant files:\n\n{context}"
    )

    response = _llm().invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
    text = response.content.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {"explanation": "AI returned no usable fix", "files": []}

    data = json.loads(text[start:end + 1])

    fixed = []
    for f in data.get("files", []):
        path = _norm(f.get("path", ""))
        if path.startswith(("backend/", "frontend/")) and f.get("content"):
            fixed.append({"path": path, "content": f["content"]})

    print(f"[code-fixer] {data.get('explanation', '')} -> {[f['path'] for f in fixed]}")
    return {"explanation": data.get("explanation", ""), "files": fixed}