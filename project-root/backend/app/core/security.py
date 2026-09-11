"""
Password hashing + JWT issuance/verification.

- Passwords: bcrypt via the `bcrypt` package directly (no passlib — one
  less dependency, and passlib's bcrypt backend has had version-compat
  issues with recent bcrypt releases).
- Tokens: PyJWT, HS256, signed with settings.jwt_secret_key (from env —
  never hardcoded, never committed). The secret is only ever read from
  Settings; it is never included in any response body or log line.
"""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings

settings = get_settings()

TOKEN_TYPE = "access"


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed/legacy hash (or None) — never let a hash-format quirk
        # raise past the auth boundary; just treat it as a failed login.
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY is not set. Set it in the environment before issuing tokens."
        )
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class InvalidTokenError(Exception):
    pass


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise InvalidTokenError("Server auth is not configured.")
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise InvalidTokenError("Invalid or expired token.")
    if payload.get("type") != TOKEN_TYPE:
        raise InvalidTokenError("Invalid token type.")
    return payload
