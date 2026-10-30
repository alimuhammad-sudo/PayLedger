from datetime import date

import pytest

from app.payroll.rules import days_employed, month_bounds, monthly_gross, period_problem


def test_month_bounds_know_leap_years():
    assert month_bounds(2024, 2) == (date(2024, 2, 1), date(2024, 2, 29))
    assert month_bounds(2026, 2)[1] == date(2026, 2, 28)


@pytest.mark.parametrize(
    ("start", "end", "days"),
    [
        (date(2020, 1, 1), None, 30),  # employed all month
        (date(2026, 6, 20), None, 11),  # joined on the 20th: 20..30
        (date(2020, 1, 1), date(2026, 6, 10), 10),  # left on the 10th: 1..10
        (date(2026, 6, 5), date(2026, 6, 6), 2),  # joined and left within the month
        (date(2026, 7, 1), None, 0),  # not started yet
        (date(2020, 1, 1), date(2026, 5, 31), 0),  # left last month
        (date(2026, 6, 30), None, 1),  # joined on the last day
    ],
)
def test_days_employed_in_june_2026(start, end, days):
    assert days_employed(start, end, 2026, 6) == days


def test_full_month_is_one_twelfth():
    assert monthly_gross(12_000_000, 30, 30) == 1_000_000


def test_partial_month_is_prorated_by_days():
    # 120,000.00 a year, 11 of 30 days: 10,000.00 x 11/30 = 3,666.666.. -> 3,666.67
    assert monthly_gross(12_000_000, 11, 30) == 366_667


def test_zero_decimal_currency_rounds_to_whole_yen():
    # 9,000,000 yen a year, 10 of 31 days: 750,000 x 10/31 = 241,935.48 -> 241,935
    assert monthly_gross(9_000_000, 10, 31) == 241_935


def test_no_days_no_pay():
    assert monthly_gross(12_000_000, 0, 30) == 0


@pytest.mark.parametrize(
    ("year", "month", "problem"),
    [
        (2026, 6, None),
        (2025, 12, None),
        (2026, 7, "cannot run payroll for a month that has not started"),
        (2026, 13, "month must be between 1 and 12"),
        (1999, 5, "year must be 2000 or later"),
    ],
)
def test_period_rules(year, month, problem):
    assert period_problem(year, month, date(2026, 6, 15)) == problem
