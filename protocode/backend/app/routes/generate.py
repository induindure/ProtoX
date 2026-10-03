
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.code_generator import generate_code
from app.services.code_fixer import fix_code

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