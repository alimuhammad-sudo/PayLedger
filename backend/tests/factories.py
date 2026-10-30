from datetime import date
from itertools import count

from sqlalchemy.orm import Session

from app.compensation.models import SalaryChange
from app.core.reference import COUNTRIES
from app.employees.models import Employee
from app.employees.service import staff_id_for

_n = count(1)


def make_employee(
    db: Session,
    *,
    name: str = "Test Person",
    country: str = "US",
    salary_minor: int = 9_000_000,
    department: str = "Engineering",
    level: str = "Senior",
    start: date = date(2022, 1, 10),
    end: date | None = None,
    email: str | None = None,
) -> Employee:
    n = next(_n)
    emp = Employee(
        staff_id="pending",
        full_name=name,
        email=email or f"person{n}@acme-hr.example",
        job_title="Software Engineer",
        department=department,
        level=level,
        country=country,
        currency=COUNTRIES[country].currency,
        start_date=start,
        end_date=end,
        salary_minor=salary_minor,
    )
    db.add(emp)
    db.flush()
    emp.staff_id = staff_id_for(emp.id)
    db.add(
        SalaryChange(
            employee_id=emp.id,
            new_salary_minor=salary_minor,
            effective_on=start,
            reason="Starting salary",
        )
    )
    db.commit()
    return emp
