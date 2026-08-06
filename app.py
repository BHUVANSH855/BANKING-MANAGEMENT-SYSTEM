# File: app.py
"""
BankSys — production entry point.

This is the file Render (and `gunicorn app:app`) actually loads. It used to
only serve a handful of Jinja-templated pages and one broken raw-SQL
/create_account route with no /api/* endpoints at all — meaning the live
site could never actually deposit, withdraw, transfer, or do anything the
redesigned frontend calls. It now serves the static frontend/ folder as-is
and exposes the full /api/* surface backed by backend/app/models/models.py,
matching backend/app/app.py's logic exactly (kept in sync intentionally —
that file remains for local debugging via `python backend/app/app.py`).
"""
import traceback
import sys
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from backend.app.models import models
from backend.app.core.db import initialize_db
from backend.app.core.utils import verify_pin, hash_pin


def require_admin(pin):
    acc = models.get_account_by_email("admin@bank.local")
    if not acc or acc.get("role") != "ADMIN":
        return False
    return verify_pin(pin, acc["pin_hash"])


# ---- Paths (this file lives at the repo root, so no parent-hopping needed) ----
REPO_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = REPO_ROOT / "frontend"
DB_FILE = REPO_ROOT / "database" / "banking.db"
INIT_SQL = REPO_ROOT / "database" / "init_db.sql"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/")
CORS(app)


def ensure_db_initialized():
    """Initialize DB if missing (safe no-op if db exists)."""
    try:
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not DB_FILE.exists():
            print("banking.db not found -> initializing DB from schema")
            if INIT_SQL.exists():
                initialize_db(str(INIT_SQL))
            else:
                initialize_db()
            print("Database initialized.")
    except Exception:
        print("DB initialization failed (continuing):")
        traceback.print_exc()


# ------------------- STATIC FRONTEND -------------------
@app.route("/", methods=["GET"])
def index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return send_from_directory(str(FRONTEND_DIR), "index.html")
    return (
        "<h2>Frontend not found</h2>"
        f"<p>Expected: {index_path}</p>"
    ), 404


@app.route("/<path:filename>", methods=["GET"])
def static_files(filename):
    file_path = FRONTEND_DIR / filename
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(FRONTEND_DIR), filename)
    return (
        "<h2>Static file not found</h2>"
        f"<p>Requested: {filename}</p>"
    ), 404


# ------------------- API endpoints -------------------
@app.route("/api/create_account", methods=["POST"])
def api_create_account():
    try:
        data = request.form.to_dict() or request.get_json(force=False) or {}
        name = (data.get("name") or "").strip()
        pin = data.get("pin")
        if not name or not pin:
            return jsonify({"error": "name and pin required"}), 400
        email = data.get("email") or None
        phone = data.get("phone") or None
        initial_deposit = float(data.get("initial_deposit") or 0)
        account_id = models.create_account(name, email, phone, pin, initial_deposit)
        return jsonify({"account_id": account_id}), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/api/deposit", methods=["POST"])
def api_deposit():
    try:
        data = request.form.to_dict() or request.get_json(force=False) or {}
        account_id = int(data.get("account_id") or 0)
        amount = float(data.get("amount") or 0)
        if account_id <= 0 or amount <= 0:
            return jsonify({"error": "account_id and positive amount required"}), 400
        new_bal = models.deposit(account_id, amount)
        return jsonify({"balance": new_bal})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/api/withdraw", methods=["POST"])
def api_withdraw():
    try:
        data = request.form.to_dict() or request.get_json(force=False) or {}
        account_id = int(data.get("account_id") or 0)
        amount = float(data.get("amount") or 0)
        pin = data.get("pin") or ""
        if account_id <= 0 or amount <= 0 or not pin:
            return jsonify({"error": "account_id, amount and pin required"}), 400
        acc = models.get_account(account_id)
        if not acc:
            return jsonify({"error": "account not found"}), 404
        if not verify_pin(pin, acc["pin_hash"]):
            models.register_failed_attempt(account_id)
            return jsonify({"error": "invalid pin"}), 403
        models.reset_failed_attempts(account_id)
        new_bal = models.withdraw(account_id, amount)
        return jsonify({"balance": new_bal})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/api/transfer", methods=["POST"])
def api_transfer():
    try:
        data = request.form.to_dict() or request.get_json(force=False) or {}
        from_id = int(data.get("from_id") or 0)
        to_id = int(data.get("to_id") or 0)
        amount = float(data.get("amount") or 0)
        pin = data.get("pin") or ""
        if from_id <= 0 or to_id <= 0 or amount <= 0 or not pin:
            return jsonify({"error": "from_id, to_id, amount and pin required"}), 400
        acc = models.get_account(from_id)
        if not acc:
            return jsonify({"error": "source account not found"}), 404
        if not verify_pin(pin, acc["pin_hash"]):
            models.register_failed_attempt(from_id)
            return jsonify({"error": "invalid pin"}), 403
        models.reset_failed_attempts(from_id)
        new_from, new_to = models.transfer(from_id, to_id, amount)
        return jsonify({"from_balance": new_from, "to_balance": new_to})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/api/transactions/<int:account_id>", methods=["GET"])
def api_transactions(account_id: int):
    try:
        limit = int(request.args.get("limit") or 200)
        txs = models.get_transactions(account_id, limit=limit)
        return jsonify(txs)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/api/account/<int:account_id>", methods=["GET"])
def api_get_account(account_id: int):
    try:
        acc = models.get_account(account_id)
        if not acc:
            return jsonify({"error": "account not found"}), 404
        acc_safe = {k: v for k, v in acc.items() if k != "pin_hash"}
        return jsonify(acc_safe)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/api/account/<int:account_id>/change-pin", methods=["POST"])
def api_change_pin(account_id: int):
    """Self-service PIN change for a regular user (uses models.update_pin,
    which previously existed but was never wired up to any route)."""
    try:
        data = request.get_json(force=True) or {}
        old_pin = data.get("old_pin") or ""
        new_pin = data.get("new_pin") or ""
        acc = models.get_account(account_id)
        if not acc:
            return jsonify({"error": "account not found"}), 404
        if not verify_pin(old_pin, acc["pin_hash"]):
            return jsonify({"error": "invalid current pin"}), 403
        models.update_pin(account_id, new_pin)
        return jsonify({"status": "PIN updated successfully"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True)
    pin = data.get("pin", "")

    if not require_admin(pin):
        return jsonify({"error": "Invalid admin PIN"}), 403

    return jsonify({"status": "success"})


@app.route("/api/admin/change-pin", methods=["POST"])
def admin_change_pin():
    data = request.get_json(force=True)
    old_pin = data.get("old_pin")
    new_pin = data.get("new_pin")

    acc = models.get_account_by_email("admin@bank.local")

    if not acc or not verify_pin(old_pin, acc["pin_hash"]):
        return jsonify({"error": "Invalid old PIN"}), 403

    if not new_pin.isdigit() or not (4 <= len(new_pin) <= 6):
        return jsonify({"error": "PIN must be 4–6 digits"}), 400

    with models.get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE accounts SET pin_hash=? WHERE account_id=?",
            (hash_pin(new_pin), acc["account_id"])
        )
        conn.commit()

    return jsonify({"status": "PIN updated successfully"})


@app.route("/api/admin/bank-balance", methods=["POST"])
def admin_bank_balance():
    data = request.get_json(force=True)
    pin = data.get("pin", "")

    if not require_admin(pin):
        return jsonify({"error": "Unauthorized"}), 403

    with models.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM system_funds WHERE id=1")
        bal = cur.fetchone()["balance"]

    return jsonify({"bank_balance": bal})


@app.route("/api/admin/stats", methods=["POST"])
def admin_stats():
    data = request.get_json(force=True)
    pin = data.get("pin", "")

    if not require_admin(pin):
        return jsonify({"error": "Unauthorized"}), 403

    with models.get_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS total_users FROM accounts WHERE role='USER'")
        users = cur.fetchone()["total_users"]

        cur.execute("SELECT SUM(amount) AS total_deposits FROM transactions WHERE type='Deposit'")
        deposits = cur.fetchone()["total_deposits"] or 0

        cur.execute("SELECT SUM(amount) AS total_withdrawals FROM transactions WHERE type='Withdraw'")
        withdrawals = cur.fetchone()["total_withdrawals"] or 0

    return jsonify({
        "total_users": users,
        "total_deposits": deposits,
        "total_withdrawals": withdrawals
    })


@app.route("/api/admin/users", methods=["POST"])
def admin_users():
    data = request.get_json(force=True)
    pin = data.get("pin", "")

    if not require_admin(pin):
        return jsonify({"error": "Unauthorized"}), 403

    with models.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                account_id,
                name,
                email,
                phone,
                balance,
                is_locked
            FROM accounts
            WHERE role='USER'
            ORDER BY account_id
        """)
        rows = cur.fetchall()

    users = []
    for r in rows:
        users.append({
            "account_id": r["account_id"],
            "name": r["name"],
            "email": r["email"],
            "phone": r["phone"],
            "balance": r["balance"],
            "status": "Locked" if r["is_locked"] else "Active"
        })

    return jsonify(users)


@app.route("/api/admin/transactions", methods=["POST"])
def admin_all_transactions():
    data = request.get_json(force=True)
    pin = data.get("pin", "")

    if not require_admin(pin):
        return jsonify({"error": "Unauthorized"}), 403

    with models.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                t.tx_id AS id,
                t.account_id,
                a.name,
                t.type,
                t.amount,
                t.balance_after,
                t.note,
                t.created_at
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.role='USER'
            ORDER BY t.created_at DESC
        """)
        rows = cur.fetchall()

    return jsonify([dict(r) for r in rows])


@app.route("/api/admin/toggle-lock", methods=["POST"])
def admin_toggle_lock():
    data = request.get_json(force=True)
    pin = data.get("pin", "")
    account_id = data.get("account_id")

    if not require_admin(pin):
        return jsonify({"error": "Unauthorized"}), 403

    if not account_id:
        return jsonify({"error": "Account ID required"}), 400

    with models.get_conn(True) as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT is_locked FROM accounts WHERE account_id=? AND role='USER'",
            (account_id,)
        )
        row = cur.fetchone()

        if not row:
            return jsonify({"error": "User not found"}), 404

        new_status = 0 if row["is_locked"] else 1

        cur.execute(
            "UPDATE accounts SET is_locked=? WHERE account_id=?",
            (new_status, account_id)
        )
        if new_status == 0:
            cur.execute(
                "UPDATE accounts SET failed_attempts=0 WHERE account_id=?",
                (account_id,)
            )

        conn.commit()

    return jsonify({
        "account_id": account_id,
        "status": "Locked" if new_status else "Active"
    })


@app.route("/api/admin/delete-account", methods=["POST"])
def admin_delete_account():
    """Wires up models.delete_account, which previously existed with no route."""
    data = request.get_json(force=True)
    pin = data.get("pin", "")
    account_id = data.get("account_id")

    if not require_admin(pin):
        return jsonify({"error": "Unauthorized"}), 403
    if not account_id:
        return jsonify({"error": "Account ID required"}), 400

    acc = models.get_account(account_id)
    if not acc:
        return jsonify({"error": "User not found"}), 404

    models.delete_account(account_id)
    return jsonify({"status": "deleted", "account_id": account_id})


# --------------------------------------------------------------------
ensure_db_initialized()
try:
    models.ensure_admin_account()
except Exception:
    print("Could not ensure admin account (continuing):", file=sys.stderr)
    traceback.print_exc()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
