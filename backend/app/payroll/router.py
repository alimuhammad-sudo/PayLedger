from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.auth.deps import DB, Admin, AnyUser
from app.core.db import get_today
from app.core.reference import COUNTRIES
from app.payroll import service

router = APIRouter(prefix="/api/payroll", tags=["payroll"])
Today = Annotated[date, Depends(get_today)]


class RunIn(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    month: int
    headcount: int
    total_usd_cents: int
    created_at: datetime


class CountryTotal(BaseModel):
    country: str
    country_name: str
    currency: str
    headcount: int
    gross_minor: int
    gross_usd_cents: int


class RunDetail(RunOut):
    countries: list[CountryTotal]


class PayslipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    staff_id: str
    full_name: str
    country: str
    currency: str
    annual_salary_minor: int
    days_paid: int
    days_in_month: int
    gross_minor: int
    gross_usd_cents: int


class PayslipPage(BaseModel):
    items: list[PayslipOut]
    total: int
    page: int
    size: int


def _detail(db, run) -> RunDetail:
    countries = [
        CountryTotal(**t, country_name=COUNTRIES[t["country"]].name)
        for t in service.totals_by_country(db, run.id)
    ]
    return RunDetail(**RunOut.model_validate(run).model_dump(), countries=countries)


@router.get("/runs", response_model=list[RunOut])
def list_runs(db: DB, _: AnyUser) -> list[RunOut]:
    return [RunOut.model_validate(r) for r in service.list_runs(db)]


@router.post("/runs", response_model=RunDetail, status_code=status.HTTP_201_CREATED)
def create_run(body: RunIn, db: DB, user: Admin, today: Today) -> RunDetail:
    return _detail(db, service.run_payroll(db, body.year, body.month, user, today))


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: int, db: DB, _: AnyUser) -> RunDetail:
    return _detail(db, service.get_run(db, run_id))


@router.get("/runs/{run_id}/payslips", response_model=PayslipPage)
def list_payslips(
    run_id: int,
    db: DB,
    _: AnyUser,
    country: Annotated[str | None, Query(max_length=2)] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PayslipPage:
    service.get_run(db, run_id)
    items, total = service.payslips(db, run_id, country=country, search=search, page=page,
                                    size=size)  # fmt: skip
    return PayslipPage(items=[PayslipOut.model_validate(i) for i in items], total=total,
                       page=page, size=size)  # fmt: skip
