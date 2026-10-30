from dataclasses import dataclass
from datetime import date

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User
from app.compensation.models import SalaryChange
from app.core.errors import Conflict, Invalid, NotFound
from app.core.fx import Currency, FxRate
from app.core.money import MoneyError, parse_amount
from app.core.reference import COUNTRIES
from app.employees.models import Employee
from app.employees.schemas import (
    EmployeeCreate,
    EmployeeDetail,
    EmployeePage,
    EmployeeRow,
    EmployeeUpdate,
    SalaryChangeOut,
    SortKey,
    Status,
)

STARTING_SALARY = "Starting salary"


@dataclass(frozen=True)
class Filters:
    search: str | None = None
    country: str | None = None
    department: str | None = None
    level: str | None = None
    status: Status = "active"


def staff_id_for(employee_id: int) -> str:
    return f"ACM{employee_id:05d}"


def usd_cents_expr(today: date) -> tuple[ColumnElement, Select]:
    """Annual salary in US cents as a SQL expression, using the rate in force today.
    Returns the expression and the rates subquery it needs joined."""
    rates = (
        select(FxRate.currency, FxRate.usd_per_unit)
        .where(FxRate.valid_from <= today)
        .order_by(FxRate.currency, FxRate.valid_from.desc())
        .distinct(FxRate.currency)
        .subquery("rates")
    )
    expr = Employee.salary_minor * rates.c.usd_per_unit * func.power(10, 2 - Currency.minor_digits)
    return expr, rates


def _with_usd(stmt: Select, today: date) -> tuple[Select, ColumnElement]:
    expr, rates = usd_cents_expr(today)
    stmt = stmt.join(Currency, Currency.code == Employee.currency).join(
        rates, rates.c.currency == Employee.currency
    )
    return stmt, expr


def apply_filters(stmt: Select, f: Filters, today: date) -> Select:
    if f.search and (term := f.search.strip()):
        like = f"%{term}%"
        stmt = stmt.where(
            or_(Employee.full_name.ilike(like), Employee.email.ilike(like),
                Employee.staff_id.ilike(f"{term}%"))
        )  # fmt: skip
    if f.country:
        stmt = stmt.where(Employee.country == f.country)
    if f.department:
        stmt = stmt.where(Employee.department == f.department)
    if f.level:
        stmt = stmt.where(Employee.level == f.level)
    if f.status == "active":
        stmt = stmt.where(or_(Employee.end_date.is_(None), Employee.end_date >= today))
    elif f.status == "left":
        stmt = stmt.where(Employee.end_date < today)
    return stmt


def is_active(emp: Employee, today: date) -> bool:
    return emp.end_date is None or emp.end_date >= today


def _row(emp: Employee, usd: float, today: date) -> EmployeeRow:
    return EmployeeRow(
        id=emp.id, staff_id=emp.staff_id, full_name=emp.full_name, email=emp.email,
        job_title=emp.job_title, department=emp.department, level=emp.level,
        country=emp.country, currency=emp.currency, start_date=emp.start_date,
        end_date=emp.end_date, active=is_active(emp, today), salary_minor=emp.salary_minor,
        salary_usd_cents=round(usd),
    )  # fmt: skip


def search(
    db: Session, f: Filters, today: date, *, sort: SortKey, desc: bool, page: int, size: int
) -> EmployeePage:
    total = db.scalar(apply_filters(select(func.count(Employee.id)), f, today)) or 0
    stmt, usd = _with_usd(select(Employee), today)
    stmt = apply_filters(stmt.add_columns(usd), f, today)
    column = {
        "name": Employee.full_name, "staff_id": Employee.staff_id,
        "start_date": Employee.start_date, "salary": usd, "department": Employee.department,
        "country": Employee.country, "level": Employee.level,
    }[sort]  # fmt: skip
    stmt = stmt.order_by(column.desc() if desc else column.asc(), Employee.id)
    stmt = stmt.offset((page - 1) * size).limit(size)
    items = [_row(emp, value, today) for emp, value in db.execute(stmt)]
    return EmployeePage(items=items, total=total, page=page, size=size)


def get_detail(db: Session, employee_id: int, today: date) -> EmployeeDetail:
    stmt, usd = _with_usd(select(Employee), today)
    found = db.execute(stmt.add_columns(usd).where(Employee.id == employee_id)).first()
    if found is None:
        raise NotFound("No employee with that id.")
    emp, value = found
    history = db.execute(
        select(SalaryChange, User.full_name)
        .outerjoin(User, User.id == SalaryChange.changed_by)
        .where(SalaryChange.employee_id == employee_id)
        .order_by(SalaryChange.effective_on.desc(), SalaryChange.id.desc())
    ).all()
    return EmployeeDetail(
        **_row(emp, value, today).model_dump(),
        history=[
            SalaryChangeOut(
                id=c.id,
                old_salary_minor=c.old_salary_minor,
                new_salary_minor=c.new_salary_minor,
                effective_on=c.effective_on,
                reason=c.reason,
                note=c.note,
                changed_by=name,
                changed_at=c.changed_at,
            )  # fmt: skip
            for c, name in history
        ],
    )


def _email_taken(db: Session, email: str, except_id: int | None = None) -> bool:
    stmt = select(Employee.id).where(func.lower(Employee.email) == email.lower())
    if except_id is not None:
        stmt = stmt.where(Employee.id != except_id)
    return db.scalar(stmt) is not None


def create(db: Session, data: EmployeeCreate, user: User, today: date) -> int:
    problems: dict[str, str] = {}
    country = COUNTRIES.get(data.country.upper())
    if country is None:
        problems["country"] = "choose one of the listed countries"
    if data.start_date > today:
        problems["start_date"] = "cannot be in the future"
    salary = None
    if country:
        try:
            salary = parse_amount(data.salary, country.currency)
        except MoneyError as exc:
            problems["salary"] = str(exc)
    if _email_taken(db, data.email):
        problems["email"] = "is already used by another employee"
    if problems:
        raise Invalid("Please fix the highlighted fields", problems)

    emp = Employee(
        staff_id="pending", full_name=data.full_name.strip(), email=data.email.lower(),
        job_title=data.job_title.strip(), department=data.department, level=data.level,
        country=country.code, currency=country.currency, start_date=data.start_date,
        salary_minor=salary,
    )  # fmt: skip
    db.add(emp)
    db.flush()
    emp.staff_id = staff_id_for(emp.id)
    db.add(
        SalaryChange(
            employee_id=emp.id, old_salary_minor=None, new_salary_minor=salary,
            effective_on=data.start_date, reason=STARTING_SALARY, changed_by=user.id,
        )
    )  # fmt: skip
    _commit(db)
    return emp.id


def update(db: Session, employee_id: int, data: EmployeeUpdate) -> None:
    emp = _get(db, employee_id)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in changes:
        changes["email"] = changes["email"].lower()
        if _email_taken(db, changes["email"], except_id=emp.id):
            raise Invalid.field("email", "is already used by another employee")
    for key, value in changes.items():
        setattr(emp, key, value.strip() if isinstance(value, str) else value)
    _commit(db)


def set_leaving_date(db: Session, employee_id: int, end_date: date | None) -> None:
    emp = _get(db, employee_id)
    if end_date is not None and end_date < emp.start_date:
        raise Invalid.field("end_date", f"cannot be before they started ({emp.start_date})")
    if end_date is None and emp.end_date is None:
        raise Conflict("This employee has no leaving date to remove.")
    emp.end_date = end_date
    _commit(db)


def _get(db: Session, employee_id: int) -> Employee:
    emp = db.get(Employee, employee_id)
    if emp is None:
        raise NotFound("No employee with that id.")
    return emp


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict("That change clashes with another record. Reload and try again.") from None
