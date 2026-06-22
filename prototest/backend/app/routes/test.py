from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.routes.services.syntax_checker import check_syntax
from app.routes.services.ai_reviewer import review_code

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
    results = []

    for file in request.files:
        syntax = check_syntax(file.path, file.content)
        ai_feedback = await review_code(file.path, file.content)

        results.append({
            "path": file.path,
            "syntax": syntax,
            "ai_feedback": ai_feedback,
        })

    total = len(results)
    passed = sum(1 for r in results if r["syntax"]["status"] == "pass")
    warned = sum(1 for r in results if r["syntax"]["status"] == "warn")
    failed = sum(1 for r in results if r["syntax"]["status"] == "fail")
    skipped = sum(1 for r in results if r["syntax"]["status"] == "skip")

    return {
        "project_name": request.project_name,
        "tech_stack": request.tech_stack,
        "summary": {
            "total": total,
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "skipped": skipped,
        },
        "results": results,
    }
