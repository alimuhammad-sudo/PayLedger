"""Tests run against a real PostgreSQL database (payroll_test), the same engine as
production, so percentile functions and constraints behave exactly as they will live.

- The schema and reference data (currencies, exchange rates) are created once per run.
- Every test runs inside a transaction that is rolled back afterwards. Code under test
  can still call commit(): it commits a savepoint inside that transaction.
- "Today" is fixed at 2026-06-15, so nothing depends on the real date.

Start the database with `docker compose up -d db` (or set PAYROLL_TEST_DATABASE_URL).
"""

import os
from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.auth.models import ADMIN, VIEWER, User
from app.auth.security import hash_password
from app.core.config import Settings
from app.core.db import Base, make_engine
from app.core.fx import Currency, FxRate
from app.core.money import MINOR_DIGITS
from app.main import create_app

TODAY = date(2026, 6, 15)
PASSWORD = "correct-horse-battery"
RATES = {
    "USD": "1", "GBP": "1.27", "EUR": "1.08", "INR": "0.012", "JPY": "0.0066",
    "CAD": "0.73", "BRL": "0.19", "MXN": "0.055",
}  # fmt: skip

TEST_DB = os.environ.get(
    "PAYROLL_TEST_DATABASE_URL", "postgresql+psycopg://payroll:payroll@localhost:55433/payroll_test"
)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    engine = make_engine(Settings(database_url=TEST_DB).database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all(Currency(code=c, minor_digits=d) for c, d in MINOR_DIGITS.items())
        s.flush()
        s.add_all(
            FxRate(currency=c, usd_per_unit=Decimal(r), valid_from=date(2026, 1, 1))
            for c, r in RATES.items()
        )
        s.commit()
    yield engine
    engine.dispose()


@pytest.fixture
def connection(engine: Engine) -> Iterator[Connection]:
    with engine.connect() as conn:
        outer = conn.begin()
        yield conn
        outer.rollback()


@pytest.fixture
def db(connection: Connection) -> Iterator[Session]:
    factory = sessionmaker(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    with factory() as session:
        yield session


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url=TEST_DB, secret_key="test-secret-" + "x" * 32)


@pytest.fixture
def client(settings: Settings, engine: Engine, connection: Connection) -> Iterator[TestClient]:
    app = create_app(settings=settings, engine=engine, clock=lambda: TODAY)
    # Requests share the test's transaction, so everything is rolled back afterwards.
    app.state.session_factory = sessionmaker(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    with TestClient(app) as c:
        yield c


_HASH = hash_password(PASSWORD)  # hashing is deliberately slow; do it once


def make_user(db: Session, email: str, role: str, name: str = "Test User") -> User:
    user = User(email=email, full_name=name, password_hash=_HASH, role=role)
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def admin(db: Session) -> User:
    return make_user(db, "admin@acme-hr.example", ADMIN, "Ada Admin")


@pytest.fixture
def viewer(db: Session) -> User:
    return make_user(db, "viewer@acme-hr.example", VIEWER, "Vic Viewer")


def login(client: TestClient, email: str) -> TestClient:
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return client


@pytest.fixture
def as_admin(client: TestClient, admin: User) -> TestClient:
    return login(client, admin.email)


@pytest.fixture
def as_viewer(client: TestClient, viewer: User) -> TestClient:
    return login(client, viewer.email)
