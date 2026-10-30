"""Fixed lists the whole app agrees on: where ACME operates, its departments and levels."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Country:
    code: str
    name: str
    currency: str


COUNTRIES: dict[str, Country] = {
    c.code: c
    for c in (
        Country("US", "United States", "USD"),
        Country("GB", "United Kingdom", "GBP"),
        Country("DE", "Germany", "EUR"),
        Country("FR", "France", "EUR"),
        Country("IN", "India", "INR"),
        Country("JP", "Japan", "JPY"),
        Country("CA", "Canada", "CAD"),
        Country("BR", "Brazil", "BRL"),
        Country("MX", "Mexico", "MXN"),
    )
}

DEPARTMENTS: tuple[str, ...] = (
    "Engineering",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Customer Success",
    "Finance",
    "People",
    "Operations",
    "Legal",
)

# Career ladder, most junior first.
LEVELS: tuple[str, ...] = (
    "Associate",
    "Mid",
    "Senior",
    "Staff",
    "Principal",
    "Manager",
    "Director",
    "VP",
)

CHANGE_REASONS: tuple[str, ...] = (
    "Annual review",
    "Promotion",
    "Market adjustment",
    "Correction",
    "Other",
)
