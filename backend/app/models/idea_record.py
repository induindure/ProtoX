import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class IdeaRecord(Base):
    __tablename__ = "ideas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False)
    app_type = Column(String, nullable=False)
    constraints = Column(Text, nullable=True)

    # Stores list of IdeaModel dicts as JSON
    ideas = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IdeaRecord id={self.id} domain={self.domain}>"
