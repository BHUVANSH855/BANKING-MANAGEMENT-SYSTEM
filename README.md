# 🏦 BankSys — Banking Management System

A full-stack banking management system: a Flask + SQLite REST API behind a
static HTML/CSS/JS frontend ("Vault Ledger" UI). Supports account creation,
deposits, withdrawals, transfers, transaction history, PIN-based security
with auto-lock, and a full admin console.

A Tkinter desktop GUI also ships in the same backend for local/offline use
(see [Desktop GUI](#desktop-gui-optional) below).

---

## Features

**Accounts**
- Create an account with an opening deposit
- Log in with account ID + PIN
- Self-service PIN change
- Account auto-locks after 3 wrong PIN attempts on withdraw/transfer

**Transactions**
- Deposit, withdraw, transfer between accounts
- Full transaction ledger per account, timestamped

**Admin console**
- PIN-protected admin login
- Bank-wide stats (total users, total deposits, total withdrawals)
- Central bank vault balance
- User management: view balances, lock/unlock, delete accounts
- Global transaction ledger across all accounts
- Change the admin PIN

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, Flask-CORS |
| Database | SQLite3 |
| Frontend | Static HTML, CSS, vanilla JavaScript (no build step, no framework) |
| Desktop GUI (optional) | Tkinter |
| Deployment | Gunicorn (e.g. on Render) |

---

## Project structure

```
BANKING-MANAGEMENT-SYSTEM/
├── app.py                     # Production entry point (gunicorn app:app)
├── requirements.txt
├── database/
│   ├── init_db.sql             # Full schema (accounts, transactions, system_funds)
│   └── banking.db              # Created automatically on first run (git-ignored)
├── backend/
│   ├── __init__.py
│   └── app/
│       ├── app.py               # Debug-friendly copy of the same API, for local runs
│       ├── models/models.py     # All account/transaction business logic
│       ├── core/
│       │   ├── db.py             # Connection handling + schema init
│       │   └── utils.py          # PIN hashing/verification
│       ├── services/
│       │   └── pincode_service.py
│       ├── gui/                  # Tkinter desktop client (optional, separate from the web app)
│       └── tests/                # Ad-hoc manual test scripts (see CONTRIBUTING)
├── frontend/
│   ├── index.html, dashboard.html, deposit.html, withdraw.html,
│   │   transfer.html, transactions.html, create_account.html,
│   │   request_account.html, admin_login.html, admin_dashboard.html, …
│   ├── css/                      # Design system (base, components, pages)
│   ├── js/
│   │   ├── api.js                 # Single source of truth for every API call
│   │   ├── main.js                 # Shared UI behaviors (theme, toasts, modals)
│   │   └── pages/                  # One script per page
│   └── assets/
└── tools/
    ├── reset_db.py              # Wipes and recreates the local database
    └── convert_mp4_to_gif.py
```

---

## Getting started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

This automatically creates `database/banking.db` from `database/init_db.sql`
on first run, and seeds a default admin account (see
[Default admin account](#default-admin-account) — **change this PIN before
any real use**).

Open **http://127.0.0.1:5000** in a browser.

### 3. Reset the database (optional, destructive)

```bash
python tools/reset_db.py
```

Wipes `database/banking.db` and rebuilds it from schema. All accounts and
transactions are lost.

---

## Default admin account

On first run, an admin account is created automatically:

- Email: `admin@bank.local`
- PIN: `123456`

**Change this immediately** via the admin console (Admin → Change admin PIN)
or `POST /api/admin/change-pin`. Do not deploy with the default PIN. See
[SECURITY.md](SECURITY.md).

---

## API reference

All endpoints are under `/api`. Requests/responses are JSON (form-encoded
also accepted on the write endpoints).

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/create_account` | Open a new account |
| POST | `/api/deposit` | Credit an account |
| POST | `/api/withdraw` | Debit an account (PIN required) |
| POST | `/api/transfer` | Move funds between two accounts (PIN required) |
| GET | `/api/transactions/<account_id>` | Transaction history for an account |
| GET | `/api/account/<account_id>` | Account details (no PIN hash) |
| POST | `/api/account/<account_id>/change-pin` | Self-service PIN change |
| POST | `/api/admin/login` | Admin PIN check |
| POST | `/api/admin/change-pin` | Change the admin PIN |
| POST | `/api/admin/bank-balance` | Central vault balance |
| POST | `/api/admin/stats` | Bank-wide totals |
| POST | `/api/admin/users` | List all user accounts |
| POST | `/api/admin/transactions` | Global transaction ledger |
| POST | `/api/admin/toggle-lock` | Lock/unlock a user account |
| POST | `/api/admin/delete-account` | Permanently delete a user account |

Every admin endpoint requires the admin PIN in the request body — there's no
session/token layer, so treat the PIN like a bearer credential.

---

## Desktop GUI (optional)

`backend/app/gui/gui.py` is a separate Tkinter client against the same
`models.py` layer. It's independent of the web app — running one doesn't
require the other. Launch it with:

```bash
python -m backend.app.gui.gui
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) — please report vulnerabilities privately,
not as a public issue.

## Code of conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

No license file is currently included. Until one is added, all rights are
reserved by the repository owner — open an issue if you'd like to use this
project under a specific license.