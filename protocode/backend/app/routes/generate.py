
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.code_generator import generate_code

router = APIRouter()

class CodeRequest(BaseModel):
    idea: str
    tech_stack: str

@router.post("/generate-code")
async def generate_code_endpoint(request: CodeRequest):
    try:
        result = await generate_code(request.idea, request.tech_stack)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))