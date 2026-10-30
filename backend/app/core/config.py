from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET = "dev-only-secret-change-me"


class Settings(BaseSettings):
    """All configuration comes from PAYROLL_* environment variables (or backend/.env)."""

    model_config = SettingsConfigDict(env_prefix="PAYROLL_", env_file=".env", extra="ignore")

    env: Literal["dev", "prod"] = "dev"
    database_url: str = "postgresql+psycopg://payroll:payroll@localhost:55433/payroll"
    secret_key: str = DEV_SECRET
    session_hours: int = 8
    # Cookies are Secure in production (HTTPS). Local http://localhost needs False.
    cookie_secure: bool = False

    @field_validator("database_url")
    @classmethod
    def _psycopg_driver(cls, url: str) -> str:
        # Hosts such as Neon hand out postgres:// or postgresql:// URLs.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    @model_validator(mode="after")
    def _prod_safety(self) -> "Settings":
        if self.env == "prod":
            if self.secret_key == DEV_SECRET or len(self.secret_key) < 32:
                raise ValueError("PAYROLL_SECRET_KEY must be set to 32+ characters in prod")
            self.cookie_secure = True  # production is HTTPS only
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
