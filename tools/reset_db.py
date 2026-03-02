from pathlib import Path
from db import initialize_db, DB_FILE

# Absolute path to init_db.sql
SQL_FILE = Path(__file__).resolve().parents[2] / "DATABASE" / "init_db.sql"

# Remove old database if it exists
if DB_FILE.exists():
    DB_FILE.unlink()

# Recreate database from schema
initialize_db(SQL_FILE)

print("✅ Database recreated successfully!")
