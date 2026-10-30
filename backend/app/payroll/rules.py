"""Monthly pay, prorated for people who join or leave part-way through the month.

    gross = annual salary / 12 x days employed in the month / days in the month

rounded half up once, to a whole minor unit (cent, penny, yen).
"""

import calendar
from datetime import date
from decimal import Decimal

from app.core.money import round_half_up


def month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def days_employed(start: date, end: date | None, year: int, month: int) -> int:
    """Calendar days in the month on which the person was employed (inclusive)."""
    first, last = month_bounds(year, month)
    from_day = max(start, first)
    to_day = min(end, last) if end else last
    return max((to_day - from_day).days + 1, 0)


def monthly_gross(annual_minor: int, days_paid: int, days_in_month: int) -> int:
    if days_paid <= 0:
        return 0
    return round_half_up(Decimal(annual_minor) * days_paid / (12 * days_in_month))


def period_problem(year: int, month: int, today: date) -> str | None:
    """Why a payroll cannot be run for this month, or None if it can."""
    if not 1 <= month <= 12:
        return "month must be between 1 and 12"
    if year < 2000:
        return "year must be 2000 or later"
    if (year, month) > (today.year, today.month):
        return "cannot run payroll for a month that has not started"
    return None
