"""
Dev utility: wipes and recreates the local database from schema.
Run from the repo root: python tools/reset_db.py
"""
import sys
from pathlib import Path

# Make the repo root importable (this script lives in tools/, one level
# below the root) so `backend.app.core.db` resolves correctly.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.db import initialize_db, DB_FILE  # noqa: E402

# The original script pointed at a "DATABASE" folder (wrong case — the real
# folder is lowercase "database") and imported `db` directly instead of
# `backend.app.core.db`, so it would fail before ever touching the database.
SQL_FILE = REPO_ROOT / "database" / "init_db.sql"

# Remove old database if it exists
if DB_FILE.exists():
    DB_FILE.unlink()
    print(f"Removed old database at {DB_FILE}")

# Recreate database from schema
initialize_db(str(SQL_FILE))

print("✅ Database recreated successfully!")
