from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import project_store, project_builder, process_manager

router = APIRouter()


class FileItem(BaseModel):
    path: str
    content: str

class StoreProjectRequest(BaseModel):
    files: list[FileItem]
    project_name: str
    tech_stack: str
    database_url: str | None = None


@router.post("/store-project")
async def store_project(request: StoreProjectRequest):
    project_id = project_store.save_project(request.dict())
    return {"project_id": project_id}


@router.post("/start-preview/{project_id}")
async def start_preview(project_id: str):
    project = project_store.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found or expired. Please send it again from ProtoCode."
        )

    # If this project is already starting or running, don't rebuild its
    # files. Rebuilding would wipe out fixes and the venv mid-install.
    status = process_manager.get_status(project_id)
    if status and any(
        status[side]["status"] in ("pending", "installing", "starting", "running")
        for side in ("frontend", "backend")
    ):
        return status

    database_url = project.get("database_url")

    project_dir = project_builder.build_project_dir(
        project_id,
        project["files"]
    )

    return process_manager.start_preview(
        project_id,
        project_dir,
        project["tech_stack"],
        database_url,
    )


@router.get("/preview-status/{project_id}")
async def preview_status(project_id: str):
    status = process_manager.get_status(project_id)
    if not status:
        return {"status": "not_started"}
    return status


@router.post("/stop-preview/{project_id}")
async def stop_preview_endpoint(project_id: str):
    process_manager.stop_preview(project_id)
    return {"status": "stopped"}
