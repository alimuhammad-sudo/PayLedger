from collections.abc import Callable
from datetime import date

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from app.analytics.router import router as analytics_router
from app.auth.router import router as auth_router
from app.core.config import Settings, get_settings
from app.core.db import make_engine, session_factory
from app.core.errors import install_error_handler
from app.employees.router import router as employees_router
from app.payroll.router import router as payroll_router


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
    clock: Callable[[], date] = date.today,
) -> FastAPI:
    """Build the app. Tests pass their own engine and a fixed clock."""
    settings = settings or get_settings()
    engine = engine or make_engine(settings.database_url)

    app = FastAPI(title="PayLedger API", version="0.1.0", docs_url="/api/docs",
                  openapi_url="/api/openapi.json")  # fmt: skip
    app.state.settings = settings
    app.state.session_factory = session_factory(engine)
    app.state.clock = clock
    install_error_handler(app)
    app.include_router(auth_router)
    app.include_router(employees_router)
    app.include_router(analytics_router)
    app.include_router(payroll_router)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
