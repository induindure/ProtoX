"""Shared FastAPI dependencies."""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.user import User
from app.services.security import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Return the logged-in, verified user, or reject the request with 401."""
    token = request.cookies.get(settings.auth_cookie_name)
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    user = db.get(User, user_id)
    if user is None or not user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    return user