"""Password hashing (Argon2id) and the signed session token kept in the cookie."""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.errors import Unauthenticated

COOKIE_NAME = "acme_session"
_ALGORITHM = "HS256"
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def password_matches(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def issue_token(user_id: int, role: str, secret: str, hours: int) -> str:
    now = datetime.now(UTC)
    claims = {"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(hours=hours)}
    return jwt.encode(claims, secret, algorithm=_ALGORITHM)


def read_token(token: str, secret: str) -> int:
    """User id from a valid token; Unauthenticated for anything else."""
    try:
        claims = jwt.decode(token, secret, algorithms=[_ALGORITHM])
        return int(claims["sub"])
    except jwt.ExpiredSignatureError:
        raise Unauthenticated("Your session has expired. Please sign in again.") from None
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise Unauthenticated("Please sign in.") from None
