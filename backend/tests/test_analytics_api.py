"""Analytics checked against numbers worked out by hand.

Rates (conftest): GBP 1.27, JPY 0.0066, USD 1. Today is 2026-06-15.
Population: US 80k, 100k, 120k; GB 50k GBP (= 63.5k USD); JP 9M JPY (= 59.4k USD);
plus one person who has left (must be ignored).
"""

from datetime import date

import pytest

from tests.factories import make_employee


@pytest.fixture
def org(db):
    make_employee(db, country="US", salary_minor=8_000_000, level="Mid")
    make_employee(db, country="US", salary_minor=10_000_000, level="Senior")
    make_employee(db, country="US", salary_minor=12_000_000, level="Senior", department="Sales")
    make_employee(db, country="GB", salary_minor=5_000_000, level="Mid")
    make_employee(db, country="JP", salary_minor=9_000_000, level="Senior")
    make_employee(db, country="US", salary_minor=99_900_000, end=date(2026, 1, 31))


def test_summary_in_usd(as_viewer, org):
    s = as_viewer.get("/api/analytics/summary").json()
    # USD cents: 5.94M, 6.35M, 8M, 10M, 12M
    assert s["headcount"] == 5
    assert s["total"] == 42_290_000
    assert s["mean"] == 8_458_000
    assert s["median"] == 8_000_000
    assert s["p25"] == 6_350_000
    assert s["p75"] == 10_000_000
    assert (s["min"], s["max"]) == (5_940_000, 12_000_000)
    assert s["as_of"] == "2026-06-15"
    assert {"currency": "GBP", "usd_per_unit": "1.27", "valid_from": "2026-01-01"} in s["rates"]


def test_summary_filters(as_viewer, org):
    s = as_viewer.get("/api/analytics/summary?country=US&level=Senior").json()
    assert s["headcount"] == 2
    assert s["median"] == 11_000_000  # percentile_cont interpolates between 100k and 120k


def test_empty_selection(as_viewer, org):
    s = as_viewer.get("/api/analytics/summary?country=MX").json()
    assert s["headcount"] == 0
    assert s["median"] is None


def test_breakdown_by_country_includes_local_median(as_viewer, org):
    groups = as_viewer.get("/api/analytics/breakdown?by=country").json()["groups"]
    assert [g["key"] for g in groups] == ["US", "GB", "JP"]  # largest first, then by code
    us, gb, jp = groups
    assert us["label"] == "United States"
    assert us["median"] == 10_000_000
    assert gb["currency"] == "GBP"
    assert gb["local_median"] == 5_000_000
    assert gb["median"] == 6_350_000
    assert jp["local_median"] == 9_000_000


def test_breakdown_by_level_mixes_currencies(as_viewer, org):
    groups = {
        g["key"]: g for g in as_viewer.get("/api/analytics/breakdown?by=level").json()["groups"]
    }
    assert groups["Senior"]["headcount"] == 3
    assert groups["Senior"]["local_median"] is None  # no single currency


def test_distribution_covers_everyone_once(as_viewer, org):
    bands = as_viewer.get("/api/analytics/distribution?bins=4").json()
    assert len(bands) == 4
    assert sum(b["count"] for b in bands) == 5
    assert bands[0]["from"] == 5_940_000
    assert bands[-1]["count"] >= 1  # the maximum lands in the last band


def test_distribution_of_nobody_is_empty(as_viewer, org):
    assert as_viewer.get("/api/analytics/distribution?country=MX").json() == []


def test_analytics_need_sign_in(client):
    assert client.get("/api/analytics/summary").status_code == 401
