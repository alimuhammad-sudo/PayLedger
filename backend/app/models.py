"""Import every model so Base.metadata knows all tables (used by Alembic and tests)."""

from app.auth.models import User
from app.compensation.models import SalaryChange
from app.core.fx import Currency, FxRate
from app.employees.models import Employee
from app.payroll.models import PayrollRun, Payslip

__all__ = ["Currency", "Employee", "FxRate", "PayrollRun", "Payslip", "SalaryChange", "User"]
