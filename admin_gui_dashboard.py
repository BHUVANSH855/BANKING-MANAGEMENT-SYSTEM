import tkinter as tk
from tkinter import ttk, messagebox
import requests

API_BASE = "http://127.0.0.1:5000"

class AdminDashboard(tk.Tk):
    def __init__(self, pin):
        super().__init__()
        self.pin = pin

        self.title("🏦 Bank Admin Dashboard")
        self.geometry("720x420")
        self.configure(bg="#f1f5f9")

        # -------- Header --------
        header = tk.Label(
            self,
            text="🏦 Bank Admin Dashboard",
            font=("Segoe UI", 20, "bold"),
            bg="#1e3a8a",
            fg="white",
            pady=15
        )
        header.pack(fill="x")

        # -------- Cards Container --------
        cards = tk.Frame(self, bg="#f1f5f9")
        cards.pack(padx=30, pady=30, fill="x")

        self.bank_lbl = self.make_card(cards, "🏦 Bank Balance", "₹ --")
        self.users_lbl = self.make_card(cards, "👥 Total Users", "--")
        self.dep_lbl = self.make_card(cards, "📥 Total Deposits", "₹ --")
        self.wd_lbl = self.make_card(cards, "📤 Total Withdrawals", "₹ --")

        self.refresh_data()

        btn_frame = tk.Frame(self, bg="#f1f5f9")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="👥 View All Users",
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="white",
            padx=20,
            pady=8,
            command=self.open_users_window
        ).pack()

        tk.Button(
            btn_frame,
            text="📜 View Transactions",
            font=("Segoe UI", 11, "bold"),
            bg="#0f766e",
            fg="white",
            padx=20,
            pady=8,
            command=self.open_transactions_window
        ).pack(pady=5)

        tk.Button(
            btn_frame,
            text="🔑 Change Admin PIN",
            font=("Segoe UI", 11, "bold"),
            bg="#7c2d12",
            fg="white",
            padx=20,
            pady=8,
            command=self.open_change_pin
        ).pack(pady=5)


    def open_transactions_window(self):
        win = tk.Toplevel(self)
        win.title("📜 Bank Transaction Ledger")
        win.geometry("1050x500")
        win.configure(bg="white")

        tk.Label(
            win,
            text="📜 All Bank Transactions",
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(anchor="w", padx=20, pady=10)

        cols = (
            "ID", "Account ID", "Name", "Type",
            "Amount", "Balance After", "Note", "Date"
        )

        tree = ttk.Treeview(win, columns=cols, show="headings", height=14)

        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center", width=120)

        tree.pack(fill="both", expand=True, padx=20, pady=10)

        res = requests.post(
            f"{API_BASE}/api/admin/transactions",
            json={"pin": self.pin},
            timeout=5
        )

        if res.status_code != 200:
            messagebox.showerror(
                "Error",
                f"Failed to load transactions.\nServer returned {res.status_code}"
            )
            return

        try:
            data = res.json()
        except Exception:
            messagebox.showerror(
                "Error",
                "Server returned invalid response.\nCheck Flask console."
            )
            print("Raw response:", res.text)
            return

        if not data:
            messagebox.showinfo("Info", "No transactions found.")
            return

        for t in data:
            tree.insert("", "end", (
                t["id"],
                t["account_id"],
                t["name"],
                t["type"],
                f"₹ {t['amount']}",
                f"₹ {t['balance_after']}",
                t["note"],
                t["created_at"]
            ))

    def make_card(self, parent, title, value):
        card = tk.Frame(parent, bg="white", bd=1, relief="solid", width=150, height=120)
        card.pack(side="left", padx=15)
        card.pack_propagate(False)

        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(pady=(15, 5))

        val_lbl = tk.Label(
            card,
            text=value,
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="#1e3a8a"
        )
        val_lbl.pack()

        return val_lbl
    
    def open_change_pin(self):
        win = tk.Toplevel(self)
        win.title("🔑 Change Admin PIN")
        win.geometry("350x300")
        win.configure(bg="white")

        tk.Label(win, text="Old PIN", bg="white").pack(pady=5)
        old_pin = tk.Entry(win, show="*", width=20)
        old_pin.pack()

        tk.Label(win, text="New PIN", bg="white").pack(pady=5)
        new_pin = tk.Entry(win, show="*", width=20)
        new_pin.pack()

        def submit():
            res = requests.post(
                f"{API_BASE}/api/admin/change-pin",
                json={
                    "old_pin": old_pin.get(),
                    "new_pin": new_pin.get()
                }
            )

            if res.status_code == 200:
                messagebox.showinfo("Success", "Admin PIN changed successfully")
                self.pin = new_pin.get()   # update session PIN
                win.destroy()
            else:
                messagebox.showerror("Error", res.json().get("error", "Failed"))

        tk.Button(
            win,
            text="Update PIN",
            bg="#2563eb",
            fg="white",
            command=submit
        ).pack(pady=20)


    def refresh_data(self):
        try:
            # --- Bank Balance ---
            res_bal = requests.post(
                f"{API_BASE}/api/admin/bank-balance",
                json={"pin": self.pin},
                timeout=5
            )
            data_bal = res_bal.json()

            if "bank_balance" not in data_bal:
                raise ValueError(data_bal.get("error", "Auth failed"))

            # --- Stats ---
            res_stats = requests.post(
                f"{API_BASE}/api/admin/stats",
                json={"pin": self.pin},
                timeout=5
            )
            data_stats = res_stats.json()

            if "total_users" not in data_stats:
                raise ValueError(data_stats.get("error", "Auth failed"))

            # --- Update UI ---
            self.bank_lbl.config(text=f"₹ {data_bal['bank_balance']}")
            self.users_lbl.config(text=str(data_stats["total_users"]))
            self.dep_lbl.config(text=f"₹ {data_stats['total_deposits']}")
            self.wd_lbl.config(text=f"₹ {data_stats['total_withdrawals']}")

        except Exception as e:
            print("Admin dashboard error:", e)
            self.bank_lbl.config(text="Error")
            self.users_lbl.config(text="--")
            self.dep_lbl.config(text="₹ --")
            self.wd_lbl.config(text="₹ --")

    def open_users_window(self):
        win = tk.Toplevel(self)
        win.title("👥 All Bank Users")
        win.geometry("950x450")
        win.configure(bg="white")

        tk.Label(
            win,
            text="👥 Registered Users",
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(anchor="w", padx=20, pady=10)

        cols = ("ID", "Name", "Email", "Phone", "Balance", "Status", "Action")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=12)

        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center", width=120)

        tree.pack(fill="both", expand=True, padx=20, pady=10)

        def load_users():
            tree.delete(*tree.get_children())
            res = requests.post(
                f"{API_BASE}/api/admin/users",
                json={"pin": self.pin}
            )
            users = res.json()

            for u in users:
                action = "Unlock" if u["status"] == "Locked" else "Lock"
                tree.insert("", "end", values=(
                    u["account_id"],
                    u["name"],
                    u["email"],
                    u["phone"],
                    f"₹ {u['balance']}",
                    u["status"],
                    action
                ))

        def toggle_lock():
            sel = tree.focus()
            if not sel:
                return

            vals = tree.item(sel, "values")
            acc_id = vals[0]

            res = requests.post(
                f"{API_BASE}/api/admin/toggle-lock",
                json={
                    "pin": self.pin,
                    "account_id": acc_id
                }
            )

            if res.status_code == 200:
                load_users()

        btn = tk.Button(
            win,
            text="🔒 Lock / Unlock Selected User",
            font=("Segoe UI", 11, "bold"),
            bg="#dc2626",
            fg="white",
            padx=20,
            pady=8,
            command=toggle_lock
        )
        btn.pack(pady=10)

        load_users()


