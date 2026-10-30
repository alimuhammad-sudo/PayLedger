"""Deterministic demo data: 10,000 employees with salary history.

Pure Python: no database. The same seed always gives the same people, salaries and
dates. Names come from Faker with a locale per country so a German employee has a German
name. Salaries follow a simple pay model:

    annual USD = level base x department factor x country factor x individual spread

converted to local currency at the planning rate and rounded to a sensible step. History
walks back from today's salary through yearly reviews (2-7%) and the occasional
promotion (10-16%), on the anniversary of the start date.
"""

import random
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from faker import Faker

from app.core.money import MINOR_DIGITS
from app.core.reference import COUNTRIES, LEVELS

ANCHOR = date(2026, 9, 30)  # the "today" the data is generated for
SEED = 7_310
RATES_FROM = date(2026, 1, 1)
USD_PER_UNIT: dict[str, str] = {
    "USD": "1", "GBP": "1.27", "EUR": "1.08", "INR": "0.012", "JPY": "0.0066",
    "CAD": "0.73", "BRL": "0.19", "MXN": "0.055",
}  # fmt: skip

LOCALES = {"US": "en_US", "GB": "en_GB", "DE": "de_DE", "FR": "fr_FR", "IN": "en_IN",
           "JP": "ja_JP", "CA": "en_CA", "BR": "pt_BR", "MX": "es_MX"}  # fmt: skip
COUNTRY_SHARE = {"US": 28, "IN": 18, "GB": 11, "DE": 9, "BR": 8, "CA": 7, "MX": 7, "JP": 6,
                 "FR": 6}  # fmt: skip
COUNTRY_PAY = {"US": 1.0, "GB": 0.82, "DE": 0.85, "FR": 0.78, "IN": 0.28, "JP": 0.7, "CA": 0.82,
               "BR": 0.33, "MX": 0.35}  # fmt: skip
DEPT_SHARE = {"Engineering": 29, "Product": 6, "Design": 4, "Sales": 15, "Marketing": 7,
              "Customer Success": 14, "Finance": 5, "People": 4, "Operations": 12,
              "Legal": 4}  # fmt: skip
DEPT_PAY = {"Engineering": 1.1, "Product": 1.08, "Design": 1.0, "Sales": 1.02, "Marketing": 0.95,
            "Customer Success": 0.82, "Finance": 1.0, "People": 0.9, "Operations": 0.88,
            "Legal": 1.12}  # fmt: skip
LEVEL_SHARE = {"Associate": 16, "Mid": 26, "Senior": 24, "Staff": 9, "Principal": 3,
               "Manager": 14, "Director": 6, "VP": 2}  # fmt: skip
LEVEL_PAY_USD = {"Associate": 55_000, "Mid": 76_000, "Senior": 102_000, "Staff": 138_000,
                 "Principal": 172_000, "Manager": 128_000, "Director": 188_000,
                 "VP": 255_000}  # fmt: skip
ROLE = {"Engineering": "Engineer", "Product": "Product Manager", "Design": "Designer",
        "Sales": "Account Executive", "Marketing": "Marketer",
        "Customer Success": "Customer Success Manager", "Finance": "Accountant",
        "People": "People Partner", "Operations": "Operations Specialist",
        "Legal": "Counsel"}  # fmt: skip
STEP = {"JPY": 10_000, "INR": 5_000}  # salaries are agreed in round numbers


@dataclass(frozen=True)
class Change:
    effective_on: date
    old_minor: int | None
    new_minor: int
    reason: str


@dataclass(frozen=True)
class Person:
    staff_number: int
    full_name: str
    email: str
    job_title: str
    department: str
    level: str
    country: str
    currency: str
    start_date: date
    end_date: date | None
    salary_minor: int
    history: tuple[Change, ...] = field(default_factory=tuple)


def job_title(department: str, level: str) -> str:
    role = ROLE[department]
    return {
        "Associate": f"Associate {role}", "Mid": role, "Senior": f"Senior {role}",
        "Staff": f"Staff {role}", "Principal": f"Principal {role}",
        "Manager": f"{department} Manager", "Director": f"Director of {department}",
        "VP": f"VP {department}",
    }[level]  # fmt: skip


def _ascii(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if c.isascii() and c.isalpha())


def _pick(rng: random.Random, weights: dict[str, float]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def _round_local(usd: float, currency: str) -> int:
    local = Decimal(str(usd)) / Decimal(USD_PER_UNIT[currency])
    step = STEP.get(currency, 500)
    whole = max(int(local / step + Decimal("0.5")) * step, step)
    return whole * 10 ** MINOR_DIGITS[currency]


def _anniversaries(start: date, until: date) -> list[date]:
    out = []
    for years in range(1, 40):
        try:
            day = start.replace(year=start.year + years)
        except ValueError:  # 29 February
            day = start.replace(year=start.year + years, day=28)
        if day > until:
            break
        out.append(day)
    return out


def generate(count: int = 10_000, seed: int = SEED, anchor: date = ANCHOR) -> list[Person]:
    rng = random.Random(seed)
    fakers = {code: Faker(loc) for code, loc in LOCALES.items()}
    for i, f in enumerate(fakers.values()):
        f.seed_instance(seed + i)
    emails: set[str] = set()
    people: list[Person] = []

    for n in range(1, count + 1):
        country = _pick(rng, COUNTRY_SHARE)
        currency = COUNTRIES[country].currency
        dept = _pick(rng, DEPT_SHARE)
        level = _pick(rng, LEVEL_SHARE)
        f = fakers[country]
        if country == "JP":
            first, last = f.first_romanized_name(), f.last_romanized_name()
        else:
            first, last = f.first_name(), f.last_name()
        parts = [p for p in (_ascii(first).lower(), _ascii(last).lower()) if p]
        local = ".".join(parts) if parts else f"staff{n}"  # names with no Latin letters
        email = f"{local}@acme-hr.example"
        if email in emails:
            email = f"{local}{n}@acme-hr.example"
        emails.add(email)

        senior = LEVELS.index(level) >= LEVELS.index("Staff")
        tenure_days = rng.randint(45, 365 * (12 if senior else 6))
        start = anchor - timedelta(days=tenure_days)

        usd = (LEVEL_PAY_USD[level] * DEPT_PAY[dept] * COUNTRY_PAY[country]
               * rng.uniform(0.86, 1.16))  # fmt: skip
        current = _round_local(usd, currency)
        unit = STEP.get(currency, 500) * 10 ** MINOR_DIGITS[currency]

        # Walk back from today's salary to the starting salary.
        reviews = _anniversaries(start, anchor)[-6:]
        amounts = [current]
        reasons = []
        for _ in reviews:
            promoted = rng.random() < 0.12
            pct = rng.uniform(0.10, 0.16) if promoted else rng.uniform(0.02, 0.07)
            reasons.append("Promotion" if promoted else "Annual review")
            amounts.append(max(int(amounts[-1] / (1 + pct) / unit) * unit, unit))
        amounts.reverse()
        reasons.reverse()
        history = [Change(start, None, amounts[0], "Starting salary")]
        for day, old, new, why in zip(reviews, amounts[:-1], amounts[1:], reasons, strict=True):
            history.append(Change(day, old, new, why))

        end = None
        if rng.random() < 0.08:
            earliest = history[-1].effective_on + timedelta(days=1)
            if earliest < anchor:
                end = earliest + timedelta(days=rng.randint(0, (anchor - earliest).days))

        people.append(
            Person(
                staff_number=n, full_name=f"{first} {last}", email=email,
                job_title=job_title(dept, level), department=dept, level=level,
                country=country, currency=currency, start_date=start, end_date=end,
                salary_minor=current, history=tuple(history),
            )
        )  # fmt: skip
    return people
