# Banking Management System 🏦

A simple yet complete **Banking Management System** built with **Python**, **Flask**, **SQLite**, and a basic **HTML/CSS frontend**.  

This project supports:

- Creating customer accounts
- Secure PIN storage (hashed, not plain text)
- Deposits & withdrawals
- Account-to-account transfers
- Transaction history tracking
- CLI (terminal) interface
- REST API with simple HTML forms as a demo frontend

---

## 🔧 Tech Stack

- **Backend (API):** Flask + Flask-CORS :contentReference[oaicite:0]{index=0}  
- **Database:** SQLite (via `sqlite3`)   
- **Frontend:** Pure HTML + CSS forms (no framework)   
- **CLI Interface:** Python `main.py` menu-driven app :contentReference[oaicite:3]{index=3}  
- **Security:** PIN hashing using SHA-256 :contentReference[oaicite:4]{index=4}  

---

## ✨ Features

### Core Banking Operations

- **Create Account**
  - Stores name, optional email & phone, PIN (hashed), and initial balance.   

- **Deposit**
  - Add money to an account.
  - Automatically records a transaction entry. :contentReference[oaicite:6]{index=6}  

- **Withdraw**
  - Withdraw money after PIN verification (via API or CLI).
  - Checks for sufficient balance and logs each withdrawal.   

- **Transfer**
  - Transfer funds between two accounts in a single atomic operation.
  - Creates `Transfer-Out` and `Transfer-In` entries for transaction history.   

- **Transaction History**
  - View past transactions for a given account, ordered by time.   

- **Delete Account**
  - Delete an account (and related transactions via foreign keys).   

### Interfaces

- **CLI (Terminal) Application**
  - Menu-based system: create, view, deposit, withdraw, transfer, history, delete. :contentReference[oaicite:11]{index=11}  

- **REST API + HTML Frontend**
  - Flask app exposes `/api/...` endpoints.
  - Simple forms for:
    - Home dashboard (`index.html`)
    - Create Account, Deposit, Withdraw, Transfer, Transactions pages (connect to backend).   

- **Tkinter GUI (Debug Wrapper)**
  - `ui.py` is a debug-friendly launcher for a `BankGUI` class (if you add your own GUI in `gui.py`). :contentReference[oaicite:13]{index=13}  

---

## 📁 Project Structure

```text
.
├── app.py              # Flask backend and API routes (plus static file serving)
├── main.py             # CLI (terminal) interface
├── db.py               # Database connection + initialization helper
├── init_db.sql         # SQL schema for accounts & transactions
├── models.py           # Business logic for accounts and transactions
├── utils.py            # PIN hashing & verification
├── ui.py               # Tkinter GUI launcher / debug wrapper
├── frontend/
│   ├── index.html      # Dashboard page
│   ├── withdraw.html   # Withdraw form page
│   ├── create_account.html / deposit.html / transfer.html / ...
│   └── styles.css      # Shared styles for frontend pages
└── banking.db          # SQLite database (auto-created)
