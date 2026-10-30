from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, SmallInteger, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base


class Currency(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    minor_digits: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class FxRate(Base):
    """A planning rate: how many US dollars one unit of `currency` is worth, from a date."""

    __tablename__ = "fx_rates"
    __table_args__ = (UniqueConstraint("currency", "valid_from"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    currency: Mapped[str] = mapped_column(ForeignKey("currencies.code"), nullable=False)
    usd_per_unit: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)


def rates_on(session: Session, day: date) -> dict[str, Decimal]:
    """The rate in force on `day` for every currency that has one."""
    stmt = (
        select(FxRate.currency, FxRate.usd_per_unit)
        .where(FxRate.valid_from <= day)
        .order_by(FxRate.currency, FxRate.valid_from.desc())
        .distinct(FxRate.currency)
    )
    return dict(session.execute(stmt).tuples().all())
