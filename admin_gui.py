import tkinter as tk
from tkinter import messagebox
import requests

API_BASE = "http://127.0.0.1:5000"

class AdminLogin(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("🏦 Bank Admin Login")
        self.geometry("360x260")
        self.resizable(False, False)
        self.configure(bg="#f8fafc")

        # -------- Header --------
        header = tk.Label(
            self,
            text="🏦 Admin Panel",
            font=("Segoe UI", 18, "bold"),
            bg="#1e3a8a",
            fg="white",
            pady=15
        )
        header.pack(fill="x")

        # -------- Card --------
        card = tk.Frame(self, bg="white", bd=1, relief="solid")
        card.pack(padx=30, pady=25, fill="both", expand=True)

        tk.Label(
            card,
            text="Admin PIN",
            font=("Segoe UI", 11),
            bg="white"
        ).pack(anchor="w", padx=15, pady=(20, 5))

        self.pin_entry = tk.Entry(
            card,
            show="*",
            font=("Segoe UI", 12),
            width=20
        )
        self.pin_entry.pack(padx=15)


        self.error_lbl = tk.Label(
            card,
            text="",
            fg="red",
            bg="white",
            font=("Segoe UI", 9)
        )
        self.error_lbl.pack(pady=(5, 0))

        login_btn = tk.Button(
            card,
            text="🔐 Login",
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="white",
            padx=20,
            pady=8,
            command=self.login
        )
        login_btn.pack(pady=25)
        self.pin_entry.bind("<Return>", lambda e: self.login())

    def login(self):
        pin = self.pin_entry.get().strip()
        self.error_lbl.config(text="")
    
        if not pin:
            self.error_lbl.config(text="PIN required")
            return
    
        try:
            res = requests.post(
                f"{API_BASE}/api/admin/login",
                json={"pin": pin},
                timeout=5
            )
    
            if res.status_code != 200:
                self.error_lbl.config(text="Invalid admin PIN")
                return
    
            print("Admin login successful, opening dashboard...")
            self.destroy()
            from admin_gui_dashboard import AdminDashboard
            AdminDashboard(pin).mainloop()
    
        except Exception:
            messagebox.showerror(
                "Connection Error",
                "Cannot connect to server.\nMake sure app.py is running."
            )
    

if __name__ == "__main__":
    app = AdminLogin()
    app.mainloop()

