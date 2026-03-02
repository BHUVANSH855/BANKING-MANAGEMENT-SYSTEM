# main.py - GUI entry point
from app.gui.gui import LoginGUI
import models

if __name__ == "__main__":
    # ensure admin exists
    models.ensure_admin_account()
    LoginGUI().mainloop()
