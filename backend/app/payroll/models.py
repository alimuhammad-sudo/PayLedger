from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PayrollRun(Base):
    __tablename__ = "payroll_runs"
    __table_args__ = (
        UniqueConstraint("year", "month", name="payroll_runs_one_per_month"),
        CheckConstraint("month between 1 and 12", name="payroll_runs_month_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    headcount: Mapped[int] = mapped_column(nullable=False)
    total_usd_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Payslip(Base):
    """What one employee is owed for one run. Values are copied, so the run never
    changes when salaries change later."""

    __tablename__ = "payslips"
    __table_args__ = (
        UniqueConstraint("run_id", "employee_id", name="payslips_one_per_employee"),
        Index("payslips_run_country_idx", "run_id", "country"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    staff_id: Mapped[str] = mapped_column(String(12), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    annual_salary_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    days_paid: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    days_in_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    gross_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gross_usd_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
