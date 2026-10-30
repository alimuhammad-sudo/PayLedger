from datetime import date

from sqlalchemy import BigInteger, cast, func, insert, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User
from app.compensation.models import SalaryChange
from app.core.errors import Conflict, Invalid, NotFound
from app.core.fx import rates_on
from app.core.money import to_usd_cents
from app.employees.models import Employee
from app.payroll.models import PayrollRun, Payslip
from app.payroll.rules import days_employed, month_bounds, monthly_gross, period_problem


def _taken(year: int, month: int) -> Conflict:
    return Conflict(f"Payroll for {year}-{month:02d} has already been run.")


def run_payroll(db: Session, year: int, month: int, user: User, today: date) -> PayrollRun:
    """Freeze what everyone employed during the month is owed.

    Salary used: the one in force on the last day of the month (from the history, so
    running a past month uses past salaries). Rate used: the one in force that day.
    """
    if problem := period_problem(year, month, today):
        raise Invalid.field("month", problem)
    if db.scalar(select(PayrollRun.id).where(PayrollRun.year == year, PayrollRun.month == month)):
        raise _taken(year, month)

    first, last = month_bounds(year, month)
    salary_at_month_end = (
        select(SalaryChange.employee_id, SalaryChange.new_salary_minor.label("salary"))
        .where(SalaryChange.effective_on <= last)
        .order_by(SalaryChange.employee_id, SalaryChange.effective_on.desc(),
                  SalaryChange.id.desc())
        .distinct(SalaryChange.employee_id)
        .subquery()
    )  # fmt: skip
    people = db.execute(
        select(Employee, salary_at_month_end.c.salary)
        .join(salary_at_month_end, salary_at_month_end.c.employee_id == Employee.id)
        .where(Employee.start_date <= last)
        .where(or_(Employee.end_date.is_(None), Employee.end_date >= first))
    ).all()

    rates = rates_on(db, last)
    missing = sorted({e.currency for e, _ in people} - set(rates))
    if missing:
        raise Invalid.field("month", f"no exchange rate for {', '.join(missing)} on {last}")

    days_in_month = last.day
    slips = []
    for emp, annual in people:
        days = days_employed(emp.start_date, emp.end_date, year, month)
        gross = monthly_gross(annual, days, days_in_month)
        slips.append(
            {
                "employee_id": emp.id, "staff_id": emp.staff_id, "full_name": emp.full_name,
                "country": emp.country, "currency": emp.currency, "annual_salary_minor": annual,
                "days_paid": days, "days_in_month": days_in_month, "gross_minor": gross,
                "gross_usd_cents": to_usd_cents(gross, emp.currency, rates[emp.currency]),
            }
        )  # fmt: skip

    run = PayrollRun(
        year=year, month=month, headcount=len(slips),
        total_usd_cents=sum(s["gross_usd_cents"] for s in slips), created_by=user.id,
    )  # fmt: skip
    db.add(run)
    try:
        db.flush()
        if slips:
            db.execute(insert(Payslip), [{**s, "run_id": run.id} for s in slips])
        db.commit()
    except IntegrityError:  # someone ran the same month at the same moment
        db.rollback()
        raise _taken(year, month) from None
    return run


def list_runs(db: Session) -> list[PayrollRun]:
    return list(
        db.scalars(select(PayrollRun).order_by(PayrollRun.year.desc(), PayrollRun.month.desc()))
    )


def get_run(db: Session, run_id: int) -> PayrollRun:
    run = db.get(PayrollRun, run_id)
    if run is None:
        raise NotFound("No payroll run with that id.")
    return run


def totals_by_country(db: Session, run_id: int) -> list[dict]:
    stmt = (
        select(
            Payslip.country,
            Payslip.currency,
            func.count().label("headcount"),
            cast(func.sum(Payslip.gross_minor), BigInteger).label("gross_minor"),
            cast(func.sum(Payslip.gross_usd_cents), BigInteger).label("gross_usd_cents"),
        )
        .where(Payslip.run_id == run_id)
        .group_by(Payslip.country, Payslip.currency)
        .order_by(func.sum(Payslip.gross_usd_cents).desc())
    )
    return [dict(r) for r in db.execute(stmt).mappings()]


def payslips(
    db: Session, run_id: int, *, country: str | None, search: str | None, page: int, size: int
) -> tuple[list[Payslip], int]:
    stmt = select(Payslip).where(Payslip.run_id == run_id)
    if country:
        stmt = stmt.where(Payslip.country == country)
    if search and (term := search.strip()):
        stmt = stmt.where(or_(Payslip.full_name.ilike(f"%{term}%"),
                              Payslip.staff_id.ilike(f"{term}%")))  # fmt: skip
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Payslip.full_name, Payslip.id).offset((page - 1) * size).limit(size)
    ).all()
    return list(rows), total
