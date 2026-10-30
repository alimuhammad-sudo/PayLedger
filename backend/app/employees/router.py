from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.auth.deps import DB, Admin, AnyUser
from app.compensation.service import record_change
from app.core.db import get_today
from app.core.reference import CHANGE_REASONS, COUNTRIES, DEPARTMENTS, LEVELS
from app.employees import service
from app.employees.schemas import (
    EmployeeCreate,
    EmployeeDetail,
    EmployeePage,
    EmployeeUpdate,
    LeaveIn,
    SalaryChangeIn,
    SortKey,
    Status,
)

router = APIRouter(prefix="/api", tags=["employees"])
Today = Annotated[date, Depends(get_today)]


class CountryOut(BaseModel):
    code: str
    name: str
    currency: str


class ReferenceOut(BaseModel):
    countries: list[CountryOut]
    departments: list[str]
    levels: list[str]
    change_reasons: list[str]


@router.get("/reference", response_model=ReferenceOut)
def reference(_: AnyUser) -> ReferenceOut:
    return ReferenceOut(
        countries=[CountryOut(**c.__dict__) for c in COUNTRIES.values()],
        departments=list(DEPARTMENTS),
        levels=list(LEVELS),
        change_reasons=list(CHANGE_REASONS),
    )


@router.get("/employees", response_model=EmployeePage)
def list_employees(
    db: DB,
    _: AnyUser,
    today: Today,
    search: Annotated[str | None, Query(max_length=100)] = None,
    country: Annotated[str | None, Query(max_length=2)] = None,
    department: Annotated[str | None, Query(max_length=40)] = None,
    level: Annotated[str | None, Query(max_length=20)] = None,
    status: Status = "active",
    sort: SortKey = "name",
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> EmployeePage:
    filters = service.Filters(search, country, department, level, status)
    return service.search(db, filters, today, sort=sort, desc=order == "desc", page=page,
                          size=size)  # fmt: skip


@router.get("/employees/{employee_id}", response_model=EmployeeDetail)
def get_employee(employee_id: int, db: DB, _: AnyUser, today: Today) -> EmployeeDetail:
    return service.get_detail(db, employee_id, today)


@router.post("/employees", response_model=EmployeeDetail, status_code=status.HTTP_201_CREATED)
def create_employee(body: EmployeeCreate, db: DB, user: Admin, today: Today) -> EmployeeDetail:
    return service.get_detail(db, service.create(db, body, user, today), today)


@router.patch("/employees/{employee_id}", response_model=EmployeeDetail)
def update_employee(
    employee_id: int, body: EmployeeUpdate, db: DB, _: Admin, today: Today
) -> EmployeeDetail:
    service.update(db, employee_id, body)
    return service.get_detail(db, employee_id, today)


@router.put("/employees/{employee_id}/leaving-date", response_model=EmployeeDetail)
def set_leaving_date(
    employee_id: int, body: LeaveIn, db: DB, _: Admin, today: Today
) -> EmployeeDetail:
    service.set_leaving_date(db, employee_id, body.end_date)
    return service.get_detail(db, employee_id, today)


@router.delete("/employees/{employee_id}/leaving-date", response_model=EmployeeDetail)
def clear_leaving_date(employee_id: int, db: DB, _: Admin, today: Today) -> EmployeeDetail:
    service.set_leaving_date(db, employee_id, None)
    return service.get_detail(db, employee_id, today)


@router.post(
    "/employees/{employee_id}/salary-changes",
    response_model=EmployeeDetail,
    status_code=status.HTTP_201_CREATED,
)
def change_salary(
    employee_id: int, body: SalaryChangeIn, db: DB, user: Admin, today: Today
) -> EmployeeDetail:
    record_change(db, employee_id, body, user, today)
    return service.get_detail(db, employee_id, today)
