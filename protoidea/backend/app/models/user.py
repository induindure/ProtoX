import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)   # Argon2 hash, never the real password
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} verified={self.is_verified}>"


class EmailToken(Base):
    """One-time tokens for email verification (and password reset later).
    Only a SHA-256 hash of the token is stored."""

    __tablename__ = "email_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True)
    purpose = Column(String, nullable=False)          # "verify_email" (later: "reset_password")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)