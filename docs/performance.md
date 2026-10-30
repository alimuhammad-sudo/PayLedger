# Performance

Target: every screen feels instant on 10,000 employees, on a single small backend.

## Measured

Seeded database (10,000 employees, 41,457 salary changes), backend on a laptop, local
PostgreSQL 17. Median of 15 requests after one warm-up, measured over HTTP.

| Request | Median (ms) |
|---|---|
| People, page 1 | 35 |
| People, page 300 | 33 |
| People, sorted by salary in USD | 26 |
| People, text search | 47 |
| One person with full history | 15 |
| Overview summary (mean, median, quartiles) | 33 |
| Median by country | 46 |
| Salary distribution | 40 |
| Run payroll for a month (9,428 payslips) | 2,341 |

| Bulk job | Time |
|---|---|
| Seed 10,000 employees with history (generate + load) | about 4 s |
| Backend test suite (111 tests, real PostgreSQL) | about 15 s |

## What makes it fast

**The current salary is a column.** `employees.salary_minor` is updated in the same
transaction as each history row, so listing and analysing 10,000 people never needs a
"latest change per person" query. The history table is only read for one person's profile
and for payroll (salary in force at a month's end).

**Statistics run in PostgreSQL.** Salaries are converted to US cents inside the query (salary
x rate in force x 10^(2 - currency digits)) and aggregated with `avg` and `percentile_cont`.
No rows travel to Python. Sorting the directory by salary uses the same expression, so
INR and USD salaries are compared fairly.

**Indexes match the filters.** Country, department, level, name and leaving date are
indexed; salary history is indexed on `(employee_id, effective_on)`.

**The seed uses COPY.** Employees and history are streamed with PostgreSQL `COPY`, one round
trip per table. Over the internet to a hosted database, thousands of separate INSERTs would
take minutes; COPY keeps it to seconds.

**The UI never holds 10,000 rows.** Lists are paged on the server. Search is debounced
(300 ms), and the previous page stays visible, dimmed, while the next one loads.

## Known limits and next steps

| Pressure | Next step |
|---|---|
| Payroll run takes about 2 s for 9,400 payslips | Write payslips with COPY, as the seed does (they are inserted in one batch today) |
| Text search scans with `ILIKE '%term%'` | A `pg_trgm` index on name and email |
| Analytics repeat the same work for every viewer | Cache per filter, cleared when salaries change |
