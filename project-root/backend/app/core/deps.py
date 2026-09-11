"""
FastAPI dependencies for authentication/authorization. Kept in app/core
(alongside security.py) rather than app/services, since these are
request-lifecycle wiring, not business logic.
"""
import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, decode_access_token
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User

# auto_error=False so a missing header raises our own 401 with a clear
# message, rather than FastAPI's generic HTTPBearer response.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists.")
    return user


def require_reviewer(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.REVIEWER:
        raise HTTPException(status_code=403, detail="Reviewer role required.")
    return user
