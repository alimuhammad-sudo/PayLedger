from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select

from app.auth.deps import DB, AnyUser
from app.auth.models import User
from app.auth.security import COOKIE_NAME, hash_password, issue_token, password_matches
from app.core.errors import Unauthenticated

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Checked when the email is unknown, so a wrong email takes as long as a wrong password.
_DUMMY_HASH = hash_password("not-a-real-password")


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    @classmethod
    def of(cls, u: User) -> "UserOut":
        return cls(id=u.id, email=u.email, full_name=u.full_name, role=u.role)


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, request: Request, response: Response, db: DB) -> UserOut:
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.lower()))
    password_ok = password_matches(user.password_hash if user else _DUMMY_HASH, body.password)
    if user is None or not password_ok:
        raise Unauthenticated("Email or password is incorrect.")
    settings = request.app.state.settings
    response.set_cookie(
        COOKIE_NAME,
        issue_token(user.id, user.role, settings.secret_key, settings.session_hours),
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return UserOut.of(user)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=UserOut)
def me(user: AnyUser) -> UserOut:
    return UserOut.of(user)
