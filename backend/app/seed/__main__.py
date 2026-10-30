"""python -m app.seed [--reset] [--if-empty] [--count N]

Loads the demo organisation into the database in PAYROLL_DATABASE_URL.
Run `alembic upgrade head` first.
"""

import argparse
import sys
import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import make_engine
from app.seed.load import DEMO_ADMIN, DEMO_VIEWER, AlreadySeeded, reset, seed


def main() -> int:
    parser = argparse.ArgumentParser(description="Load 10,000 demo employees")
    parser.add_argument("--reset", action="store_true", help="delete all data first")
    parser.add_argument("--if-empty", action="store_true", help="do nothing if already seeded")
    parser.add_argument("--count", type=int, default=10_000)
    args = parser.parse_args()

    started = time.perf_counter()
    with Session(make_engine(get_settings().database_url)) as db:
        if args.reset:
            reset(db)
        try:
            loaded = seed(db, count=args.count)
        except AlreadySeeded as exc:
            if args.if_empty:
                print("Already seeded; nothing to do.")
                return 0
            print(exc, file=sys.stderr)
            return 1
    print(f"Loaded {loaded.employees:,} employees and {loaded.salary_changes:,} salary changes "
          f"in {time.perf_counter() - started:.1f}s.")  # fmt: skip
    print(f"Sign in as {DEMO_ADMIN} (admin) or {DEMO_VIEWER} (viewer).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
