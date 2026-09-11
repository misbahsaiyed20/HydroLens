"""
User signup/login. Kept separate from app/core/security.py: that module is
pure crypto (hashing, JWT), this module is the DB-touching business logic
(uniqueness checks, role assignment) — same separation pattern as the rest
of app/services/.
"""
import logging

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import SignupRequest

logger = logging.getLogger("aqua_sentinel")


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_citizen(db: Session, payload: SignupRequest) -> User:
    """
    Public signup path. Always creates role=CITIZEN — there is no code path
    from this function to REVIEWER; see scripts/create_reviewer.py for the
    only way a reviewer account is created.
    """
    if get_user_by_email(db, payload.email):
        raise EmailAlreadyRegisteredError("An account with this email already exists.")

    user = User(
        email=payload.email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        role=UserRole.CITIZEN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user signed up: id=%s role=%s", user.id, user.role.value)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        # Same error for "no such user" and "wrong password" — never reveal
        # which one, or an attacker can enumerate registered emails.
        raise InvalidCredentialsError("Incorrect email or password.")
    return user
