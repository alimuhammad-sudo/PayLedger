from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.compensation.models import SalaryChange
from app.compensation.rules import EmployeeState, ProposedChange, check_change
from app.core.errors import Invalid, NotFound
from app.core.money import MoneyError, parse_amount
from app.employees.models import Employee
from app.employees.schemas import SalaryChangeIn


def record_change(
    db: Session, employee_id: int, data: SalaryChangeIn, user: User, today: date
) -> None:
    """Append a history row and move the employee's current salary, in one transaction.

    The employee row is locked first, so two admins changing the same salary at the same
    moment are applied one after the other, each against the latest history.
    """
    emp = db.scalar(select(Employee).where(Employee.id == employee_id).with_for_update())
    if emp is None:
        raise NotFound("No employee with that id.")

    try:
        amount = parse_amount(data.new_salary, emp.currency)
    except MoneyError as exc:
        raise Invalid.field("new_salary", str(exc)) from None

    last_on = db.scalar(
        select(func.max(SalaryChange.effective_on)).where(SalaryChange.employee_id == emp.id)
    )
    problems = check_change(
        ProposedChange(amount, data.effective_on, data.reason, data.note),
        EmployeeState(emp.salary_minor, emp.start_date, emp.end_date, last_on),
        today,
    )
    if problems:
        raise Invalid("Please fix the highlighted fields", problems)

    db.add(
        SalaryChange(
            employee_id=emp.id,
            old_salary_minor=emp.salary_minor,
            new_salary_minor=amount,
            effective_on=data.effective_on,
            reason=data.reason,
            note=(data.note or "").strip() or None,
            changed_by=user.id,
        )
    )
    emp.salary_minor = amount
    db.commit()
