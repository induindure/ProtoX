"""
Finds buttons that do nothing and asks the LLM to implement the feature
(frontend + backend) or remove the button. Returns the files unchanged on any failure.
"""

import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.completeness_checker import _norm
from app.services.llm_provider import get_llm, message_text, parse_json_loose

_BUTTON_RE = re.compile(r"<button\b((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)>(.*?)</button>", re.S | re.I)
_HANDLER_RE = re.compile(r"""(@click|v-on:click|onClick|\btype\s*=\s*["']submit["'])""", re.I)
_BACKEND_HINT = re.compile(r"(router|route|view|schema|serializer|crud|model|url|main|depend|auth)", re.I)
_FRONT_HINT = re.compile(r"(api|client|store|service)", re.I)

_SYSTEM = """You are completing a generated full-stack project. Some buttons in the frontend do nothing
because they have no click handler. For EACH one, do ONE of these:
(a) Implement the feature fully, with the smallest working change: a modal or form in the
    frontend, an API function using the project's existing API client, and the matching backend
    endpoint (plus schema/crud changes) following the patterns already in the project.
(b) If it cannot be implemented sensibly with the existing models, remove the button.

Rules:
- Keep the project's framework and structure. Use the existing API client; never hardcode URLs or data.
- Never use pydantic in Django projects. Never use Django features in FastAPI projects.
- Never let the user edit the field that identifies them in the auth token (username/email).
- Do not touch unrelated code.
- Return ONLY the files you changed, each with its COMPLETE new content (new files allowed).

Respond with ONLY a JSON object, no markdown fences:
{"explanation": "<one sentence>", "files": [{"path": "<path>", "content": "<full file content>"}]}
"""


def find_dead_buttons(files):
    found = {}
    for f in files:
        path = _norm(f["path"])
        if not path.startswith("frontend/") or not path.endswith((".vue", ".jsx", ".tsx")):
            continue
        content = f["content"]
        has_form = "<form" in content.lower()
        for m in _BUTTON_RE.finditer(content):
            attrs, inner = m.group(1), m.group(2)
            if _HANDLER_RE.search(attrs) or "v-bind" in attrs or "{..." in attrs:
                continue
            if has_form and "type" not in attrs.lower():
                continue  # default submit button inside a form
            label = re.sub(r"<[^>]+>|\{\{.*?\}\}|\s+", " ", inner).strip()[:40] or "(icon button)"
            found.setdefault(path, []).append(label)
    return found


def _context_files(files, flagged):
    ctx = {}
    for f in files:
        p = _norm(f["path"])
        if p in flagged:
            ctx[p] = f
        elif p.startswith("backend/") and p.endswith(".py") and _BACKEND_HINT.search(p):
            ctx[p] = f
        elif p.startswith("frontend/") and p.endswith((".js", ".ts")) and _FRONT_HINT.search(p):
            ctx[p] = f
    return list(ctx.values())


def fix_dead_buttons(files, tech_stack="", max_files=3):
    dead = find_dead_buttons(files)
    if not dead:
        return files

    flagged = dict(list(dead.items())[:max_files])
    try:
        issues = "\n".join(
            f"- {p}: button(s) with no click handler: {', '.join(labels)}"
            for p, labels in flagged.items()
        )
        context = "\n\n".join(
            f"### {_norm(f['path'])}\n{f['content']}" for f in _context_files(files, set(flagged))
        )
        prompt = (
            f"Tech stack: {tech_stack or 'unknown'}\n\nProblems:\n{issues}\n\n"
            "All files in the project:\n"
            + "\n".join(_norm(f["path"]) for f in files[:400])
            + f"\n\nRelevant files:\n\n{context}"
        )
        llm = get_llm(max_tokens=16000, temperature=0.2, small=True)
        response = llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
        data = parse_json_loose(message_text(response).strip())
    except Exception as e:
        print(f"[feature-completer] failed, keeping files unchanged: {e}")
        return files

    if not data:
        print("[feature-completer] unreadable reply, keeping files unchanged")
        return files

    changed = {}
    for f in data.get("files", []):
        path = _norm(f.get("path", ""))
        if path.startswith(("backend/", "frontend/")) and f.get("content"):
            changed[path] = f["content"]
    if not changed:
        return files

    merged, seen = [], set()
    for f in files:
        p = _norm(f["path"])
        if p in changed:
            merged.append({**f, "content": changed[p]})
            seen.add(p)
        else:
            merged.append(f)
    for p, c in changed.items():
        if p not in seen:
            merged.append({"path": p, "content": c})

    print(f"[feature-completer] {data.get('explanation', '')} -> {list(changed)}")
    return merged