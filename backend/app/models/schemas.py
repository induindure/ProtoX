from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class IdeaRequest(BaseModel):
    domain: str = Field(..., example="healthcare")
    app_type: str = Field(..., example="web app")
    constraints: Optional[str] = Field(None)
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class IdeaScores(BaseModel):
    feasibility: int   # 0-100
    novelty: int
    market_fit: int
    total: int


class IdeaModel(BaseModel):
    title: str
    description: str
    features: List[str]
    tech_hints: List[str]
    target_users: str


class RankedIdea(BaseModel):
    idea: IdeaModel
    scores: IdeaScores   # ✅ your scoring engine output


class IdeaResponse(BaseModel):
    session_id: str
    record_id: str
    domain: str
    app_type: str
    ideas: List[RankedIdea]   # ✅ now ranked with scores


class IdeaListResponse(BaseModel):
    records: List[IdeaResponse]