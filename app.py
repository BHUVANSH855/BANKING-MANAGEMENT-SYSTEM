# File: app.py
"""
Debug-friendly Flask backend for Banking Management System.

Replace your existing app.py with this file while debugging frontend 404 issues.
It prints directory info and the frontend folder contents at startup,
logs every request path, and checks file existence before serving.
"""
import traceback
import sys
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

def require_admin(pin):
    acc = models.get_account_by_email("admin@bank.local")
    if not acc or acc.get("role") != "ADMIN":
        return False
    return verify_pin(pin, acc["pin_hash"])

# Try to import project modules (models/db/utils)
try:
    import models
    from db import initialize_db
    from utils import verify_pin, hash_pin
except Exception as e:
    print("Error importing project modules (models/db/utils). Make sure these files are in the same folder as app.py.", file=sys.stderr)
    traceback.print_exc()
    # We continue because for debugging static files we don't need models to be present necessarily.

# Setup
PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DB_FILE = PROJECT_ROOT / "banking.db"
INIT_SQL = PROJECT_ROOT / "init_db.sql"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/")
CORS(app)

def ensure_db_initialized():
    """Initialize DB if missing (safe no-op if db exists)."""
    try:
        if not DB_FILE.exists():
            print("banking.db not found → initializing DB")
            if INIT_SQL.exists():
                initialize_db(str(INIT_SQL))
            else:
                initialize_db()
            print("Database initialized.")
    except Exception:
        print("DB initialization failed (continuing):")
        traceback.print_exc()

# Startup diagnostics
def print_startup_info():
    print("=== Startup diagnostics ===")
    print("Current working directory:", Path.cwd())
    print("Project root:", PROJECT_ROOT)
    print("Frontend folder expected at:", FRONTEND_DIR)
    if FRONTEND_DIR.exists() and FRONTEND_DIR.is_dir():
        print("Frontend folder exists. Listing contents:")
        for p in sorted(FRONTEND_DIR.iterdir()):
            print("  -", p.name, "(dir)" if p.is_dir() else "(file)")
    else:
        print("Frontend folder DOES NOT exist! (This is the likely cause of 404)")
    print("banking.db exists?:", DB_FILE.exists())
    print("===========================")

# Simple request logging (for debug)
@app.before_request
def log_request():
    print(f"[REQ] {request.method} {request.path}")

# Index route - serve index.html (only if file exists)
@app.route("/", methods=["GET"])
def index():
    index_path = FRONTEND_DIR / "index.html"
    print("Serving root / -> checking for:", index_path)
    if index_path.exists():
        return send_from_directory(str(FRONTEND_DIR), "index.html")
    else:
        # Helpful error message for debugging in browser
        return (
            "<h2>Index not found</h2>"
            f"<p>Expected file: {index_path}</p>"
            f"<p>Project root: {PROJECT_ROOT}</p>"
            "<p>Make sure the folder 'frontend' (containing index.html) is in the same folder as app.py</p>"
        ), 404

# Generic static file handler (serves css/js/pages if present)
@app.route("/<path:filename>", methods=["GET"])
def static_files(filename):
    file_path = FRONTEND_DIR / filename
    print("Static request for:", filename, "-> exists?", file_path.exists())
    if file_path.exists():
        return send_from_directory(str(FRONTEND_DIR), filename)
    # If file not found in frontend, return helpful 404
    return (
        "<h2>Static file not found</h2>"
        f"<p>Requested: {filename}</p>"
        f"<p>Looked in: {file_path}</p>"
    ), 404

# ------------------- API endpoints (same as before) -------------------
# Note: these use the models functions. If models import failed, these endpoints may error.
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
            return jsonify({"error": "invalid pin"}), 403
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
            return jsonify({"error": "invalid pin"}), 403
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
                t.id,
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
        conn.commit()
    return jsonify({
        "account_id": account_id,
        "status": "Locked" if new_status else "Active"
    })

# --------------------------------------------------------------------
if __name__ == "__main__":
    ensure_db_initialized()
    models.ensure_admin_account()
    print_startup_info()
    print("URL map (routes):")
    print(app.url_map)
    # Start server
    app.run(host="127.0.0.1", port=5000, debug=True)
