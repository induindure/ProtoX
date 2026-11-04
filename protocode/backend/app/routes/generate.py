import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.code_generator import generate_code
from app.services.code_fixer import fix_code, _llm, message_text, parse_json_loose

router = APIRouter()


class FileItem(BaseModel):
    path: str
    content: str


class FixRequest(BaseModel):
    error_log: str
    files: list[FileItem]
    all_paths: list[str] = []
    tech_stack: str = ""


@router.post("/fix-code")
def fix_code_endpoint(request: FixRequest):
    try:
        return fix_code(
            request.error_log,
            [f.model_dump() for f in request.files],
            request.all_paths,
            request.tech_stack,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class CodeRequest(BaseModel):
    idea: str
    tech_stack: str
    database_url: str | None = None


@router.post("/generate-code")
async def generate_code_endpoint(request: CodeRequest):
    try:
        result = await generate_code(request.idea, request.tech_stack, request.database_url)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class ChatEditRequest(BaseModel):
    instruction: str
    files: list[dict]          # [{"path": ..., "content": ...}]
    tech_stack: str = ""


_PLAN_SYSTEM = (
    "You help edit a generated full-stack project. You get a user request and the "
    "list of project files with sizes. Choose which EXISTING files must be read and "
    "edited to do the request (max 8, exact paths from the list). Also list NEW files "
    "that must be created. Return ONLY JSON, no markdown: "
    '{"read": ["path", ...], "new_files": ["path", ...]}'
)

CHAT_BUDGET = 16_000  # chars of file content sent to the editor


def _plan_files(instruction: str, clean: list[dict], tech_stack: str):
    listing = "\n".join(f"{f['path']} ({len(f['content'])} chars)" for f in clean[:400])
    prompt = (
        f"Tech stack: {tech_stack or 'unknown'}\n\n"
        f"User request:\n{instruction}\n\n"
        f"Project files:\n{listing}"
    )
    try:
        resp = _llm().invoke([SystemMessage(content=_PLAN_SYSTEM), HumanMessage(content=prompt)])
        data = parse_json_loose(message_text(resp).strip()) or {}
    except Exception as e:
        print(f"[chat-edit] planner failed: {e}")
        return [], []
    known = {f["path"] for f in clean}
    read = [p for p in data.get("read", []) if p in known]
    new = [p for p in data.get("new_files", []) if isinstance(p, str)]
    return read, new


@router.post("/chat-edit")
def chat_edit(req: ChatEditRequest):
    def _text(v):
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return str(v.get("value") or "")
        return str(v)

    clean = [
        {"path": str(f.get("path", "")), "content": _text(f.get("content"))}
        for f in req.files
    ]
    by_path = {f["path"]: f for f in clean}

    # Step 1: the model looks at the file list and picks what to read
    read, new_files = _plan_files(req.instruction, clean, req.tech_stack)
    print(f"[chat-edit] plan read={read} new={new_files}")

    # fallback if the planner returned nothing: old keyword scoring
    if not read:
        words = set(re.findall(r"[a-z]{4,}", req.instruction.lower()))

        def score(f):
            return sum(w in (f["path"] + " " + f["content"]).lower() for w in words)

        read = [f["path"] for f in sorted(clean, key=score, reverse=True)[:8]]

    picked, skipped, budget = [], [], CHAT_BUDGET
    for p in read:
        f = by_path[p]
        if len(f["content"]) > budget:
            skipped.append(p)
            continue
        budget -= len(f["content"])
        picked.append(f)

    error_log = (
        "USER CHANGE REQUEST (this is not an error):\n"
        f"{req.instruction}\n\n"
        "Rules:\n"
        "- Edit the provided files as needed. You MAY create new files (new pages, "
        "components, routes, endpoints) when the request needs them, only under "
        "frontend/ or backend/.\n"
        "- Wire new files in: register new pages in the router/App file, include new "
        "backend routers in the main file, and add nav links where it makes sense.\n"
        "- Never hardcode sample data, fake numbers or placeholder content. Data must "
        "come from the app's own database through real API endpoints.\n"
        "- Return complete file contents for every file you change or create.\n"
        + (f"- Files you probably need to create: {', '.join(new_files)}\n" if new_files else "")
    )
    try:
        result = fix_code(error_log, picked, [f["path"] for f in clean], req.tech_stack)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    if skipped:
        result["explanation"] = (
            (result.get("explanation") or "")
            + f" (Could not read, too large for one pass: {', '.join(skipped)})"
        ).strip()
    return result