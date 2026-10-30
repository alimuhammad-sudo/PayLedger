from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.core.reference import DEPARTMENTS, LEVELS

Department = Literal[DEPARTMENTS]  # type: ignore[valid-type]
Level = Literal[LEVELS]  # type: ignore[valid-type]
Status = Literal["active", "left", "all"]
SortKey = Literal["name", "staff_id", "start_date", "salary", "department", "country", "level"]


class EmployeeRow(BaseModel):
    id: int
    staff_id: str
    full_name: str
    email: str
    job_title: str
    department: str
    level: str
    country: str
    currency: str
    start_date: date
    end_date: date | None
    active: bool
    salary_minor: int
    salary_usd_cents: int


class EmployeePage(BaseModel):
    items: list[EmployeeRow]
    total: int
    page: int
    size: int


class SalaryChangeOut(BaseModel):
    id: int
    old_salary_minor: int | None
    new_salary_minor: int
    effective_on: date
    reason: str
    note: str | None
    changed_by: str | None
    changed_at: datetime


class EmployeeDetail(EmployeeRow):
    history: list[SalaryChangeOut]


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    job_title: str = Field(min_length=1, max_length=120)
    department: Department
    level: Level
    country: str = Field(min_length=2, max_length=2)
    start_date: date
    salary: str = Field(max_length=30, description="Annual salary, e.g. '85000' or '85000.50'")


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    job_title: str | None = Field(default=None, min_length=1, max_length=120)
    department: Department | None = None
    level: Level | None = None


class LeaveIn(BaseModel):
    end_date: date


class SalaryChangeIn(BaseModel):
    new_salary: str = Field(max_length=30)
    effective_on: date
    reason: str = Field(max_length=40)
    note: str | None = Field(default=None, max_length=300)
