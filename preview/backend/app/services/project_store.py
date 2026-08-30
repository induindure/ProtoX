"""
Temporary in-memory store for projects handed off from ProtoCode.
Identical pattern to ProtoTest's project_store.py — same TTL approach,
kept as a separate copy (not a shared import) so each module stays
independently deployable, matching how ProtoCode/ProtoTest are split.
"""

import uuid
import time

_store = {}
TTL_SECONDS = 60 * 30  # 30 minutes


def save_project(project: dict) -> str:
    project_id = str(uuid.uuid4())
    _store[project_id] = {"data": project, "created_at": time.time()}
    _cleanup_expired()
    return project_id


def get_project(project_id: str) -> dict | None:
    entry = _store.get(project_id)
    if not entry:
        return None
    if time.time() - entry["created_at"] > TTL_SECONDS:
        del _store[project_id]
        return None
    return entry["data"]


def _cleanup_expired():
    now = time.time()
    expired = [k for k, v in _store.items() if now - v["created_at"] > TTL_SECONDS]
    for k in expired:
        del _store[k]
