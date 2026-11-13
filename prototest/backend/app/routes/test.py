from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.routes.services.project_store import save_project, get_project

from app.routes.services.syntax_checker import check_syntax
from app.routes.services.stack_runner import get_runner
from app.routes.services.project_builder import build_project_dir
from app.routes.services.test_generator import generate_test_file
from app.routes.services.test_executor import run_pytest, run_jest, cleanup
from app.routes.services.code_fixer import fix_syntax_error, fix_test_failure, fix_wrong_test
import asyncio
from fastapi import HTTPException
from app.routes.services.llm_provider import complete

router = APIRouter()

MAX_AUTO_FIX_ATTEMPTS = 3

class FileInput(BaseModel):
    path: str
    content: str


class TestRequest(BaseModel):
    files: List[FileInput]
    project_name: str
    tech_stack: str

import re

class FixPromptRequest(BaseModel):
    files: List[FileInput]
    output: str
    test_code: str = ""
    source: str = "test"        # "test" or "preview"
    user_note: str = ""

ERROR_RE = re.compile(r"traceback|error|exception|failed|refused|cannot find", re.I)

@router.post("/store-project")
async def store_project(request: TestRequest):
    project_id = save_project({
        "files": [f.dict() for f in request.files],
        "project_name": request.project_name,
        "tech_stack": request.tech_stack,
    })
    return {"project_id": project_id}


@router.get("/get-project/{project_id}")
async def get_project_endpoint(project_id: str):
    project = get_project(project_id)
    if not project:
        return {"error": "Project not found or expired"}
    return project


@router.post("/test")
async def run_tests(request: TestRequest):
    # Step 1: fast syntax pre-check per file (unchanged, cheap and instant)
    syntax_results = []
    for file in request.files:
        syntax = check_syntax(file.path, file.content)
        syntax_results.append({"path": file.path, "syntax": syntax})

    syntax_failed = [r for r in syntax_results if r["syntax"]["status"] == "fail"]

    # Step 2: determine runner from tech_stack
    runner = get_runner(request.tech_stack)

    if runner == "unsupported":
        return {
            "project_name": request.project_name,
            "tech_stack": request.tech_stack,
            "summary": {"total": len(syntax_results), "syntax_failed": len(syntax_failed)},
            "syntax_results": syntax_results,
            "test_execution": {
                "ran": False,
                "reason": f"No test runner configured for stack: {request.tech_stack}",
            },
        }

    project_dir = None
    try:
        # Step 3: reconstruct project on disk
        project_dir = build_project_dir(request.files)

        # Step 4: generate real test code targeting the actual files
        test_code = await generate_test_file(request.files, runner)

        # Step 5: actually execute the tests
        if runner == "pytest":
            execution = run_pytest(project_dir, test_code)
        else:
            execution = run_jest(project_dir, test_code)

        execution["ran"] = True
        execution["generated_test_code"] = test_code

    finally:
        if project_dir:
            cleanup(project_dir)

    return {
        "project_name": request.project_name,
        "tech_stack": request.tech_stack,
        "summary": {
            "total": len(syntax_results),
            "syntax_failed": len(syntax_failed),
            "tests_passed": execution.get("passed", False),
        },
        "syntax_results": syntax_results,
        "test_execution": execution,
    }


@router.post("/auto-fix")
async def auto_fix(request: TestRequest):
    """
    Repeatedly fixes syntax errors and failing tests via the LLM and re-checks,
    up to MAX_AUTO_FIX_ATTEMPTS total cycles. Only the in-memory working copy of
    the files is mutated — nothing is written back to ProtoCode's project store.
    """
    files = {f.path: f.content for f in request.files}
    runner = get_runner(request.tech_stack)

    iterations = []
    final_execution = None
    success = False

    test_code = None
    test_repair_used = False
    for attempt in range(1, MAX_AUTO_FIX_ATTEMPTS + 1):
        syntax_results = [
            {"path": path, "syntax": check_syntax(path, content)}
            for path, content in files.items()
        ]
        syntax_failed = [r for r in syntax_results if r["syntax"]["status"] == "fail"]

        if syntax_failed:
            fixed_files = []
            for r in syntax_failed:
                path = r["path"]
                files[path] = await fix_syntax_error(path, files[path], r["syntax"]["message"])
                fixed_files.append(path)
            iterations.append({
                "attempt": attempt,
                "fix_type": "syntax",
                "fixed_files": fixed_files,
                "test_execution": None,
            })
            continue

        if runner == "unsupported":
            final_execution = {
                "ran": False,
                "reason": f"No test runner configured for stack: {request.tech_stack}",
            }
            iterations.append({
                "attempt": attempt,
                "fix_type": None,
                "fixed_files": [],
                "test_execution": final_execution,
            })
            success = True
            break

        file_inputs = [FileInput(path=p, content=c) for p, c in files.items()]
        project_dir = None
        try:
            project_dir = build_project_dir(file_inputs)
            if test_code is None:
                test_code = await generate_test_file(file_inputs, runner)
            if runner == "pytest":
                execution = run_pytest(project_dir, test_code)
            else:
                execution = run_jest(project_dir, test_code)
            execution["ran"] = True
            execution["generated_test_code"] = test_code
        finally:
            if project_dir:
                cleanup(project_dir)

        final_execution = execution
        iteration = {
            "attempt": attempt,
            "fix_type": "test",
            "fixed_files": [],
            "test_execution": execution,
        }
        iterations.append(iteration)

        if execution.get("passed"):
            success = True
            break

        out_text = execution.get("stdout", "") + "\n" + execution.get("stderr", "")
        new_test = None
        test_side_failure = (
            "422" in out_text
            or "KeyError" in out_text
            or "NameError" in out_text
            or "ERROR collecting test_generated.py" in out_text
        )
        if runner == "pytest" and test_side_failure and not test_repair_used:
            new_test = await fix_wrong_test(file_inputs, out_text, test_code)
        if new_test:
            test_repair_used = True
            test_code = new_test        # retry with the repaired test
            iteration["fixed_files"] = ["(test file)"]
            continue

        patch = await fix_test_failure(
            file_inputs, execution.get("stdout", ""), execution.get("stderr", ""), test_code, runner
        )
        if not patch:
            break

        for entry in patch:
            files[entry["path"]] = entry["content"]
        iteration["fixed_files"] = [entry["path"] for entry in patch]

    # Recompute a fresh, accurate syntax snapshot of the final file state —
    # cheap (no LLM call) and avoids reporting a stale pre-fix result if the
    # loop exhausted its attempts right after a syntax fix.
    final_syntax_results = [
        {"path": path, "syntax": check_syntax(path, content)}
        for path, content in files.items()
    ]

    return {
        "project_name": request.project_name,
        "tech_stack": request.tech_stack,
        "success": success,
        "attempts_used": len(iterations),
        "iterations": iterations,
        "final_syntax_results": final_syntax_results,
        "final_test_execution": final_execution,
        "files": [{"path": p, "content": c} for p, c in files.items()],
    }

@router.post("/fix-prompt")
async def fix_prompt(request: FixPromptRequest):
    out = request.output
    is_preview = request.source == "preview"

    if is_preview and not request.user_note.strip() and not ERROR_RE.search(out):
        return {"prompt": "", "no_issue": True}

    mentioned, keyed = [], []
    for f in request.files:
        p = f.path.replace("\\", "/")
        low = p.lower()
        name = p.rsplit("/", 1)[-1]
        if name and (name in out or p in out):
            mentioned.append(f)
        elif is_preview:
            if any(k in low for k in ("main", "app.", "router", "vite.config",
                                      "package.json", "settings", "requirements")):
                keyed.append(f)
        elif "backend/" in low and any(
            k in low for k in ("schema", "model", "route", "router", "main", "view", "serializer")
        ):
            keyed.append(f)

    picked, budget = [], 7000
    for f in mentioned + keyed:
        if len(f.content) > budget:
            continue
        budget -= len(f.content)
        picked.append(f"--- {f.path} ---\n{f.content}")

    if is_preview:
        system = (
            "You write instructions for an AI code editor. You are given the logs of a web app "
            "in a preview, an optional description from the user, and some of its code. "
            "A user description can include functional bugs, UI improvements, styling changes, "
            "or design requests. These all count as valid problems to address. "
            "If the user description is non-empty, NEVER reply with NO_ISSUE, even if the logs "
            "show no errors. Follow the user's description and write ONE short instruction "
            "(max 120 words) telling the editor what to change in the APP code. "
            "Only reply with exactly NO_ISSUE if the logs show no real error AND the user "
            "description is empty. Name the exact files, components or settings where possible. "
            "Plain text only."
        )
        user = (
            f"User description: {request.user_note or '(none)'}\n\n"
            f"Logs:\n{out[-3000:]}\n\nCode:\n{chr(10).join(picked)}"
        )

    try:
        text = await asyncio.to_thread(complete, system, user, 2000)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    text = text.strip()
    if not text:
        raise HTTPException(status_code=502, detail="Empty response from model")
    if text.upper().startswith("NO_ISSUE"):
        return {"prompt": "", "no_issue": True}
    return {"prompt": text}