"""Signup with 6-digit email codes, login, logout."""
from datetime import datetime, timedelta, timezone

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.deps import get_current_user
from app.models.user import EmailToken, User
from app.services.email_service import send_verification_code
from app.services.security import (
    burn_password_check,
    codes_match,
    create_access_token,
    hash_code,
    hash_password,
    new_verification_code,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

VERIFY_PURPOSE = "verify_email"
RESEND_COOLDOWN_SECONDS = 60

SIGNUP_MESSAGE = "We've sent a 6-digit code to your email."
RESEND_MESSAGE = "If this account still needs verifying, a new code has been sent."
INVALID_CODE = "This code is invalid or has expired. Request a new one."
TOO_MANY_ATTEMPTS = "Too many incorrect attempts. Request a new code."


# ---------- request / response shapes ----------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class EmailRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=1, max_length=20)


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


def _check_email_domain(email: str) -> None:
    """Reject addresses whose domain has no mail server (fake domains, typos like gmial.con)."""
    try:
        validate_email(email, check_deliverability=True)
    except EmailNotValidError:
        raise HTTPException(
            status_code=400,
            detail="This email address can't receive mail. Please check it for typos.",
        )


def _delete_stale_unverified(db: Session) -> None:
    """Remove signups that were never verified, so dummy accounts don't pile up."""
    cutoff = _now() - timedelta(hours=settings.unverified_account_hours)
    db.query(User).filter(User.is_verified.is_(False), User.created_at < cutoff).delete(
        synchronize_session=False
    )
    db.commit()


def _issue_code(db: Session, user: User, background_tasks: BackgroundTasks) -> None:
    """Create a fresh 6-digit code and email it (at most once a minute)."""
    latest = (
        db.query(EmailToken)
        .filter(EmailToken.user_id == user.id, EmailToken.purpose == VERIFY_PURPOSE)
        .order_by(EmailToken.created_at.desc())
        .first()
    )
    if latest and latest.created_at and (_now() - latest.created_at).total_seconds() < RESEND_COOLDOWN_SECONDS:
        return

    # Only the newest code works
    db.query(EmailToken).filter(
        EmailToken.user_id == user.id,
        EmailToken.purpose == VERIFY_PURPOSE,
    ).delete(synchronize_session=False)

    code = new_verification_code()
    db.add(EmailToken(
        user_id=user.id,
        token_hash=hash_code(user.id, code),
        purpose=VERIFY_PURPOSE,
        attempts=0,
        expires_at=_now() + timedelta(minutes=settings.verify_code_minutes),
    ))
    db.commit()
    background_tasks.add_task(send_verification_code, user.email, code)


# ---------- endpoints ----------

@router.post("/signup", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
def signup(body: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = _normalise(body.email)
    _check_email_domain(email)
    _delete_stale_unverified(db)

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
        _issue_code(db, user, background_tasks)
    elif not user.is_verified:
        # Not verified yet: whoever proves they own the inbox sets the password.
        # (Stops someone "reserving" another person's email with their own password.)
        user.password_hash = hash_password(body.password)
        db.commit()
        _issue_code(db, user, background_tasks)
    else:
        burn_password_check(body.password)   # already verified: same reply, same timing

    return MessageOut(message=SIGNUP_MESSAGE)


@router.post("/verify-email", response_model=UserOut)
def verify_email(body: VerifyCodeRequest, response: Response, db: Session = Depends(get_db)):
    code = body.code.strip().replace(" ", "")
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=400, detail="Enter the 6-digit code from the email.")

    user = db.query(User).filter(User.email == _normalise(body.email)).first()
    if user is None or user.is_verified:
        raise HTTPException(status_code=400, detail=INVALID_CODE)

    record = (
        db.query(EmailToken)
        .filter(
            EmailToken.user_id == user.id,
            EmailToken.purpose == VERIFY_PURPOSE,
            EmailToken.used_at.is_(None),
            EmailToken.expires_at > _now(),
        )
        .order_by(EmailToken.created_at.desc())
        .first()
    )
    if record is None:
        raise HTTPException(status_code=400, detail=INVALID_CODE)
    if record.attempts >= settings.verify_max_attempts:
        raise HTTPException(status_code=429, detail=TOO_MANY_ATTEMPTS)

    if not codes_match(user.id, code, record.token_hash):
        record.attempts += 1
        db.commit()
        left = settings.verify_max_attempts - record.attempts
        if left <= 0:
            raise HTTPException(status_code=429, detail=TOO_MANY_ATTEMPTS)
        raise HTTPException(
            status_code=400,
            detail=f"Incorrect code. {left} attempt{'s' if left != 1 else ''} left.",
        )

    record.used_at = _now()
    user.is_verified = True
    user.verified_at = _now()
    db.commit()

    _set_session_cookie(response, user)   # verified users are logged straight in
    return _user_out(user)


@router.post("/resend-verification", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
def resend_verification(body: EmailRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == _normalise(body.email)).first()
    if user is not None and not user.is_verified:
        _issue_code(db, user, background_tasks)
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