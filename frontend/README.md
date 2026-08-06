# BankSys — Vault Ledger Frontend (Redesigned)

A complete, drop-in replacement for the `frontend/` folder in
`BANKING-MANAGEMENT-SYSTEM`. Pure HTML/CSS/JS — no build step, no
frameworks. Copy this folder over your existing `frontend/` directory (or
point your Flask `static_folder`/`template_folder` at it) and it talks to
your existing Flask API as-is.

## What's inside

```
frontend/
├── index.html              Landing page + login + quick actions
├── login.html               Standalone login
├── account_access.html      Login / request-account chooser
├── create_account.html      Open a new account
├── request_account.html     Account opening request (see note below)
├── dashboard.html           Balance, deposit/withdraw/transfer, recent activity
├── deposit.html
├── withdraw.html
├── transfer.html
├── transactions.html        Full ledger lookup by account ID
├── admin_login.html         NEW — admin sign-in (was missing, see below)
├── admin_dashboard.html     Stats, vault balance, users, global ledger, change PIN
├── css/
│   ├── base.css              Design tokens, resets, typography
│   ├── components.css        Buttons, cards, forms, tables, toasts, modal, loader
│   └── pages.css              Hero, dashboard, admin, action-grid layouts
├── js/
│   ├── api.js                 Single source of truth for every API call
│   ├── main.js                 Theme toggle, nav, toasts, modal, reveal, count-up
│   └── pages/                  One small file per page, wiring forms to api.js
└── assets/
    └── bank-hero.png           Reused from your original repo
```

## Design

"Vault Ledger" — a deep navy/ink theme with a brass accent, passbook-style
cards (stitched left edge, ledger hole-punch), tabular monospace figures for
money, and rubber-stamp status badges. Fraunces for display type, Inter for
body copy, IBM Plex Mono for every number. Built-in dark ("Vault") and light
("Paper") modes via the sun/moon toggle in the navbar. Motion is deliberate:
a floating hero illustration, scroll reveals, an animated balance count-up,
button ripples, and a rotating "vault dial" loading spinner — no confetti or
gratuitous effects.

## Real mismatches found in the original frontend, and how they were fixed

1. **Transfer silently failed.** `transfer.html` posted fields named
   `from_account` / `to_account`, but `/api/transfer` reads `from_id` /
   `to_id`. Both defaulted to `0` server-side, so `models.transfer()` always
   raised "account not found." Fixed in `js/pages/transfer.js` — the form
   now sends `from_id`/`to_id`.

2. **New accounts opened with ₹0.** `create_account.html` sent a field named
   `deposit`; the backend reads `initial_deposit`. The number you typed was
   ignored. Fixed in `js/pages/create-account.js` and `request-account.js`.

3. **`admin_dashboard.html` linked to a page that didn't exist.** It redirects
   to `admin_login.html` when there's no admin session, but that file was
   never in the repo — so any admin without `localStorage.admin` set hit a
   404. Added `admin_login.html`, wired to `POST /api/admin/login`.

4. **Duplicate element IDs broke the dashboard.** `dashboard.html` had three
   forms (deposit/withdraw/transfer) that all reused `id="amount"` and
   `id="pin"`. `document.getElementById` always returns the *first* match,
   so withdraw and transfer silently read the deposit field's value. Every
   input now has a unique ID (`depositAmount`, `withdrawAmount`,
   `withdrawPin`, `transferAmount`, `transferPin`, …).

5. **Hardcoded `localhost` API base.** `app.js` pointed at
   `http://127.0.0.1:5000/api` unconditionally — meaning the deployed
   Render site could never reach its own backend. `js/api.js` now only uses
   that URL when actually running on `localhost`/`127.0.0.1`, and falls back
   to a same-origin `/api` path otherwise.

6. **Admin endpoints with no UI.** The backend exposes
   `/api/admin/bank-balance`, `/api/admin/transactions`, and
   `/api/admin/change-pin`, but nothing in the old frontend called them.
   `admin_dashboard.html` now surfaces all of it: a vault-balance stat card,
   a full cross-account transaction ledger, and a change-PIN form.

7. **Withdraw/transfer used raw HTML form POSTs.** Submitting either page
   navigated the browser to the raw JSON API response instead of showing
   feedback in the UI. Both are now `fetch`-based with toast notifications
   and inline validation.

8. **`admin_requests.html` had no backend behind it** — two hardcoded fake
   "pending requests" with buttons that did nothing (no approve/reject
   endpoint exists in the API). It's been dropped rather than shipped as
   dead UI; `request_account.html` now honestly explains that account
   opening is instant (it calls the real `/api/create_account`), since
   there's no approval-queue endpoint to wire it to.

## Known limitation this frontend can't fix on its own

`backend/app/app.py` (the version with the working `/api/*` routes) serves
static files from `Path(__file__).parent / "frontend"`, i.e.
`backend/app/frontend/`. Your actual `frontend/` folder lives at the repo
root. That's a backend path issue, not a frontend one — either move this
folder to `backend/app/frontend/`, update `FRONTEND_DIR` in `app.py`, or run
the root-level `app.py` (which uses Jinja templates instead of static
files) if you'd rather serve it that way.

Also worth knowing: there's no backend endpoint that verifies a regular
user's PIN at login — only `GET /api/account/:id` (existence check).  PINs
*are* verified server-side for withdraw and transfer. Login confirms the
account exists; the PIN gate happens at the point of an actual transaction,
matching how the backend is written today.

## Admin PIN handling

Every `/api/admin/*` endpoint requires the PIN on *every single call* (the
backend has no session/token system). Rather than prompting for it on each
click, the admin PIN is kept in `sessionStorage` for the current tab only —
cleared automatically when the tab closes, and cleared explicitly on
logout.
