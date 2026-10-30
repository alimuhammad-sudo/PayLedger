import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_dev_defaults_are_usable_locally():
    s = Settings(env="dev")
    assert s.cookie_secure is False


def test_prod_needs_a_real_secret():
    with pytest.raises(ValidationError, match="PAYROLL_SECRET_KEY"):
        Settings(env="prod")
    with pytest.raises(ValidationError):
        Settings(env="prod", secret_key="short")


def test_prod_cookies_are_always_secure():
    assert Settings(env="prod", secret_key="k" * 40, cookie_secure=False).cookie_secure is True


@pytest.mark.parametrize("url", ["postgres://u:p@h/db", "postgresql://u:p@h/db"])
def test_plain_postgres_urls_use_psycopg(url):
    assert Settings(database_url=url).database_url == "postgresql+psycopg://u:p@h/db"
