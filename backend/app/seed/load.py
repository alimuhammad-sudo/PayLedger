"""Write the generated organisation into PostgreSQL.

Employees and salary history go in with COPY, which streams every row in one round trip
per table instead of thousands of INSERTs. That matters most for a hosted database,
where each round trip crosses the internet.
"""

import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.auth.models import ADMIN, VIEWER, User
from app.auth.security import hash_password
from app.core.fx import Currency, FxRate
from app.core.money import MINOR_DIGITS
from app.employees.models import Employee
from app.employees.service import staff_id_for
from app.seed.generator import ANCHOR, RATES_FROM, SEED, USD_PER_UNIT, generate

DEMO_ADMIN = "hr.admin@acme-hr.example"
DEMO_VIEWER = "hr.viewer@acme-hr.example"
DEFAULT_PASSWORD = "acme-payroll-demo"


@dataclass(frozen=True)
class Loaded:
    employees: int
    salary_changes: int


class AlreadySeeded(RuntimeError):
    pass


def reset(db: Session) -> None:
    db.execute(text(
        "TRUNCATE payslips, payroll_runs, salary_changes, employees, users, fx_rates, "
        "currencies RESTART IDENTITY CASCADE"
    ))  # fmt: skip


def seed(
    db: Session, *, count: int = 10_000, seed: int = SEED, anchor: date = ANCHOR,
    password: str | None = None,
) -> Loaded:  # fmt: skip
    if db.scalar(select(func.count(Employee.id))):
        raise AlreadySeeded("The database already has employees; use --reset to replace them.")

    db.add_all(Currency(code=c, minor_digits=d) for c, d in MINOR_DIGITS.items())
    db.flush()
    db.add_all(FxRate(currency=c, usd_per_unit=Decimal(r), valid_from=RATES_FROM)
               for c, r in USD_PER_UNIT.items())  # fmt: skip
    pw = hash_password(password or os.environ.get("PAYROLL_DEMO_PASSWORD", DEFAULT_PASSWORD))
    admin = User(email=DEMO_ADMIN, full_name="Hira Admin", password_hash=pw, role=ADMIN)
    db.add_all([admin, User(email=DEMO_VIEWER, full_name="Vikram Viewer", password_hash=pw,
                            role=VIEWER)])  # fmt: skip
    db.flush()

    people = generate(count, seed, anchor)
    # Reserve ids from the sequence so COPY can write them and the sequence stays correct
    # for employees added later through the app.
    ids = db.scalars(
        text("SELECT nextval('employees_id_seq') FROM generate_series(1, :n)"), {"n": len(people)}
    ).all()

    raw = db.connection().connection.dbapi_connection
    changes = 0
    with raw.cursor() as cur:
        with cur.copy(
            "COPY employees (id, staff_id, full_name, email, job_title, department, level, "
            "country, currency, start_date, end_date, salary_minor) FROM STDIN"
        ) as copy:
            for emp_id, p in zip(ids, people, strict=True):
                copy.write_row((emp_id, staff_id_for(emp_id), p.full_name, p.email, p.job_title,
                                p.department, p.level, p.country, p.currency, p.start_date,
                                p.end_date, p.salary_minor))  # fmt: skip
        with cur.copy(
            "COPY salary_changes (employee_id, old_salary_minor, new_salary_minor, "
            "effective_on, reason, changed_by) FROM STDIN"
        ) as copy:
            for emp_id, p in zip(ids, people, strict=True):
                for c in p.history:
                    copy.write_row((emp_id, c.old_minor, c.new_minor, c.effective_on, c.reason,
                                    None))  # fmt: skip
                    changes += 1
    db.commit()
    return Loaded(employees=len(people), salary_changes=changes)
