"""When is a salary change allowed? Plain function, no database, so every rule has a test."""

from dataclasses import dataclass
from datetime import date

from app.core.reference import CHANGE_REASONS


@dataclass(frozen=True)
class ProposedChange:
    new_salary_minor: int
    effective_on: date
    reason: str
    note: str | None


@dataclass(frozen=True)
class EmployeeState:
    current_salary_minor: int
    start_date: date
    end_date: date | None
    last_change_on: date | None


def check_change(change: ProposedChange, emp: EmployeeState, today: date) -> dict[str, str]:
    """Every problem with the change, keyed by field. Empty means it is allowed."""
    problems: dict[str, str] = {}

    if change.new_salary_minor == emp.current_salary_minor:
        problems["new_salary"] = "is the same as the current salary"

    if change.effective_on > today:
        problems["effective_on"] = "cannot be in the future"
    elif change.effective_on < emp.start_date:
        problems["effective_on"] = f"cannot be before they started ({emp.start_date.isoformat()})"
    elif emp.last_change_on and change.effective_on < emp.last_change_on:
        problems["effective_on"] = (
            f"must be on or after the last change ({emp.last_change_on.isoformat()})"
        )
    elif emp.end_date and change.effective_on > emp.end_date:
        problems["effective_on"] = f"is after they left ({emp.end_date.isoformat()})"

    if change.reason not in CHANGE_REASONS:
        problems["reason"] = "choose one of the listed reasons"
    elif change.reason == "Other" and not (change.note or "").strip():
        problems["note"] = "explain the change when the reason is Other"

    return problems
