# db.py - Database utilities
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Go up from:
# backend/app/core/db.py
# to project root
BASE_DIR = Path(__file__).resolve().parents[3]

DB_FILE = BASE_DIR / "database" / "banking.db"

@contextmanager
def get_conn(autocommit: bool = False):
    """
    Yields a sqlite3.Connection.
    If autocommit=True, commit after leaving context.
    Caller may still call conn.commit() or conn.rollback() as needed.
    """
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        if autocommit:
            conn.commit()
    finally:
        conn.close()

def initialize_db(sql_file: str = None):
    """
    Create tables. If sql_file provided, execute that SQL file; otherwise create inline.
    """
    with get_conn(True) as conn:
        cur = conn.cursor()
        cur.execute('PRAGMA foreign_keys = ON;')
        if sql_file:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            cur.executescript(sql)
        else:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    balance REAL NOT NULL DEFAULT 0.0,
    pin_hash TEXT NOT NULL,
    role TEXT DEFAULT 'USER',
    created_at TEXT DEFAULT (datetime('now'))
)
            ''')
            cur.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL NOT NULL,
                note TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
            )
            ''')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id)')
        conn.commit()