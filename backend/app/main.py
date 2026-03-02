# main.py - GUI entry point
from backend.app.gui.gui import LoginGUI
from backend.app.models import models
from backend.app.core.db import initialize_db

if __name__ == "__main__":
    # Step 1: Create tables if not exist
    initialize_db()

    # Step 2: Ensure admin account exists
    models.ensure_admin_account()

    # Step 3: Start GUI
    LoginGUI().mainloop()