from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Employee(Base):
    """One person. `salary_minor` is the annual salary in force today, in the smallest
    unit of `currency`; it is only ever changed together with a SalaryChange row."""

    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("salary_minor > 0", name="employees_salary_positive"),
        CheckConstraint("end_date is null or end_date >= start_date", name="employees_dates"),
        Index("employees_country_idx", "country"),
        Index("employees_department_idx", "department"),
        Index("employees_level_idx", "level"),
        Index("employees_name_idx", "full_name"),
        Index("employees_end_date_idx", "end_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    job_title: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[str] = mapped_column(String(40), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    currency: Mapped[str] = mapped_column(ForeignKey("currencies.code"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    salary_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
