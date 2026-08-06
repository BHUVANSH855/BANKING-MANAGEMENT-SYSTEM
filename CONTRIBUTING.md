# Contributing to BankSys

Thanks for taking a look at this project. It started as an academic/portfolio
banking system and has since had a full frontend redesign and a pass of
backend bug fixes — there's still plenty to improve, and contributions are
welcome.

## Before you start

- Open an issue describing the bug or feature before submitting a large PR,
  so we can agree on the approach first. Small fixes (typos, obvious bugs)
  can go straight to a PR.
- This is a learning-oriented project. Explain *why* behind non-trivial
  changes in the PR description, not just *what*.

## Development setup

```bash
git clone <this-repo>
cd BANKING-MANAGEMENT-SYSTEM
pip install -r requirements.txt
python app.py
```

The app serves at `http://127.0.0.1:5000` and auto-creates
`database/banking.db` from `database/init_db.sql` on first run.

To start from a clean database at any point:

```bash
python tools/reset_db.py
```

## Project layout (where things live)

- **API routes & business logic**: `app.py` (production entry point) and
  `backend/app/app.py` (a kept-in-sync copy used for local debug runs).
  Route handlers should stay thin — the actual logic belongs in
  `backend/app/models/models.py`.
- **Database schema**: `database/init_db.sql` is the source of truth. If you
  add a column or table, update this file — don't rely on
  `backend/app/core/db.py`'s inline fallback schema, which exists only as a
  safety net and is deliberately minimal.
- **Frontend**: plain HTML/CSS/JS in `frontend/`, no build step.
  - Shared API calls go in `frontend/js/api.js` — add new backend endpoints
    there rather than calling `fetch()` directly from a page script.
  - Shared UI behavior (toasts, modals, theme toggle) lives in
    `frontend/js/main.js`.
  - Each page has its own script in `frontend/js/pages/`.
  - Keep the two backend copies of the API (`app.py` and
    `backend/app/app.py`) in sync when you change an endpoint — see
    `FULL_STACK_FIX_REPORT.md` for why both exist.

## Coding style

- **Python**: follow PEP 8. Prefer explicit, readable code over clever
  one-liners — this project is used for learning as much as for running.
- **JavaScript**: vanilla ES6+, no build tooling. Match the existing
  pattern of one `BankAPI.xxx()` call per backend endpoint, and surface
  errors via `Toast.error()` rather than `alert()`.
- **SQL**: parameterized queries only (`?` placeholders) — never
  string-format user input into a query.

## Tests

There isn't an automated test suite yet. `backend/app/tests/` currently
holds a few **manual, ad-hoc scripts** (not pytest tests) used while
building the email/SMS/pincode integrations — some have hardcoded
credentials and broken imports and should not be run as-is (see
[SECURITY.md](SECURITY.md)). If you're picking up test coverage as a task:

- A pytest suite around `backend/app/models/models.py` (deposit, withdraw,
  transfer, lock/unlock, PIN change) using a temporary SQLite file would be
  the highest-value place to start.
- Please don't commit real credentials in any test file — use
  environment variables or a `.env.example` placeholder instead.

## Submitting a change

1. Fork and branch from `main` (`feature/short-description` or
   `fix/short-description`).
2. Make your change, keeping backend/frontend/database in sync if you touch
   the API surface (add/update the corresponding entry in `frontend/js/api.js`
   and the README's API reference table).
3. Test manually: run `python app.py`, exercise the affected flow in a
   browser, and check the Flask console for errors.
4. Open a PR describing what changed and why. Screenshots are appreciated
   for any frontend change.

## Reporting bugs

Open an issue with: steps to reproduce, what you expected, what actually
happened, and any relevant console/server output. For security-sensitive
issues, see [SECURITY.md](SECURITY.md) instead of opening a public issue.