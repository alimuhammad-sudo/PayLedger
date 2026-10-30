"""Payroll runs. Today is 2026-06-15; GBP rate 1.27."""

from datetime import date

from sqlalchemy import select

from app.compensation.models import SalaryChange
from tests.factories import make_employee


def run(client, year=2026, month=5):
    return client.post("/api/payroll/runs", json={"year": year, "month": month})


def test_full_month_and_prorated_leaver_and_joiner(as_admin, db):
    make_employee(db, name="All Month", salary_minor=12_000_000)  # 10,000.00 a month
    make_employee(db, name="Joiner", salary_minor=12_000_000, start=date(2026, 5, 22))  # 10/31
    make_employee(db, name="Leaver", salary_minor=12_000_000, end=date(2026, 5, 15))  # 15/31
    make_employee(db, name="Brit", country="GB", salary_minor=6_000_000)  # 5,000.00 GBP
    make_employee(db, name="Gone", end=date(2026, 4, 30))
    make_employee(db, name="Later", start=date(2026, 6, 1))

    r = run(as_admin)

    assert r.status_code == 201
    body = r.json()
    assert body["headcount"] == 4
    slips = {s["full_name"]: s for s in
             as_admin.get(f"/api/payroll/runs/{body['id']}/payslips").json()["items"]}  # fmt: skip
    assert set(slips) == {"All Month", "Joiner", "Leaver", "Brit"}
    assert slips["All Month"]["gross_minor"] == 1_000_000
    assert (slips["Joiner"]["days_paid"], slips["Joiner"]["gross_minor"]) == (10, 322_581)
    assert (slips["Leaver"]["days_paid"], slips["Leaver"]["gross_minor"]) == (15, 483_871)
    assert slips["Brit"]["gross_minor"] == 500_000
    assert slips["Brit"]["gross_usd_cents"] == 635_000
    assert body["total_usd_cents"] == 1_000_000 + 322_581 + 483_871 + 635_000


def test_uses_salary_in_force_at_month_end(as_admin, db):
    emp = make_employee(db, salary_minor=12_000_000, start=date(2025, 1, 1))
    db.add(SalaryChange(employee_id=emp.id, old_salary_minor=12_000_000,
                        new_salary_minor=24_000_000, effective_on=date(2026, 6, 1),
                        reason="Promotion"))  # fmt: skip
    emp.salary_minor = 24_000_000
    db.commit()

    may = run(as_admin, month=5).json()
    june = run(as_admin, month=6).json()

    assert may["total_usd_cents"] == 1_000_000  # before the raise
    assert june["total_usd_cents"] == 2_000_000


def test_run_is_frozen(as_admin, db):
    emp = make_employee(db, salary_minor=12_000_000)
    created = run(as_admin).json()
    as_admin.post(f"/api/employees/{emp.id}/salary-changes",
                  json={"new_salary": "500000", "effective_on": "2026-06-01",
                        "reason": "Promotion"})  # fmt: skip
    again = as_admin.get(f"/api/payroll/runs/{created['id']}").json()
    assert again["total_usd_cents"] == 1_000_000


def test_country_totals(as_admin, db):
    make_employee(db, country="GB", salary_minor=6_000_000)
    make_employee(db, country="GB", salary_minor=6_000_000)
    make_employee(db, country="US", salary_minor=12_000_000)
    countries = run(as_admin).json()["countries"]
    assert countries[0] == {"country": "GB", "country_name": "United Kingdom", "currency": "GBP",
                            "headcount": 2, "gross_minor": 1_000_000,
                            "gross_usd_cents": 1_270_000}  # fmt: skip


def test_one_run_per_month(as_admin, db):
    make_employee(db)
    assert run(as_admin).status_code == 201
    second = run(as_admin)
    assert second.status_code == 409
    assert second.json()["message"] == "Payroll for 2026-05 has already been run."


def test_future_month_is_refused(as_admin):
    r = run(as_admin, month=7)
    assert r.status_code == 422
    assert r.json()["fields"] == {"month": "cannot run payroll for a month that has not started"}


def test_viewer_can_read_runs_but_not_create(as_admin, as_viewer, db):
    make_employee(db)
    assert run(as_viewer).status_code == 403


def test_runs_listed_newest_first(as_admin, db):
    make_employee(db)
    run(as_admin, month=3)
    run(as_admin, month=5)
    runs = as_admin.get("/api/payroll/runs").json()
    assert [(r["year"], r["month"]) for r in runs] == [(2026, 5), (2026, 3)]


def test_payslips_filter_and_page(as_admin, db):
    for i in range(5):
        make_employee(db, name=f"US {i}")
    make_employee(db, name="Brit", country="GB")
    rid = run(as_admin).json()["id"]
    gb = as_admin.get(f"/api/payroll/runs/{rid}/payslips?country=GB").json()
    page2 = as_admin.get(f"/api/payroll/runs/{rid}/payslips?size=2&page=2").json()
    assert [s["full_name"] for s in gb["items"]] == ["Brit"]
    assert page2["total"] == 6
    assert len(page2["items"]) == 2


def test_unknown_run(as_admin):
    assert as_admin.get("/api/payroll/runs/999999").status_code == 404
    assert as_admin.get("/api/payroll/runs/999999/payslips").status_code == 404


def test_history_rows_untouched_by_payroll(as_admin, db):
    emp = make_employee(db)
    run(as_admin)
    rows = db.scalars(select(SalaryChange).where(SalaryChange.employee_id == emp.id)).all()
    assert len(rows) == 1
