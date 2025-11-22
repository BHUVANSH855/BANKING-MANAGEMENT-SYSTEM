# File: ui.py  (debug-ready GUI starter)
"""
Debugging wrapper for the Tkinter GUI.
Saves silent-exit headaches by printing startup/exception messages.
Replace your current ui.py with this and run in a terminal:
    python ui.py
"""
import traceback
import sys
import os

print("Starting ui.py ...")
print("Working directory:", os.getcwd())
print("Python executable:", sys.executable)
print("Python version:", sys.version)

# quick tkinter check
try:
    import tkinter as tk
    from tkinter import messagebox
    print("Imported tkinter OK (Tk version:", tk.TkVersion, ")")
except Exception as e:
    print("Failed to import tkinter:", e, file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

# Try to import your app GUI code (the BankGUI class).
# If your GUI code is in gui.py or ui_original.py, import it; else we include a tiny demo here.
GUI_MODULE_NAME = "gui"  # if you saved the GUI code as gui.py
# If your main GUI class is in a different file, change GUI_MODULE_NAME accordingly.

bank_gui_class = None
try:
    # if you have a separate gui.py with BankGUI class, try importing it
    mod = __import__(GUI_MODULE_NAME)
    bank_gui_class = getattr(mod, "BankGUI", None)
    if bank_gui_class:
        print(f"Found BankGUI class in {GUI_MODULE_NAME}.py")
except Exception as e:
    print(f"Could not import {GUI_MODULE_NAME}.py or it has errors: {e}")
    traceback.print_exc()
    # we'll fall back to a minimal demo window below

# If BankGUI not found, build a minimal test window to ensure tkinter works
if not bank_gui_class:
    print("BankGUI class not found — launching a simple test window as fallback.")
    class TestApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Tkinter Test Window")
            self.geometry("400x200")
            lbl = tk.Label(self, text="Tkinter is working — replace GUI module or fix import.", padx=12, pady=12)
            lbl.pack()
            btn = tk.Button(self, text="Close", command=self.destroy)
            btn.pack(pady=10)
    app = TestApp()
else:
    try:
        app = bank_gui_class()
    except Exception as e:
        print("Error while creating BankGUI instance:", e, file=sys.stderr)
        traceback.print_exc()
        print("Falling back to minimal test window.")
        class TestApp(tk.Tk):
            def __init__(self):
                super().__init__()
                self.title("Tkinter Fallback Window")
                self.geometry("400x200")
                lbl = tk.Label(self, text="Fallback window (BankGUI failed to instantiate).", padx=12, pady=12)
                lbl.pack()
                btn = tk.Button(self, text="Close", command=self.destroy)
                btn.pack(pady=10)
        app = TestApp()

# Final: start mainloop, but wrap in try/except so we can log errors
try:
    print("Starting Tk mainloop. A window should appear now.")
    app.mainloop()
    print("Mainloop exited normally.")
except Exception as e:
    print("Exception occurred during mainloop:", e, file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

print("ui.py finished.")
