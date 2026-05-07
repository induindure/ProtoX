from typing import List
import uuid
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.idea_record import IdeaRecord
from app.models.schemas import IdeaRequest, IdeaResponse, IdeaListResponse, IdeaModel
from app.agents.proto_idea import proto_idea_agent
from app.services.scorer import score_and_rank


class RefineIdeaRequest(BaseModel):
    title: str
    current_description: str
    current_features: List[str]
    current_tech_hints: List[str]
    current_target_users: str
    feedback: str


router = APIRouter(prefix="/ideas", tags=["ProtoIdea"])


@router.post("/generate", response_model=IdeaResponse, summary="Generate app ideas")
async def generate_ideas(request: IdeaRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())

    try:
        raw_ideas = await proto_idea_agent.generate(
            domain=request.domain,
            app_type=request.app_type,
            constraints=request.constraints or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse ideas: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Idea generation failed: {e}")

    # ✅ Your scoring engine ranks the ideas
    ranked_ideas = score_and_rank(raw_ideas)

    # Save raw ideas to DB (flat, without scores)
    try:
        record = IdeaRecord(
            id=uuid.uuid4(),
            session_id=session_id,
            domain=request.domain,
            app_type=request.app_type,
            constraints=request.constraints,
            ideas=[ri.idea.model_dump() for ri in ranked_ideas],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id = str(record.id)
    except Exception:
        db.rollback()
        record_id = "db-unavailable"

    return IdeaResponse(
        session_id=session_id,
        record_id=record_id,
        domain=request.domain,
        app_type=request.app_type,
        ideas=ranked_ideas,   # ✅ RankedIdea objects with scores
    )


@router.post("", response_model=IdeaResponse, summary="Generate app ideas (alias)")
async def generate_ideas_alias(request: IdeaRequest, db: Session = Depends(get_db)):
    return await generate_ideas(request, db)


@router.post("/refine", response_model=IdeaModel, summary="Refine an idea based on user feedback")
async def refine_idea(request: RefineIdeaRequest):
    """
    Refine a generated idea based on user feedback.
    Returns an updated IdeaModel with modified features, description, etc.
    """
    try:
        refined = await proto_idea_agent.refine(
            title=request.title,
            description=request.current_description,
            features=request.current_features,
            tech_hints=request.current_tech_hints,
            target_users=request.current_target_users,
            feedback=request.feedback,
        )
        return refined
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {e}")


@router.get("/history", response_model=IdeaListResponse, summary="Get all past idea generations")
def get_history(db: Session = Depends(get_db)):
    try:
        records = db.query(IdeaRecord).order_by(IdeaRecord.created_at.desc()).all()
        result = []
        for r in records:
            result.append(IdeaResponse(
                session_id=r.session_id,
                record_id=str(r.id),
                domain=r.domain,
                app_type=r.app_type,
                ideas=r.ideas,
            ))
        return IdeaListResponse(records=result)
    except Exception:
        return IdeaListResponse(records=[])


@router.get("/{record_id}", response_model=IdeaResponse, summary="Get a specific idea record")
def get_idea(record_id: str, db: Session = Depends(get_db)):
    record = db.query(IdeaRecord).filter(IdeaRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Idea record not found")
    return IdeaResponse(
        session_id=record.session_id,
        record_id=str(record.id),
        domain=record.domain,
        app_type=record.app_type,
        ideas=record.ideas,
    )


@router.delete("/{record_id}", summary="Delete an idea record")
def delete_idea(record_id: str, db: Session = Depends(get_db)):
    record = db.query(IdeaRecord).filter(IdeaRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Idea record not found")
    db.delete(record)
    db.commit()
    return {"message": "Deleted successfully", "record_id": record_id}