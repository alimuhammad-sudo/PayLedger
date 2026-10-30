"""Expected errors raised by services, turned into HTTP responses in one place.

Body shape: {"message": "...", "fields": {"field_name": "what is wrong"}}
`fields` only appears when specific inputs are wrong, so forms can show each message
next to its input.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status = 400

    def __init__(self, message: str, fields: dict[str, str] | None = None):
        super().__init__(message)
        self.message = message
        self.fields = fields or {}


class Invalid(AppError):
    status = 422

    @classmethod
    def field(cls, name: str, problem: str) -> "Invalid":
        return cls("Please fix the highlighted fields", {name: problem})


class NotFound(AppError):
    status = 404


class Conflict(AppError):
    status = 409


class Unauthenticated(AppError):
    status = 401


class Forbidden(AppError):
    status = 403


def install_error_handler(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    def _handle(_: Request, exc: AppError) -> JSONResponse:
        body: dict = {"message": exc.message}
        if exc.fields:
            body["fields"] = exc.fields
        return JSONResponse(status_code=exc.status, content=body)
