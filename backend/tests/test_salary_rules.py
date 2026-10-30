from datetime import date

from app.compensation.rules import EmployeeState, ProposedChange, check_change

TODAY = date(2026, 6, 15)
EMP = EmployeeState(
    current_salary_minor=8_000_000,
    start_date=date(2022, 3, 1),
    end_date=None,
    last_change_on=date(2025, 4, 1),
)


def change(**kw) -> ProposedChange:
    base = dict(new_salary_minor=8_800_000, effective_on=TODAY, reason="Promotion", note=None)
    return ProposedChange(**{**base, **kw})


def test_valid_change_has_no_problems():
    assert check_change(change(), EMP, TODAY) == {}


def test_backdated_change_after_the_last_one_is_allowed():
    assert check_change(change(effective_on=date(2026, 1, 1)), EMP, TODAY) == {}


def test_same_salary_is_rejected():
    assert check_change(change(new_salary_minor=8_000_000), EMP, TODAY) == {
        "new_salary": "is the same as the current salary"
    }


def test_future_date_is_rejected():
    problems = check_change(change(effective_on=date(2026, 7, 1)), EMP, TODAY)
    assert problems == {"effective_on": "cannot be in the future"}


def test_before_start_date_is_rejected():
    problems = check_change(change(effective_on=date(2021, 1, 1)), EMP, TODAY)
    assert problems["effective_on"] == "cannot be before they started (2022-03-01)"


def test_history_stays_in_date_order():
    problems = check_change(change(effective_on=date(2025, 1, 1)), EMP, TODAY)
    assert problems["effective_on"] == "must be on or after the last change (2025-04-01)"


def test_change_after_leaving_is_rejected():
    left = EmployeeState(8_000_000, date(2022, 3, 1), date(2026, 5, 31), date(2025, 4, 1))
    problems = check_change(change(effective_on=date(2026, 6, 1)), left, TODAY)
    assert problems["effective_on"] == "is after they left (2026-05-31)"


def test_unknown_reason_is_rejected():
    assert check_change(change(reason="Because"), EMP, TODAY) == {
        "reason": "choose one of the listed reasons"
    }


def test_other_needs_a_note():
    assert check_change(change(reason="Other", note="  "), EMP, TODAY) == {
        "note": "explain the change when the reason is Other"
    }
    assert check_change(change(reason="Other", note="Retention offer"), EMP, TODAY) == {}


def test_reports_every_problem_at_once():
    problems = check_change(
        change(new_salary_minor=8_000_000, effective_on=date(2027, 1, 1), reason="?"), EMP, TODAY
    )
    assert set(problems) == {"new_salary", "effective_on", "reason"}
