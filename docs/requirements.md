# Requirements: Salary Management for ACME

## Who and why

**User:** the HR Manager at ACME, 10,000 employees across several countries.

**Today:** salaries live in Excel. Every change overwrites the old value, nobody can tell
what someone earned last year, and answering "what do we pay engineers in Germany?" means
building a pivot table by hand.

**Goal:** one web app where the HR Manager keeps every employee's pay, sees how it changed
over time, and gets answers about pay across the company without leaving the app.

## What we will build

1. **Employees and salary history**
   - Searchable, paginated list of all 10,000 employees with filters (country, department,
     level) and sorting.
   - Employee page showing current pay and every past change: amount, date it took effect,
     reason, and who made it.
   - A salary change is always a new dated entry. Old values are never overwritten.

2. **Pay analytics**
   - Headcount, total payroll, average and median pay.
   - The same figures split by country, department and level.
   - Pay in different currencies is converted to one reporting currency (USD) using fixed,
     dated exchange rates, so a report run twice gives the same answer.

3. **Payroll**
   - Generate a monthly payroll: what each active employee is owed that month, with totals
     per country.
   - A generated payroll is a saved record and does not change if salaries change later.

4. **Login and roles**
   - Email and password login.
   - **HR Admin:** can view and change everything.
   - **HR Viewer:** can view everything, cannot change anything.

**Data:** a seed script creates 10,000 realistic employees with salary history across
several countries, so the app can be demonstrated and tested at full size.

**Technical:** Python + FastAPI backend, PostgreSQL database, Next.js frontend. Money is
stored as whole numbers of the smallest currency unit (cents, pence, yen) to avoid
rounding errors.

## What we will not build, and why

| Left out | Reason |
|---|---|
| **CSV import and export** | The point is to move HR off spreadsheets, so the answers live in the app: history, analytics and payroll are all on screen. Importing safely needs row-by-row validation and duplicate handling, and the seed script covers the demo data. Both are good next steps. |
| **Paying people** (bank transfers, tax, benefits) | The problem is managing and understanding salary data. Actually paying people is a separate, heavily regulated system. |
| **Several organisations in one app** | Only ACME uses it. |
| **Approval flows and notifications** | The HR Manager is the person who approves. Every change is already recorded with who made it. |
| **Employee self-service, SSO, password reset** | The only user is HR. Basic login is enough to protect salary data for this scope. |
| **Live exchange rates** | They would make reports change minute to minute. Fixed dated rates keep numbers repeatable. |

## Done means

- The HR Manager can find any employee, change their salary with a reason, and see the
  old salary still in the history.
- The dashboard answers "average pay by country in USD" in one screen.
- A viewer account cannot change anything, even by calling the API directly.
- Tests run in seconds and give the same result every time.
