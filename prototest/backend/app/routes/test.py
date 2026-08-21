from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.routes.services.project_store import save_project, get_project

from app.routes.services.syntax_checker import check_syntax
from app.routes.services.stack_runner import get_runner
from app.routes.services.project_builder import build_project_dir
from app.routes.services.test_generator import generate_test_file
from app.routes.services.test_executor import run_pytest, run_jest, cleanup

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

router = APIRouter()

class FileInput(BaseModel):
    path: str
    content: str

class TestRequest(BaseModel):
    files: List[FileInput]
    project_name: str
    tech_stack: str

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