"""Salary changes through the API. Today is 2026-06-15."""

from datetime import date

from sqlalchemy import select

from app.compensation.models import SalaryChange
from tests.factories import make_employee


def change(**over) -> dict:
    return {"new_salary": "99000", "effective_on": "2026-06-01", "reason": "Promotion", **over}


def test_change_moves_current_salary_and_keeps_the_old_one(as_admin, db):
    emp = make_employee(db, salary_minor=9_000_000)

    r = as_admin.post(f"/api/employees/{emp.id}/salary-changes", json=change())

    assert r.status_code == 201
    body = r.json()
    assert body["salary_minor"] == 9_900_000
    latest, first = body["history"]
    assert latest["old_salary_minor"] == 9_000_000
    assert latest["new_salary_minor"] == 9_900_000
    assert latest["reason"] == "Promotion"
    assert latest["changed_by"] == "Ada Admin"
    assert first["reason"] == "Starting salary"


def test_history_is_append_only(as_admin, db):
    emp = make_employee(db, salary_minor=9_000_000)
    as_admin.post(f"/api/employees/{emp.id}/salary-changes", json=change(effective_on="2026-03-01"))
    as_admin.post(f"/api/employees/{emp.id}/salary-changes",
                  json=change(new_salary="105000", effective_on="2026-06-01"))  # fmt: skip

    rows = db.scalars(
        select(SalaryChange).where(SalaryChange.employee_id == emp.id).order_by(SalaryChange.id)
    ).all()
    assert [(r.old_salary_minor, r.new_salary_minor) for r in rows] == [
        (None, 9_000_000),
        (9_000_000, 9_900_000),
        (9_900_000, 10_500_000),
    ]


def test_problems_come_back_per_field(as_admin, db):
    emp = make_employee(db, salary_minor=9_000_000)
    r = as_admin.post(
        f"/api/employees/{emp.id}/salary-changes",
        json=change(new_salary="90000", effective_on="2026-07-01", reason="Whim"),
    )
    assert r.status_code == 422
    assert r.json()["fields"] == {
        "new_salary": "is the same as the current salary",
        "effective_on": "cannot be in the future",
        "reason": "choose one of the listed reasons",
    }


def test_rejected_change_leaves_nothing_behind(as_admin, db):
    emp = make_employee(db, salary_minor=9_000_000)
    as_admin.post(f"/api/employees/{emp.id}/salary-changes", json=change(effective_on="2020-01-01"))
    db.expire_all()
    assert emp.salary_minor == 9_000_000
    assert (
        len(db.scalars(select(SalaryChange).where(SalaryChange.employee_id == emp.id)).all()) == 1
    )


def test_bad_amount_is_a_field_error(as_admin, db):
    emp = make_employee(db, country="JP", salary_minor=9_000_000)
    r = as_admin.post(f"/api/employees/{emp.id}/salary-changes", json=change(new_salary="1.5"))
    assert r.json()["fields"] == {"new_salary": "JPY has no decimal places"}


def test_change_for_someone_who_left_must_predate_leaving(as_admin, db):
    emp = make_employee(db, end=date(2026, 4, 30))
    r = as_admin.post(f"/api/employees/{emp.id}/salary-changes", json=change())
    assert r.json()["fields"] == {"effective_on": "is after they left (2026-04-30)"}


def test_unknown_employee(as_admin):
    r = as_admin.post("/api/employees/999999/salary-changes", json=change())
    assert r.status_code == 404
