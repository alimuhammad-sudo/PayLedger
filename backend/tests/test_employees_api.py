"""Directory, profile, add/edit, leaving date. Today is 2026-06-15 (conftest)."""

from datetime import date

from tests.factories import make_employee


def new_hire(**over) -> dict:
    body = {
        "full_name": "Grace Hopper",
        "email": "grace@acme-hr.example",
        "job_title": "Staff Engineer",
        "department": "Engineering",
        "level": "Staff",
        "country": "GB",
        "start_date": "2026-05-01",
        "salary": "98000",
    }
    return {**body, **over}


# ---- access ------------------------------------------------------------------


def test_directory_needs_sign_in(client):
    assert client.get("/api/employees").status_code == 401


def test_viewer_can_read_but_not_write(as_viewer, db):
    emp = make_employee(db)
    assert as_viewer.get(f"/api/employees/{emp.id}").status_code == 200
    assert as_viewer.post("/api/employees", json=new_hire()).status_code == 403
    assert as_viewer.patch(f"/api/employees/{emp.id}", json={"level": "Staff"}).status_code == 403
    change = {"new_salary": "1", "effective_on": "2026-06-01", "reason": "Promotion"}
    r = as_viewer.post(f"/api/employees/{emp.id}/salary-changes", json=change)
    assert r.status_code == 403
    assert r.json() == {"message": "Only HR admins can make changes."}


# ---- directory ---------------------------------------------------------------


def test_pages_and_counts(as_viewer, db):
    for i in range(12):
        make_employee(db, name=f"Person {i:02d}")
    body = as_viewer.get("/api/employees?size=5&page=3").json()
    assert body["total"] == 12
    assert [e["full_name"] for e in body["items"]] == ["Person 10", "Person 11"]


def test_search_matches_name_email_and_staff_id(as_viewer, db):
    a = make_employee(db, name="Ada Lovelace", email="ada@acme-hr.example")
    make_employee(db, name="Alan Turing")
    assert as_viewer.get("/api/employees?search=lovelace").json()["total"] == 1
    assert as_viewer.get("/api/employees?search=ada@").json()["total"] == 1
    assert as_viewer.get(f"/api/employees?search={a.staff_id}").json()["items"][0]["id"] == a.id


def test_filters_combine(as_viewer, db):
    make_employee(db, country="GB", department="Sales")
    make_employee(db, country="GB", department="Engineering")
    make_employee(db, country="US", department="Sales")
    r = as_viewer.get("/api/employees?country=GB&department=Sales").json()
    assert r["total"] == 1


def test_status_filter(as_viewer, db):
    make_employee(db, name="Here")
    make_employee(db, name="Gone", end=date(2026, 1, 31))
    make_employee(db, name="Leaving", end=date(2026, 7, 31))  # still active today

    def names(status):
        return sorted(e["full_name"] for e in
                      as_viewer.get(f"/api/employees?status={status}").json()["items"])  # fmt: skip

    assert names("active") == ["Here", "Leaving"]
    assert names("left") == ["Gone"]
    assert len(names("all")) == 3


def test_salary_sort_compares_in_usd(as_viewer, db):
    # INR 9,000,000.00 = 108,000 USD; JPY 9,000,000 = 59,400 USD; USD 100,000
    make_employee(db, name="India", country="IN", salary_minor=900_000_000)
    make_employee(db, name="Japan", country="JP", salary_minor=9_000_000)
    make_employee(db, name="States", country="US", salary_minor=10_000_000)

    items = as_viewer.get("/api/employees?sort=salary&order=desc").json()["items"]

    assert [e["full_name"] for e in items] == ["India", "States", "Japan"]
    assert [e["salary_usd_cents"] for e in items] == [10_800_000, 10_000_000, 5_940_000]


def test_unknown_sort_is_rejected(as_viewer):
    assert as_viewer.get("/api/employees?sort=password").status_code == 422


# ---- profile -----------------------------------------------------------------


def test_profile_has_history(as_viewer, db):
    emp = make_employee(db)
    body = as_viewer.get(f"/api/employees/{emp.id}").json()
    assert body["staff_id"] == emp.staff_id
    assert body["active"] is True
    assert [h["reason"] for h in body["history"]] == ["Starting salary"]


def test_unknown_employee_is_404(as_viewer):
    r = as_viewer.get("/api/employees/999999")
    assert r.status_code == 404
    assert r.json() == {"message": "No employee with that id."}


# ---- add / edit ----------------------------------------------------------------


def test_add_employee_records_starting_salary(as_admin):
    r = as_admin.post("/api/employees", json=new_hire())

    assert r.status_code == 201
    body = r.json()
    assert body["staff_id"] == f"ACM{body['id']:05d}"
    assert body["currency"] == "GBP"  # from the country
    assert body["salary_minor"] == 9_800_000
    (start,) = body["history"]
    assert start["reason"] == "Starting salary"
    assert start["old_salary_minor"] is None
    assert start["changed_by"] == "Ada Admin"


def test_add_employee_reports_every_problem(as_admin, db):
    make_employee(db, email="grace@acme-hr.example")
    r = as_admin.post("/api/employees", json=new_hire(country="ZZ", start_date="2027-01-01"))
    assert r.status_code == 422
    assert set(r.json()["fields"]) == {"country", "start_date", "email"}


def test_yen_salary_cannot_have_decimals(as_admin):
    r = as_admin.post("/api/employees", json=new_hire(country="JP", salary="9000000.50"))
    assert r.json()["fields"] == {"salary": "JPY has no decimal places"}


def test_edit_details(as_admin, db):
    emp = make_employee(db)
    r = as_admin.patch(f"/api/employees/{emp.id}", json={"level": "Staff", "job_title": " Lead "})
    assert r.json()["level"] == "Staff"
    assert r.json()["job_title"] == "Lead"


def test_edit_rejects_duplicate_email(as_admin, db):
    make_employee(db, email="taken@acme-hr.example")
    emp = make_employee(db)
    r = as_admin.patch(f"/api/employees/{emp.id}", json={"email": "TAKEN@acme-hr.example"})
    assert r.json()["fields"] == {"email": "is already used by another employee"}


# ---- leaving -----------------------------------------------------------------


def test_set_and_clear_leaving_date(as_admin, db):
    emp = make_employee(db)
    left = as_admin.put(f"/api/employees/{emp.id}/leaving-date", json={"end_date": "2026-05-31"})
    assert left.json()["active"] is False
    back = as_admin.delete(f"/api/employees/{emp.id}/leaving-date")
    assert back.json()["active"] is True
    assert as_admin.delete(f"/api/employees/{emp.id}/leaving-date").status_code == 409


def test_leaving_before_start_is_rejected(as_admin, db):
    emp = make_employee(db, start=date(2024, 1, 1))
    r = as_admin.put(f"/api/employees/{emp.id}/leaving-date", json={"end_date": "2023-12-31"})
    assert r.status_code == 422
    assert "end_date" in r.json()["fields"]


def test_reference_lists(as_viewer):
    body = as_viewer.get("/api/reference").json()
    assert {"code": "JP", "name": "Japan", "currency": "JPY"} in body["countries"]
    assert body["levels"][0] == "Associate"
