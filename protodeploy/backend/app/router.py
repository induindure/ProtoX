import shutil
import requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .deployer import deploy_to_github, GH
from .extractor import extract_project

router = APIRouter(prefix="/api/protodeploy", tags=["protodeploy"])


@router.post("/deploy")
def deploy(
    file: UploadFile = File(...),
    github_token: str = Form(...),
    repo_name: str = Form(...),
):
    tmp = None
    try:
        root, tmp = extract_project(file.file.read())
        return deploy_to_github(root, github_token, repo_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


@router.get("/status")
def status(owner: str, repo: str):
    r = requests.get(f"{GH}/repos/{owner}/{repo}/actions/runs?per_page=1")
    runs = r.json().get("workflow_runs", []) if r.ok else []
    if not runs:
        return {"status": "queued", "conclusion": None}
    return {"status": runs[0]["status"], "conclusion": runs[0]["conclusion"]}