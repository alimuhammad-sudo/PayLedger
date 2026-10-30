from decimal import Decimal

import pytest

from app.core.money import MoneyError, format_amount, parse_amount, to_usd_cents


@pytest.mark.parametrize(
    ("text", "currency", "minor"),
    [
        ("85000", "USD", 8_500_000),
        ("85000.5", "GBP", 8_500_050),
        ("1,250,000", "INR", 125_000_000),
        ("9000000", "JPY", 9_000_000),
        (" 72000.00 ", "EUR", 7_200_000),
    ],
)
def test_parse_amount(text, currency, minor):
    assert parse_amount(text, currency) == minor


@pytest.mark.parametrize(
    ("text", "currency", "message"),
    [
        ("9000000.5", "JPY", "JPY has no decimal places"),
        ("100.123", "USD", "USD allows at most 2 decimal places"),
        ("0", "USD", "must be a positive amount"),
        ("-5", "USD", "must be a positive amount"),
        ("lots", "USD", "'lots' is not a number"),
        ("100", "XYZ", "unsupported currency XYZ"),
    ],
)
def test_parse_amount_rejects(text, currency, message):
    with pytest.raises(MoneyError, match=message):
        parse_amount(text, currency)


def test_format_amount_respects_currency_digits():
    assert format_amount(8_500_050, "GBP") == "85000.50"
    assert format_amount(9_000_000, "JPY") == "9000000"


def test_usd_conversion_handles_zero_decimal_currency():
    # 9,000,000 yen at 0.0066 USD/yen = 59,400.00 USD
    assert to_usd_cents(9_000_000, "JPY", Decimal("0.0066")) == 5_940_000


def test_usd_conversion_rounds_half_up_once():
    # 1 penny at 1.265 USD/GBP = 1.265 cents -> 1 cent; 3 pennies -> 3.795 -> 4 cents
    assert to_usd_cents(1, "GBP", Decimal("1.265")) == 1
    assert to_usd_cents(3, "GBP", Decimal("1.265")) == 4
    assert to_usd_cents(1, "USD", Decimal("0.5")) == 1


def test_usd_conversion_refuses_bad_rate():
    with pytest.raises(MoneyError):
        to_usd_cents(100, "EUR", Decimal("0"))
