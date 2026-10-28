"""Password hashing, login tokens and one-time email tokens."""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher()   # Argon2id with safe default parameters

# Used so a login for an email that doesn't exist takes as long as a wrong
# password - otherwise attackers could tell which emails have accounts.
_DUMMY_HASH = _hasher.hash("protox-timing-equaliser")


# ---------- passwords ----------

def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def burn_password_check(password: str) -> None:
    """Spend the same time as a real check when the user does not exist."""
    verify_password(password, _DUMMY_HASH)


# ---------- login tokens (stored in an httpOnly cookie) ----------

def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID | None:
    """Return the user id if the token is valid and not expired, else None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


# ---------- one-time email tokens ----------

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def new_email_token() -> tuple[str, str]:
    """Return (raw_token_for_the_email_link, hash_to_store_in_the_database)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)