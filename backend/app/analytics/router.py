from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.analytics import service
from app.auth.deps import DB, AnyUser
from app.core.db import get_today
from app.core.reference import COUNTRIES
from app.employees.service import Filters

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
Today = Annotated[date, Depends(get_today)]


class Stats(BaseModel):
    """All amounts are annual salaries in US cents."""

    headcount: int
    total: int | None
    mean: int | None
    p25: int | None
    median: int | None
    p75: int | None
    min: int | None
    max: int | None


class Rate(BaseModel):
    currency: str
    usd_per_unit: str
    valid_from: date


class SummaryOut(Stats):
    as_of: date
    rates: list[Rate]


class Group(Stats):
    key: str
    label: str
    currency: str | None = None
    local_median: int | None = None


class BreakdownOut(BaseModel):
    by: service.Dimension
    groups: list[Group]


class Band(BaseModel):
    from_usd_cents: int = Field(alias="from")
    to_usd_cents: int = Field(alias="to")
    count: int


def filters(
    country: Annotated[str | None, Query(max_length=2)] = None,
    department: Annotated[str | None, Query(max_length=40)] = None,
    level: Annotated[str | None, Query(max_length=20)] = None,
) -> Filters:
    return Filters(None, country, department, level, "active")


FiltersDep = Annotated[Filters, Depends(filters)]


@router.get("/summary", response_model=SummaryOut)
def summary(db: DB, _: AnyUser, today: Today, f: FiltersDep) -> SummaryOut:
    return SummaryOut(
        **service.summary(db, f, today), as_of=today, rates=service.rates_used(db, today)
    )


@router.get("/breakdown", response_model=BreakdownOut)
def breakdown(
    db: DB, _: AnyUser, today: Today, f: FiltersDep, by: service.Dimension = "country"
) -> BreakdownOut:
    groups = []
    for g in service.breakdown(db, f, today, by):
        label = COUNTRIES[g["key"]].name if by == "country" and g["key"] in COUNTRIES else g["key"]
        groups.append(Group(**g, label=label))
    return BreakdownOut(by=by, groups=groups)


@router.get("/distribution", response_model=list[Band], response_model_by_alias=True)
def distribution(
    db: DB, _: AnyUser, today: Today, f: FiltersDep,
    bins: Annotated[int, Query(ge=2, le=50)] = 16,
) -> list[Band]:  # fmt: skip
    return [Band(**b) for b in service.distribution(db, f, today, bins)]
