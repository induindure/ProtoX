from pydantic import BaseModel
from typing import List

class IdeaRequest(BaseModel):
    domain: str = "healthcare"
    app_type: str = "web"

class IdeaModel(BaseModel):
    title: str
    description: str
    features: List[str]

class IdeaResponse(BaseModel):
    ideas: List[IdeaModel]