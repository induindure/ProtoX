from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


# ── Input ────────────────────────────────────────────────────────────────────

class IdeaRequest(BaseModel):
    domain: str = Field(..., example="healthcare", description="Domain the app should be in")
    app_type: str = Field(..., example="web app", description="Type of application")
    constraints: Optional[str] = Field(None, example="must be free to use, simple UI")
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


# ── Output ───────────────────────────────────────────────────────────────────

class IdeaModel(BaseModel):
    title: str
    description: str
    features: List[str]
    tech_hints: List[str]
    target_users: str


class IdeaResponse(BaseModel):
    session_id: str
    record_id: str
    domain: str
    app_type: str
    ideas: List[IdeaModel]


class IdeaListResponse(BaseModel):
    records: List[IdeaResponse]
