import io
import re
import secrets
import time
import zipfile
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(prefix="/api/protodeploy")

_STORE: dict = {}
TTL_SECONDS = 3600


class FileInput(BaseModel):
    path: str
    content: str


class StoreRequest(BaseModel):
    files: List[FileInput]
    project_name: str
    tech_stack: str = ""


def _purge() -> None:
    now = time.time()
    for k in [k for k, v in _STORE.items() if now - v["ts"] > TTL_SECONDS]:
        _STORE.pop(k, None)


@router.post("/store-project")
def store_project(req: StoreRequest):
    _purge()
    for f in req.files:
        p = f.path.replace("\\", "/")
        if p.startswith("/") or ".." in p.split("/"):
            raise HTTPException(400, f"Unsafe file path: {f.path}")
    pid = secrets.token_hex(8)
    _STORE[pid] = {"req": req, "ts": time.time()}
    return {"project_id": pid}


@router.get("/project-zip/{project_id}")
def project_zip(project_id: str):
    _purge()
    item = _STORE.get(project_id)
    if not item:
        raise HTTPException(404, "Project not found or expired")
    req = item["req"]
    folder = re.sub(r"[^a-zA-Z0-9._-]", "-", req.project_name) or "protox-app"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in req.files:
            z.writestr(f"{folder}/{f.path.replace(chr(92), '/')}", f.content)
    return Response(buf.getvalue(), media_type="application/zip")
