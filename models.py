# models.py - account and transaction operations
from db import get_conn
from utils import hash_pin

# ---------- Account CRUD ----------
def create_account(name, email, phone, pin, initial_deposit=0.0):
    pin_h = hash_pin(pin)
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO accounts (name,email,phone,balance,pin_hash) VALUES (?,?,?,?,?)',
            (name, email, phone, initial_deposit, pin_h)
        )
        account_id = cur.lastrowid
        if initial_deposit > 0:
            cur.execute(
                'INSERT INTO transactions (account_id,type,amount,balance_after,note) VALUES (?,?,?,?,?)',
                (account_id, 'Deposit', initial_deposit, initial_deposit, 'Initial deposit')
            )
        conn.commit()
        return account_id

def get_account(account_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM accounts WHERE account_id=?', (account_id,))
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

def deposit(account_id, amount):
    if amount <= 0:
        raise ValueError('Amount must be positive')
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute('SELECT balance FROM accounts WHERE account_id=?', (account_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError('Account not found')
        new_balance = row['balance'] + amount
        update_balance(account_id, new_balance, cur)
        add_transaction(cur, account_id, 'Deposit', amount, new_balance, 'Deposit')
        conn.commit()
        return new_balance

def withdraw(account_id, amount):
    if amount <= 0:
        raise ValueError('Amount must be positive')
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute('SELECT balance FROM accounts WHERE account_id=?', (account_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError('Account not found')
        if row['balance'] < amount:
            raise ValueError('Insufficient funds')
        new_balance = row['balance'] - amount
        update_balance(account_id, new_balance, cur)
        add_transaction(cur, account_id, 'Withdraw', amount, new_balance, 'Withdrawal')
        conn.commit()
        return new_balance

def transfer(from_acct, to_acct, amount):
    if amount <= 0:
        raise ValueError('Amount must be positive')
    with get_conn(False) as conn:
        cur = conn.cursor()
        try:
            conn.execute('BEGIN')
            cur.execute('SELECT balance FROM accounts WHERE account_id=?', (from_acct,))
            r1 = cur.fetchone()
            cur.execute('SELECT balance FROM accounts WHERE account_id=?', (to_acct,))
            r2 = cur.fetchone()
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
