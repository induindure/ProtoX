from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.idea_record import IdeaRecord
from app.models.schemas import IdeaRequest, IdeaResponse, IdeaListResponse

router = APIRouter(prefix="/ideas", tags=["ProtoIdea"])

# ✅ Fixed: matches IdeaModel schema exactly (tech_hints + target_users, not tech_stack)
DUMMY_IDEAS = [
    {
        "title": "MediTrack",
        "description": "A personal health record app for patients to track medications and appointments.",
        "features": ["Medication reminders", "Appointment scheduler", "Health history log"],
        "tech_hints": ["React", "FastAPI", "PostgreSQL"],
        "target_users": "Patients managing chronic conditions",
    },
    {
        "title": "CareConnect",
        "description": "Connects patients with local healthcare providers for quick consultations.",
        "features": ["Provider search", "Video consultations", "Prescription requests"],
        "tech_hints": ["Next.js", "Django", "WebRTC"],
        "target_users": "People needing quick medical advice",
    },
]


@router.post("/generate", response_model=IdeaResponse, summary="Generate app ideas")
async def generate_ideas(request: IdeaRequest):
    # ✅ No DB dependency — won't hang even if DB is down
    # TODO: swap DUMMY_IDEAS with real agent call once DB is stable:
    # ideas = await proto_idea_agent.generate(request.domain, request.app_type, request.constraints)

    session_id = request.session_id or str(uuid.uuid4())

    return IdeaResponse(
        session_id=session_id,
        record_id="dummy-id",
        domain=request.domain,
        app_type=request.app_type,
        ideas=DUMMY_IDEAS,
    )


@router.post("", response_model=IdeaResponse, summary="Generate app ideas (alias)")
async def generate_ideas_alias(request: IdeaRequest):
    return await generate_ideas(request)


@router.get("/history", response_model=IdeaListResponse, summary="Get all past idea generations")
def get_history(db: Session = Depends(get_db)):
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