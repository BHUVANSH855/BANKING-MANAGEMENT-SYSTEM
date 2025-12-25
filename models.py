# models.py - account and transaction operations
from db import get_conn
from utils import hash_pin
import hashlib

# ---------- DEFAULT BANK ADMIN ----------
ADMIN_ID = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()

def verify_admin(admin_id, password):
    if admin_id != ADMIN_ID:
        return False
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed == ADMIN_PASSWORD_HASH

def ensure_admin_account():
    from utils import hash_pin
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM accounts WHERE role='ADMIN'")
        if cur.fetchone():
            return
        cur.execute("""
            INSERT INTO accounts (
                name, email, phone,
                balance, pin_hash, role
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "BANK_ADMIN",
            "admin@bank.local",
            "0000000000",
            0.0,
            hash_pin("123456"),
            "ADMIN"
        ))
        conn.commit()

# ---------- Account CRUD ----------
def create_account(
    name,
    email,
    phone,
    pin,
    initial_deposit,
    dob=None,
    gender=None,
    id_type=None,
    id_document_path=None,
    photo_path=None,
    addr_line1=None,
    village=None,
    tehsil=None,
    district=None,
    state=None,
    postal_code=None,
    account_type=None
):
    from utils import hash_pin
    pin_h = hash_pin(pin)

    with get_conn(True) as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO accounts (
                name, email, phone,
                dob, gender,
                id_type, id_document_path, photo_path,
                addr_line1, village, tehsil, district, state, postal_code,
                account_type, initial_deposit,
                balance, pin_hash
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            name, email, phone,
            dob, gender,
            id_type, id_document_path, photo_path,
            addr_line1, village, tehsil, district, state, postal_code,
            account_type, initial_deposit,
            initial_deposit, pin_h
        ))

        # ✅ account_id is GUARANTEED here
        account_id = cur.lastrowid

        # Initial transaction
        if initial_deposit > 0:
            cur.execute("""
                INSERT INTO transactions
                (account_id, type, amount, balance_after, note)
                VALUES (?,?,?,?,?)
            """, (
                account_id,
                "Deposit",
                initial_deposit,
                initial_deposit,
                "Initial deposit"
            ))
        conn.commit()
        return account_id

def get_account(account_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM accounts WHERE account_id=? AND role='USER'",
            (account_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_account_by_email(email):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM accounts WHERE email=?', (email,))
        row = cur.fetchone()
        return dict(row) if row else None

def update_balance(account_id, new_balance, cur):
    cur.execute('UPDATE accounts SET balance=? WHERE account_id=?', (new_balance, account_id))

# ---------- Transactions ----------
def add_transaction(cur, account_id, type_, amount, balance_after, note=None):
    cur.execute(
        'INSERT INTO transactions (account_id,type,amount,balance_after,note) VALUES (?,?,?,?,?)',
        (account_id, type_, amount, balance_after, note)
    )

def deposit(account_id, amount, note=None):
    if amount <= 0:
        raise ValueError('Amount must be positive')

    with get_conn(True) as conn:
        cur = conn.cursor()

        # Fetch user
        cur.execute(
            "SELECT balance, is_locked FROM accounts WHERE account_id=? AND role='USER'",
            (account_id,)
        )
        
        row = cur.fetchone()
        if not row:
            raise ValueError('Account not found')
        if row["is_locked"]:
            raise ValueError("Account is locked by bank admin")


        # Update bank funds
        cur.execute("UPDATE system_funds SET balance = balance + ?", (amount,))

        # Update user balance
        new_balance = row['balance'] + amount
        update_balance(account_id, new_balance, cur)

        # Log transaction
        add_transaction(
            cur,
            account_id,
            'Deposit',
            amount,
            new_balance,
            note or 'Deposit credited from bank'
        )

        conn.commit()
        return new_balance


def withdraw(account_id, amount, note=None):
    if amount <= 0:
        raise ValueError('Amount must be positive')

    with get_conn(True) as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT balance, is_locked FROM accounts WHERE account_id=? AND role='USER'",
            (account_id,)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError('Account not found')
        if row["is_locked"]:
            raise ValueError("Account is locked by bank admin")


        if row['balance'] < amount:
            raise ValueError('Insufficient funds')

        # Reduce bank funds
        cur.execute("UPDATE system_funds SET balance = balance - ?", (amount,))

        new_balance = row['balance'] - amount
        update_balance(account_id, new_balance, cur)

        add_transaction(
            cur,
            account_id,
            'Withdraw',
            amount,
            new_balance,
            note or 'Withdrawal debited to bank'
        )

        conn.commit()
        return new_balance


def transfer(from_acct, to_acct, amount):
    if amount <= 0:
        raise ValueError('Amount must be positive')
    with get_conn(False) as conn:
        cur = conn.cursor()
        try:
            conn.execute('BEGIN')
            cur.execute(
                "SELECT balance, is_locked FROM accounts WHERE account_id=? AND role='USER'",
                (from_acct,)
            )
            r1 = cur.fetchone()
            if r1["is_locked"]:
                raise ValueError("Source account is locked by bank admin")

            cur.execute(
                "SELECT balance, is_locked FROM accounts WHERE account_id=? AND role='USER'",
                (to_acct,)
            )
            r2 = cur.fetchone()
            if r2["is_locked"]:
                raise ValueError("Destination account is locked by bank admin")

            if not r1 or not r2:
                raise ValueError('One or both accounts not found')
            if r1['balance'] < amount:
                raise ValueError('Insufficient funds in source account')

            new_from = r1['balance'] - amount
            new_to = r2['balance'] + amount
            cur.execute('UPDATE accounts SET balance=? WHERE account_id=?', (new_from, from_acct))
            cur.execute('UPDATE accounts SET balance=? WHERE account_id=?', (new_to, to_acct))
            add_transaction(cur, from_acct, 'Transfer-Out', amount, new_from, f'Transfer to {to_acct}')
            add_transaction(cur, to_acct, 'Transfer-In', amount, new_to, f'Transfer from {from_acct}')
            conn.commit()
            return new_from, new_to
        except Exception:
            conn.rollback()
            raise

def get_transactions(account_id, limit=100):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM transactions WHERE account_id=? ORDER BY created_at DESC LIMIT ?', (account_id, limit))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def delete_account(account_id):
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM accounts WHERE account_id=?', (account_id,))
        conn.commit()

def update_pin(account_id, new_pin):
    if not new_pin.isdigit() or not (4 <= len(new_pin) <= 6):
        raise ValueError("PIN must be 4–6 digits")

    pin_h = hash_pin(new_pin)

    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE accounts SET pin_hash=? WHERE account_id=?",
            (pin_h, account_id)
        )
        conn.commit()

def register_failed_attempt(account_id):
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE accounts SET failed_attempts = failed_attempts + 1 WHERE account_id=?",
            (account_id,)
        )
        cur.execute(
            "UPDATE accounts SET is_locked=1 WHERE account_id=? AND failed_attempts>=3",
            (account_id,)
        )


def reset_failed_attempts(account_id):
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE accounts SET failed_attempts=0 WHERE account_id=?",
            (account_id,)
        )


def lock_account(account_id):
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE accounts SET is_locked=1 WHERE account_id=?",
            (account_id,)
        )
        conn.commit()

def unlock_account(account_id):
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE accounts
            SET is_locked = 0,
                failed_attempts = 0
            WHERE account_id = ?
        """, (account_id,))
        conn.commit()

