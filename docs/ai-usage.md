# How AI was used

The brief asks for AI tools to be used deliberately. This records how.

**Tool:** Claude Code (Anthropic), working in the repository with shell access. Commits it
helped write carry a `Co-Authored-By` trailer.

## Method

1. **Decisions first, in writing.** Scope, stack and exclusions were decided before any code
   and committed as [requirements.md](requirements.md). The AI then drafted
   [design.md](design.md) from those decisions, before implementation.
2. **One feature per commit, each with tests.** Rules that need no database (money, salary
   changes, payroll proration) are plain functions with their own tests. Everything else is
   tested through the API against a real PostgreSQL database.
3. **Run it, don't assume it.** After the build passed, the app was driven in a real browser
   against the seeded backend, signing in, filtering, sorting, attempting an invalid salary
   change, running payroll, and checking a viewer cannot edit, watching for console and
   server errors.

## Prompts

The decisions and instructions given, verbatim:

> backend is same
> must haves are salary history, analytics, payroll, lgon roles and exports
> db is postgres

> lets exclude the csv export and keep the rest

> start building it

Exports were first listed as a must-have and then moved to the exclusions; the
requirements record the final position and the reason.

## What was checked, and what the AI got wrong

| What happened | How it was caught | Fix |
|---|---|---|
| The email validator rejects the reserved `.test` domain, so every login in the tests returned 422. | First test run. | Demo and test addresses use `acme-hr.example`. |
| An off-by-one when walking salary history backwards (`zip` of n review dates with n+1 amounts). | `strict=True` on `zip` raised at once. | Pair each review with the amounts before and after it. |
| The seed's email fallback could never trigger (an f-string with a dot is never empty), so a name with no Latin letters would make `.@domain`. | Lint (`SIM222`) flagged the always-true expression. | Build the address from the non-empty parts, else `staff<n>`. |
| The backend module had a factory but no `app` object, so `uvicorn app.main:app` failed. | Starting the server for the browser check. | Run with `--factory` locally; `index.py` builds the app for hosting. |
| The profile chart cut off its y-axis labels and started at zero, hiding the raises. | Looking at the screenshot. | Wider axis, compact labels, axis scaled to the data. |

## Not left to the AI

- **Money arithmetic.** Integer minor units, one rounding step, and tests with hand-worked
  values (including yen, which has no minor unit, and half-cent cases).
- **Authorization.** Tests assert a viewer gets 403 on every write.
- **Numbers in the docs.** Timings in [performance.md](performance.md) and test counts come
  from actual runs.
