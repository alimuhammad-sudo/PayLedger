from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SalaryChange(Base):
    """Append-only: one row per salary change, never edited or deleted.

    The first row for an employee is their starting salary (old_salary_minor is null).
    """

    __tablename__ = "salary_changes"
    __table_args__ = (
        CheckConstraint("new_salary_minor > 0", name="salary_changes_positive"),
        Index("salary_changes_employee_idx", "employee_id", "effective_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    old_salary_minor: Mapped[int | None] = mapped_column(BigInteger)
    new_salary_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    effective_on: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(String(300))
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
