"""Signup, email verification, login, logout."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.deps import get_current_user
from app.models.user import EmailToken, User
from app.services.email_service import send_verification_email
from app.services.security import (
    burn_password_check,
    create_access_token,
    hash_password,
    hash_token,
    new_email_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

VERIFY_PURPOSE = "verify_email"
RESEND_COOLDOWN_SECONDS = 60

# Same reply whether or not the email already has an account,
# so nobody can use signup to find out who uses ProtoX.
SIGNUP_MESSAGE = "Check your inbox — we've sent a link to verify your email."
RESEND_MESSAGE = "If an unverified account exists for this email, a new verification link has been sent."


# ---------- request / response shapes ----------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class EmailRequest(BaseModel):
    email: EmailStr


class TokenRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class UserOut(BaseModel):
    id: str
    email: str


class MessageOut(BaseModel):
    message: str


# ---------- helpers ----------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalise(email: str) -> str:
    return email.strip().lower()


def _user_out(user: User) -> UserOut:
    return UserOut(id=str(user.id), email=user.email)


def _set_session_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=create_access_token(user.id),
        httponly=True,                 # JavaScript can't read it
        secure=settings.cookie_secure,  # true in production (HTTPS)
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def _issue_verification(db: Session, user: User, background_tasks: BackgroundTasks) -> None:
    """Create a fresh verification token and email it (at most once a minute)."""
    latest = (
        db.query(EmailToken)
        .filter(EmailToken.user_id == user.id, EmailToken.purpose == VERIFY_PURPOSE)
        .order_by(EmailToken.created_at.desc())
        .first()
    )
    if latest and latest.created_at and (_now() - latest.created_at).total_seconds() < RESEND_COOLDOWN_SECONDS:
        return

    # Old unused links stop working once a new one is sent
    db.query(EmailToken).filter(
        EmailToken.user_id == user.id,
        EmailToken.purpose == VERIFY_PURPOSE,
        EmailToken.used_at.is_(None),
    ).delete(synchronize_session=False)

    raw_token, token_hash = new_email_token()
    db.add(EmailToken(
        user_id=user.id,
        token_hash=token_hash,
        purpose=VERIFY_PURPOSE,
        expires_at=_now() + timedelta(hours=settings.verify_token_hours),
    ))
    db.commit()
    background_tasks.add_task(send_verification_email, user.email, raw_token)


# ---------- endpoints ----------

@router.post("/signup", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
def signup(body: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = _normalise(body.email)
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        user = User(email=email, password_hash=hash_password(body.password))
        db.add(user)
        try:
            db.commit()
        except IntegrityError:          # same email signed up twice at the same moment
            db.rollback()
            return MessageOut(message=SIGNUP_MESSAGE)
        db.refresh(user)
        _issue_verification(db, user, background_tasks)
    else:
        burn_password_check(body.password)   # keep timing the same as a new signup
        if not user.is_verified:
            _issue_verification(db, user, background_tasks)

    return MessageOut(message=SIGNUP_MESSAGE)


@router.post("/verify-email", response_model=UserOut)
def verify_email(body: TokenRequest, response: Response, db: Session = Depends(get_db)):
    record = (
        db.query(EmailToken)
        .filter(
            EmailToken.token_hash == hash_token(body.token),
            EmailToken.purpose == VERIFY_PURPOSE,
            EmailToken.used_at.is_(None),
            EmailToken.expires_at > _now(),
        )
        .first()
    )
    if record is None:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired.")

    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired.")

    record.used_at = _now()
    if not user.is_verified:
        user.is_verified = True
        user.verified_at = _now()
    db.commit()

    _set_session_cookie(response, user)   # verified users are logged straight in
    return _user_out(user)


@router.post("/resend-verification", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
def resend_verification(body: EmailRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == _normalise(body.email)).first()
    if user is not None and not user.is_verified:
        _issue_verification(db, user, background_tasks)
    return MessageOut(message=RESEND_MESSAGE)


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == _normalise(body.email)).first()

    if user is None:
        burn_password_check(body.password)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    _set_session_cookie(response, user)
    return _user_out(user)


@router.post("/logout", response_model=MessageOut)
def logout(response: Response):
    response.delete_cookie(
        settings.auth_cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return MessageOut(message="Logged out.")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)