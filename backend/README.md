# Backend

FastAPI + SQLAlchemy 2 + PostgreSQL. Design: [../docs/design.md](../docs/design.md).

```bash
docker compose up -d db                 # from the repo root
pip install -e ".[dev]"
alembic upgrade head
python -m app.seed                      # --reset to start over, --if-empty for deploys
uvicorn app.main:create_app --factory --port 8050 --reload
```

Interactive API docs: http://localhost:8050/api/docs

## Settings (environment variables)

| Variable | Default | |
|---|---|---|
| `PAYROLL_ENV` | `dev` | `prod` requires a real secret and forces Secure cookies |
| `PAYROLL_DATABASE_URL` | local docker database | a plain `postgresql://` URL (e.g. from Neon) also works |
| `PAYROLL_SECRET_KEY` | dev-only value | signs session cookies; 32+ characters in prod |
| `PAYROLL_SESSION_HOURS` | `8` | session length |
| `PAYROLL_DEMO_PASSWORD` | `acme-payroll-demo` | password for the two seeded users |

## API

| Area | Routes |
|---|---|
| Auth | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` |
| People | `GET/POST /api/employees`, `GET/PATCH /api/employees/{id}`, `PUT/DELETE /api/employees/{id}/leaving-date` |
| Salary | `POST /api/employees/{id}/salary-changes` |
| Analytics | `GET /api/analytics/summary`, `/breakdown?by=`, `/distribution` |
| Payroll | `GET/POST /api/payroll/runs`, `GET /api/payroll/runs/{id}`, `/payslips` |
| Reference | `GET /api/reference` |

Writes need the `admin` role; reads accept either role.

## Tests

```bash
pytest                    # real PostgreSQL (payroll_test), each test rolled back
ruff check app tests migrations && ruff format --check app tests
alembic check             # models and migrations agree
```

Set `PAYROLL_TEST_DATABASE_URL` to point the tests at another database.
