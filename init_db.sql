PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Basic info
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    dob TEXT,
    gender TEXT,
    id_type TEXT,
    id_document_path TEXT,
    photo_path TEXT,
    addr_line1 TEXT,
    village TEXT,
    tehsil TEXT,
    district TEXT,
    state TEXT,
    postal_code TEXT,
    account_type TEXT,
    initial_deposit REAL,
    balance REAL NOT NULL DEFAULT 0.0,
    pin_hash TEXT NOT NULL,
    role TEXT DEFAULT 'USER',        -- USER / ADMIN
    failed_attempts INTEGER DEFAULT 0,
    is_locked INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);


CREATE TABLE IF NOT EXISTS transactions (
    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    type TEXT NOT NULL, -- Deposit, Withdraw, Transfer-Out, Transfer-In
    amount REAL NOT NULL,
    balance_after REAL NOT NULL,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id);

-- Central Bank System Wallet
CREATE TABLE IF NOT EXISTS system_funds (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    balance REAL NOT NULL
);

INSERT OR IGNORE INTO system_funds (id, balance)
VALUES (1, 0.0);
