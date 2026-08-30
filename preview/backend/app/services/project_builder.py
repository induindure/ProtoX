"""
Reconstructs a ProtoCode-generated project onto disk so real dev servers
(vite/next/uvicorn/node/django) can run against it.

Different from ProtoTest's project_builder.py in one way: ProtoTest uses a
tempfile that the caller rmtree's right after the test run finishes. Preview
processes stay alive for a while (the user is looking at the iframe), so we
need a stable, predictable directory per project_id instead — one that
survives across the multiple requests (start / status / stop) for the same
preview session.

WORKSPACE_ROOT lives in the system temp directory, NOT inside this backend's
own folder — uvicorn's --reload file watcher recursively watches the whole
working directory, and writing hundreds of project/venv files into a folder
inside the backend triggers constant false-positive reloads, killing every
running preview session mid-flight. System temp is outside that watch scope.
"""

import tempfile
from pathlib import Path
from typing import List

WORKSPACE_ROOT = Path(tempfile.gettempdir()) / "protox_preview_workspaces"
WORKSPACE_ROOT.mkdir(exist_ok=True)


def get_project_dir(project_id: str) -> Path:
    return WORKSPACE_ROOT / project_id


def build_project_dir(project_id: str, files: List[dict]) -> Path:
    """
    files: list of {"path": ..., "content": ...} dicts (same shape ProtoCode emits).
    Idempotent — if called again for the same project_id, files are rewritten
    in place (handles the case where the user tweaks something and re-sends).
    """
    root = get_project_dir(project_id)
    root.mkdir(parents=True, exist_ok=True)

    for file in files:
        rel_path = file["path"]
        content = file["content"]

        target = (root / rel_path).resolve()
        if not str(target).startswith(str(root.resolve())):
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return root


def cleanup_project_dir(project_id: str):
    import shutil
    root = get_project_dir(project_id)
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)