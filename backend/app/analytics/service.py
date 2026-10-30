"""Pay statistics, computed in PostgreSQL.

Every figure covers active employees on the reference date. Salaries are converted to US
cents inside the query (salary x rate in force x 10^(2 - currency digits)), then
aggregated with avg / percentile_cont, so no rows are pulled into Python. Results are
rounded to whole cents once, here.
"""

from datetime import date
from typing import Literal

from sqlalchemy import Select, func, literal_column, select
from sqlalchemy.orm import Session

from app.core.fx import Currency, FxRate
from app.employees.models import Employee
from app.employees.service import Filters, apply_filters, usd_cents_expr

Dimension = Literal["country", "department", "level"]
STATS = ("headcount", "total", "mean", "p25", "median", "p75", "min", "max")


def _active(filters: Filters) -> Filters:
    return Filters(None, filters.country, filters.department, filters.level, "active")


def _base(filters: Filters, today: date) -> tuple[Select, object]:
    """SELECT over active, filtered employees with the USD expression joined in."""
    usd, rates = usd_cents_expr(today)
    stmt = (
        select()
        .select_from(Employee)
        .join(Currency, Currency.code == Employee.currency)
        .join(rates, rates.c.currency == Employee.currency)
    )
    return apply_filters(stmt, _active(filters), today), usd


def _stat_columns(usd) -> list:
    return [
        func.count().label("headcount"),
        func.sum(usd).label("total"),
        func.avg(usd).label("mean"),
        func.percentile_cont(0.25).within_group(usd).label("p25"),
        func.percentile_cont(0.5).within_group(usd).label("median"),
        func.percentile_cont(0.75).within_group(usd).label("p75"),
        func.min(usd).label("min"),
        func.max(usd).label("max"),
    ]


def _to_ints(row) -> dict:
    return {k: (None if row[k] is None else round(row[k])) for k in STATS}


def summary(db: Session, filters: Filters, today: date) -> dict:
    stmt, usd = _base(filters, today)
    row = db.execute(stmt.add_columns(*_stat_columns(usd))).mappings().one()
    out = _to_ints(row)
    out["headcount"] = row["headcount"]
    return out


def breakdown(db: Session, filters: Filters, today: date, by: Dimension) -> list[dict]:
    """One row per group, largest headcount first. Grouping by country also gives the
    median in that country's own currency."""
    stmt, usd = _base(filters, today)
    key = getattr(Employee, by)
    columns = [key.label("key"), *_stat_columns(usd)]
    if by == "country":
        columns += [
            func.min(Employee.currency).label("currency"),
            func.percentile_cont(0.5).within_group(Employee.salary_minor).label("local_median"),
        ]
    stmt = stmt.add_columns(*columns).group_by(key).order_by(literal_column("headcount").desc(),
                                                              key)  # fmt: skip
    out = []
    for row in db.execute(stmt).mappings():
        item = {"key": row["key"], **_to_ints(row), "headcount": row["headcount"]}
        if by == "country":
            item["currency"] = row["currency"]
            item["local_median"] = round(row["local_median"])
        out.append(item)
    return out


def distribution(db: Session, filters: Filters, today: date, bins: int) -> list[dict]:
    """Equal-width salary bands (USD) from the lowest to the highest salary."""
    stmt, usd = _base(filters, today)
    values = stmt.add_columns(usd.label("usd")).subquery("salaries")
    lo, hi = db.execute(select(func.min(values.c.usd), func.max(values.c.usd))).one()
    if lo is None:
        return []
    lo, hi = float(lo), float(hi)
    width = max((hi - lo) / bins, 1.0)
    bucket = func.least(func.floor((values.c.usd - lo) / width), bins - 1).label("bucket")
    counts = dict(db.execute(select(bucket, func.count()).group_by(bucket)).tuples().all())
    return [
        {"from": round(lo + i * width), "to": round(lo + (i + 1) * width),
         "count": counts.get(i, 0)}
        for i in range(bins)
    ]  # fmt: skip


def rates_used(db: Session, today: date) -> list[dict]:
    stmt = (
        select(FxRate.currency, FxRate.usd_per_unit, FxRate.valid_from)
        .where(FxRate.valid_from <= today)
        .order_by(FxRate.currency, FxRate.valid_from.desc())
        .distinct(FxRate.currency)
    )
    return [
        {"currency": c, "usd_per_unit": str(r.normalize()), "valid_from": v}
        for c, r, v in db.execute(stmt)
    ]
