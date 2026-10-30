"""Money as whole numbers of a currency's smallest unit.

Amounts are ints everywhere. Decimal only appears when parsing what a person typed and
when applying an exchange rate, and every result is rounded exactly once.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# Digits after the decimal point for each currency ACME pays in.
MINOR_DIGITS: dict[str, int] = {
    "USD": 2,
    "GBP": 2,
    "EUR": 2,
    "INR": 2,
    "JPY": 0,
    "CAD": 2,
    "BRL": 2,
    "MXN": 2,
}


class MoneyError(ValueError):
    pass


def digits(currency: str) -> int:
    try:
        return MINOR_DIGITS[currency]
    except KeyError:
        raise MoneyError(f"unsupported currency {currency}") from None


def parse_amount(text: str, currency: str) -> int:
    """'85000.50' GBP -> 8500050. Refuses more decimals than the currency has."""
    try:
        value = Decimal(str(text).strip().replace(",", ""))
    except InvalidOperation:
        raise MoneyError(f"'{text}' is not a number") from None
    if not value.is_finite() or value <= 0:
        raise MoneyError("must be a positive amount")
    scaled = value.scaleb(digits(currency))
    if scaled != scaled.to_integral_value():
        places = digits(currency)
        raise MoneyError(
            f"{currency} has no decimal places" if places == 0
            else f"{currency} allows at most {places} decimal places"
        )  # fmt: skip
    return int(scaled)


def format_amount(minor: int, currency: str) -> str:
    """8500050 GBP -> '85000.50'. Plain digits, for APIs; the UI does locale formatting."""
    places = digits(currency)
    return f"{Decimal(minor).scaleb(-places):.{places}f}"


def round_half_up(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_HALF_UP))


def to_usd_cents(minor: int, currency: str, usd_per_unit: Decimal) -> int:
    """Convert an amount in `currency` minor units to US cents at `usd_per_unit`."""
    if usd_per_unit <= 0:
        raise MoneyError("exchange rate must be positive")
    return round_half_up(Decimal(minor).scaleb(2 - digits(currency)) * usd_per_unit)
