"""FastAPI dependencies: who is calling, and are they allowed to change data."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.models import ADMIN, User
from app.auth.security import COOKIE_NAME, read_token
from app.core.db import get_db
from app.core.errors import Forbidden, Unauthenticated

DB = Annotated[Session, Depends(get_db)]


def current_user(request: Request, db: DB) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise Unauthenticated("Please sign in.")
    user = db.get(User, read_token(token, request.app.state.settings.secret_key))
    if user is None:
        raise Unauthenticated("Please sign in.")
    return user


def admin_user(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != ADMIN:
        raise Forbidden("Only HR admins can make changes.")
    return user


AnyUser = Annotated[User, Depends(current_user)]
Admin = Annotated[User, Depends(admin_user)]
