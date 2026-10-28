from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.proto_idea import proto_idea_agent
from app.db.database import get_db
from app.deps import get_current_user
from app.models.idea_record import IdeaRecord
from app.models.schemas import IdeaListResponse, IdeaModel, IdeaRequest, IdeaResponse
from app.models.user import User
from app.services.scorer import score_and_rank


class RefineIdeaRequest(BaseModel):
    title: str
    current_description: str
    current_features: List[str]
    current_tech_hints: List[str]
    current_target_users: str
    feedback: str


router = APIRouter(prefix="/ideas", tags=["ProtoIdea"])


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=404, detail="Idea record not found")


def _get_own_record(record_id: str, db: Session, user: User) -> IdeaRecord:
    """Only ever returns a record that belongs to the logged-in user.
    Someone else's id gets the same 404 as one that doesn't exist."""
    record = (
        db.query(IdeaRecord)
        .filter(IdeaRecord.id == _parse_uuid(record_id), IdeaRecord.user_id == user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Idea record not found")
    return record


@router.post("/generate", response_model=IdeaResponse, summary="Generate app ideas")
async def generate_ideas(
    request: IdeaRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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

    ranked_ideas = score_and_rank(raw_ideas)

    try:
        record = IdeaRecord(
            id=uuid.uuid4(),
            user_id=user.id,
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
        ideas=ranked_ideas,
    )


@router.post("", response_model=IdeaResponse, summary="Generate app ideas (alias)")
async def generate_ideas_alias(
    request: IdeaRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await generate_ideas(request, db, user)


@router.post("/refine", response_model=IdeaModel, summary="Refine an idea based on user feedback")
async def refine_idea(
    request: RefineIdeaRequest,
    user: User = Depends(get_current_user),
):
    try:
        return await proto_idea_agent.refine(
            title=request.title,
            description=request.current_description,
            features=request.current_features,
            tech_hints=request.current_tech_hints,
            target_users=request.current_target_users,
            feedback=request.feedback,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {e}")


@router.get("/history", response_model=IdeaListResponse, summary="Your past generations")
def get_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        records = (
            db.query(IdeaRecord)
            .filter(IdeaRecord.user_id == user.id)
            .order_by(IdeaRecord.created_at.desc())
            .all()
        )
        return IdeaListResponse(records=[
            IdeaResponse(
                session_id=r.session_id,
                record_id=str(r.id),
                domain=r.domain,
                app_type=r.app_type,
                ideas=r.ideas,
            )
            for r in records
        ])
    except Exception:
        return IdeaListResponse(records=[])


@router.get("/{record_id}", response_model=IdeaResponse, summary="One of your records")
def get_idea(
    record_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = _get_own_record(record_id, db, user)
    return IdeaResponse(
        session_id=record.session_id,
        record_id=str(record.id),
        domain=record.domain,
        app_type=record.app_type,
        ideas=record.ideas,
    )


@router.delete("/{record_id}", summary="Delete one of your records")
def delete_idea(
    record_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = _get_own_record(record_id, db, user)
    db.delete(record)
    db.commit()
    return {"message": "Deleted successfully", "record_id": record_id}