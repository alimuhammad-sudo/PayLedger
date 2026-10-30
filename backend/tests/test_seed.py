from collections import Counter
from datetime import date

import pytest
from sqlalchemy import delete, func, select

from app.auth.models import User
from app.compensation.models import SalaryChange
from app.compensation.rules import EmployeeState, ProposedChange, check_change
from app.core.fx import Currency, FxRate
from app.core.money import MINOR_DIGITS
from app.core.reference import COUNTRIES
from app.employees.models import Employee
from app.seed.generator import ANCHOR, generate, job_title
from app.seed.load import AlreadySeeded, seed

SAMPLE = 600


@pytest.fixture(scope="module")
def people():
    return generate(SAMPLE)


def test_same_seed_same_people(people):
    assert generate(SAMPLE) == people


def test_different_seed_different_people(people):
    assert generate(SAMPLE, seed=1) != people


def test_emails_unique_and_ascii(people):
    emails = [p.email for p in people]
    assert len(set(emails)) == SAMPLE
    assert all(e.isascii() for e in emails)


def test_every_country_appears_with_its_currency(people):
    assert set(Counter(p.country for p in people)) == set(COUNTRIES)
    assert all(p.currency == COUNTRIES[p.country].currency for p in people)


def test_history_is_valid_and_ends_at_current_salary(people):
    for p in people:
        h = p.history
        assert h[0].reason == "Starting salary" and h[0].effective_on == p.start_date
        assert h[-1].new_minor == p.salary_minor
        assert all(c.effective_on <= ANCHOR for c in h)
        for prev, nxt in zip(h, h[1:], strict=False):
            assert nxt.old_minor == prev.new_minor
            assert nxt.new_minor > prev.new_minor
            # each step would pass the same rules the API applies
            state = EmployeeState(prev.new_minor, p.start_date, p.end_date, prev.effective_on)
            change = ProposedChange(nxt.new_minor, nxt.effective_on, nxt.reason, None)
            assert check_change(change, state, ANCHOR) == {}


def test_leavers_leave_after_their_last_change(people):
    leavers = [p for p in people if p.end_date]
    assert 0.03 < len(leavers) / SAMPLE < 0.15
    assert all(p.history[-1].effective_on < p.end_date <= ANCHOR for p in leavers)


def test_yen_salaries_are_whole_ten_thousands(people):
    for p in people:
        if p.currency == "JPY":
            assert p.salary_minor % 10_000 == 0


def test_job_titles():
    assert job_title("Engineering", "Senior") == "Senior Engineer"
    assert job_title("Sales", "Director") == "Director of Sales"


def test_seed_loads_into_postgres(db):
    # Reference data from conftest is replaced for this test (rolled back afterwards).
    db.execute(delete(FxRate))
    db.execute(delete(Currency))
    loaded = seed(db, count=50, anchor=date(2026, 6, 15), password="pw")

    assert loaded.employees == 50
    assert db.scalar(select(func.count(Employee.id))) == 50
    assert db.scalar(select(func.count(SalaryChange.id))) == loaded.salary_changes
    assert db.scalar(select(func.count(Currency.code))) == len(MINOR_DIGITS)
    assert {u.role for u in db.scalars(select(User))} == {"admin", "viewer"}
    first = db.scalar(select(Employee).order_by(Employee.id))
    assert first.staff_id == f"ACM{first.id:05d}"


def test_seed_refuses_to_run_twice(db):
    db.execute(delete(FxRate))
    db.execute(delete(Currency))
    seed(db, count=5, anchor=date(2026, 6, 15), password="pw")
    with pytest.raises(AlreadySeeded):
        seed(db, count=5, anchor=date(2026, 6, 15), password="pw")
