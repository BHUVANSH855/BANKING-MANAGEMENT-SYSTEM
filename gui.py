import os
print(">>> Loaded gui.py FROM:", os.path.abspath(__file__))
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import models
import datetime
from utils import verify_pin
from live_pincode_lookup import lookup_pin

# ---------- Supported image formats ----------
SUPPORTED_IMAGE_EXTS = (
    ".jpg", ".jpeg", ".png", ".bmp",
    ".tiff", ".webp", ".gif", ".ico"
)

# ---------- Helper conversion ----------
def to_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default

def to_float(val, default=0.0):
    try:
        return float(val)
    except Exception:
        return default


# ---------- Main GUI ----------
class BankGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        # Create all variables BEFORE validation is assigned
        self.full_name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.pin_var = tk.StringVar()
        self.confirm_pin_var = tk.StringVar()
        self.initial_deposit_var = tk.StringVar()
        self.account_type_var = tk.StringVar()
        self.dob_var = tk.StringVar()
        self.dob_entry_widget = None
        self.age_label_var = tk.StringVar()
        self.gender_var = tk.StringVar()
        self.id_type_var = tk.StringVar()
        self.id_doc_path_var = tk.StringVar()
        self.photo_path_var = tk.StringVar()
        self.alt_phone_var = tk.StringVar()
        self.addr_line1_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.district_var = tk.StringVar()
        self.state_var = tk.StringVar()
        self.village_var = tk.StringVar()
        self.tehsil_var = tk.StringVar()
        self.postal_code_var = tk.StringVar()
        self.num_validate = (self.register(self.only_numbers), "%P")
        self.phone_validate = (self.register(self.only_10_digits), "%P")
        self.field_widgets = {}
        # -------- View Account State --------
        self.current_account = None
        self.view_tab_buttons = {}
        self.view_tab_content = None
        self.active_view_tab = None

        self.title("🏦 Banking Management System")
        self.minsize(950, 650)
        self.configure(bg="#f0f2f5")

        # --- Gradient Background ---
        self.bg_canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        def draw_gradient():
            self.bg_canvas.delete("grad")
            height = self.winfo_height()
            width = self.winfo_width()
            for i in range(height):
                # Color transition from light blue → white
                r1, g1, b1 = 230, 242, 255   # light blue
                r2, g2, b2 = 255, 255, 255   # white

                r = int(r1 + (r2 - r1) * (i / height))
                g = int(g1 + (g2 - g1) * (i / height))
                b = int(b1 + (b2 - b1) * (i / height))

                color = f"#{r:02x}{g:02x}{b:02x}"
                self.bg_canvas.create_line(0, i, width, i, fill=color, tags="grad")

            self.bg_canvas.tag_lower("grad")

        self.after(50, draw_gradient)
        self.bind("<Configure>", lambda e: draw_gradient())

        # --- Set icon ---
        icon_path = Path(__file__).resolve().parent / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                try:
                    img = tk.PhotoImage(file=str(icon_path))
                    self.iconphoto(False, img)
                except Exception:
                    pass

        # --- Center window ---
        self.update_idletasks()
        w, h = 1000, 700
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # --- ttk styling ---
        style = ttk.Style(self)
        preferred = ("vista", "xpnative", "clam")
        for t in preferred:
            try:
                style.theme_use(t)
                break
            except Exception:
                continue

        style.configure("TLabel", background="#f4f6fa", font=("Segoe UI", 10))
        style.configure("Heading.TLabel", background="#f4f6fa", font=("Segoe UI", 14, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"),
                        background="#2b7cff", foreground="white", padding=6)
        style.map("Primary.TButton",
                  background=[('active', '#1a5fd8'), ('!active', '#2b7cff')],
                  foreground=[('active', 'white')])

        # --- Layout frames ---
        header = ttk.Label(self, text="🏦 Banking Management System", style="Heading.TLabel")
        header.pack(fill="x", padx=20, pady=(15, 10))

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # Left menu
        menu = ttk.Frame(container)
        menu.pack(side="left", fill="y", padx=(0, 10))

        # Right content
        self.content = ttk.Frame(container)
        self.content.pack(side="right", fill="both", expand=True)

        # Menu buttons
        buttons = [
            ("Create Account", self.show_create),
            ("View Account", self.show_view),
            ("Deposit", self.show_deposit),
            ("Withdraw", self.show_withdraw),
            ("Transfer", self.show_transfer),
            ("Transactions", self.show_transactions),
            ("Delete Account", self.show_delete)
        ]
        for text, cmd in buttons:
            ttk.Button(menu, text=text, style="Primary.TButton", command=cmd).pack(fill="x", pady=5)

        # Default view
        self.show_create()


    # ---------- Utility ----------
    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()


    # ---------- Create Account ----------
    def show_create(self):
        self.clear_content()
        ttk.Label(self.content, text="Create New Account", style="Heading.TLabel").pack(anchor="w", pady=5)
        frame = ttk.Frame(self.content)
        frame.pack(anchor="nw", pady=10)

        labels = ["Full Name", "Email", "Phone", "PIN (4–6 digits)", "Initial Deposit"]
        entries = {}
        for i, lbl in enumerate(labels):
            ttk.Label(frame, text=lbl).grid(row=i, column=0, sticky="w", pady=4)
            ent = ttk.Entry(frame, width=35, show="*" if "PIN" in lbl else "")
            ent.grid(row=i, column=1, padx=10)
            entries[lbl] = ent

        def submit():
            name = entries["Full Name"].get().strip()
            pin = entries["PIN (4–6 digits)"].get().strip()
            if not name or not pin:
                return messagebox.showerror("Error", "Name and PIN required")
            if not pin.isdigit() or not (4 <= len(pin) <= 6):
                return messagebox.showerror("Error", "PIN must be 4–6 digits")
            try:
                acc_id = models.create_account(
                    name,
                    entries["Email"].get().strip() or None,
                    entries["Phone"].get().strip() or None,
                    pin,
                    to_float(entries["Initial Deposit"].get(), 0.0)
                )
                messagebox.showinfo("Success", f"Account created! ID: {acc_id}")
                for e in entries.values():
                    e.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(self.content, text="Create Account", style="Primary.TButton", command=submit).pack(anchor="e", pady=10)


    # ---------- View Account ----------
    def show_view(self):
        self.clear_content()
        ttk.Label(self.content, text="View Account Details", style="Heading.TLabel").pack(anchor="w", pady=5)
        frame = ttk.Frame(self.content)
        frame.pack(anchor="nw", pady=10)

        ttk.Label(frame, text="Account ID").grid(row=0, column=0, sticky="w")
        acc_entry = ttk.Entry(frame, width=10)
        acc_entry.grid(row=0, column=1, padx=8)
        output = tk.Text(self.content, height=10, width=80)
        output.pack(pady=10)

        def view():
            aid = to_int(acc_entry.get())
            acc = models.get_account(aid)
            if not acc:
                return messagebox.showerror("Error", "Account not found")
            output.delete("1.0", tk.END)
            info = (
                f"Account ID: {acc['account_id']}\n"
                f"Name: {acc['name']}\nEmail: {acc['email']}\n"
                f"Phone: {acc['phone']}\nBalance: {acc['balance']}\n"
                f"Created: {acc['created_at']}"
            )
            output.insert(tk.END, info)

        ttk.Button(frame, text="Load", style="Primary.TButton", command=view).grid(row=0, column=2, padx=6)


    # ---------- Deposit ----------
    def show_deposit(self):
        self.clear_content()
        ttk.Label(self.content, text="Deposit Amount", style="Heading.TLabel").pack(anchor="w", pady=5)
        frame = ttk.Frame(self.content)
        frame.pack(anchor="nw", pady=10)
        ttk.Label(frame, text="Account ID").grid(row=0, column=0)
        aid = ttk.Entry(frame, width=10)
        aid.grid(row=0, column=1, padx=8)
        ttk.Label(frame, text="Amount").grid(row=1, column=0)
        amt = ttk.Entry(frame, width=10)
        amt.grid(row=1, column=1, padx=8)

        def deposit():
            a, m = to_int(aid.get()), to_float(amt.get())
            if a <= 0 or m <= 0:
                return messagebox.showerror("Error", "Valid account and amount required")
            try:
                new = models.deposit(a, m)
                messagebox.showinfo("Success", f"Deposited! New balance: {new}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(frame, text="Deposit", style="Primary.TButton", command=deposit).grid(row=2, column=1, pady=8, sticky="e")


    # ---------- Withdraw ----------
    def show_withdraw(self):
        self.clear_content()
        ttk.Label(self.content, text="Withdraw Amount", style="Heading.TLabel").pack(anchor="w", pady=5)
        frame = ttk.Frame(self.content)
        frame.pack(anchor="nw", pady=10)
        ttk.Label(frame, text="Account ID").grid(row=0, column=0)
        aid = ttk.Entry(frame, width=10)
        aid.grid(row=0, column=1, padx=8)
        ttk.Label(frame, text="Amount").grid(row=1, column=0)
        amt = ttk.Entry(frame, width=10)
        amt.grid(row=1, column=1, padx=8)
        ttk.Label(frame, text="PIN").grid(row=2, column=0)
        pin = ttk.Entry(frame, width=10, show="*")
        pin.grid(row=2, column=1, padx=8)

        def withdraw():
            a, m, p = to_int(aid.get()), to_float(amt.get()), pin.get().strip()
            if a <= 0 or m <= 0 or not p:
                return messagebox.showerror("Error", "All fields required")
            acc = models.get_account(a)
            if not acc:
                return messagebox.showerror("Error", "Account not found")
            if not verify_pin(p, acc["pin_hash"]):
                return messagebox.showerror("Error", "Invalid PIN")
            try:
                new = models.withdraw(a, m)
                messagebox.showinfo("Success", f"Withdrawn. New balance: {new}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(frame, text="Withdraw", style="Primary.TButton", command=withdraw).grid(row=3, column=1, pady=8, sticky="e")


    # ---------- Transfer ----------
    def show_transfer(self):
        self.clear_content()
        ttk.Label(self.content, text="Transfer Funds", style="Heading.TLabel").pack(anchor="w", pady=5)
        frame = ttk.Frame(self.content)
        frame.pack(anchor="nw", pady=10)
        labels = ["From Account ID", "To Account ID", "Amount", "PIN"]
        entries = {}
        for i, lbl in enumerate(labels):
            ttk.Label(frame, text=lbl).grid(row=i, column=0, sticky="w", pady=3)
            e = ttk.Entry(frame, width=12, show="*" if "PIN" in lbl else "")
            e.grid(row=i, column=1, padx=8)
            entries[lbl] = e

        def transfer():
            f, t, a, p = (to_int(entries["From Account ID"].get()),
                          to_int(entries["To Account ID"].get()),
                          to_float(entries["Amount"].get()),
                          entries["PIN"].get().strip())
            if f <= 0 or t <= 0 or a <= 0 or not p:
                return messagebox.showerror("Error", "All fields required")
            acc = models.get_account(f)
            if not acc:
                return messagebox.showerror("Error", "Source account not found")
            if not verify_pin(p, acc["pin_hash"]):
                return messagebox.showerror("Error", "Invalid PIN")
            try:
                new_f, new_t = models.transfer(f, t, a)
                messagebox.showinfo("Success", f"Transferred! New balances:\nFrom: {new_f}\nTo: {new_t}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(self.content, text="Transfer", style="Primary.TButton", command=transfer).pack(anchor="e", pady=10)


    # ---------- Transactions ----------
    def show_transactions(self):
        self.clear_content()
        ttk.Label(self.content, text="Transaction History", style="Heading.TLabel").pack(anchor="w", pady=5)
        frame = ttk.Frame(self.content)
        frame.pack(anchor="nw", pady=10)
        ttk.Label(frame, text="Account ID").grid(row=0, column=0)
        aid = ttk.Entry(frame, width=10)
        aid.grid(row=0, column=1, padx=8)
        ttk.Button(frame, text="Load", style="Primary.TButton", command=lambda: self.load_tx(aid.get())).grid(row=0, column=2)

        cols = ("created_at", "type", "amount", "balance_after", "note")
        self.tree = ttk.Treeview(self.content, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, anchor="w", width=140 if c == "note" else 120)
        self.tree.pack(fill="both", expand=True, pady=8)

    def load_tx(self, aid_str):
        aid = to_int(aid_str)
        if aid <= 0:
            return messagebox.showerror("Error", "Enter valid account ID")
        try:
            txs = models.get_transactions(aid, limit=100)
            for r in self.tree.get_children():
                self.tree.delete(r)
            for t in txs:
                self.tree.insert("", tk.END, values=(t["created_at"], t["type"], t["amount"], t["balance_after"], t.get("note", "")))
        except Exception as e:
            messagebox.showerror("Error", str(e))


    # ---------- Delete Account ----------
    def show_delete(self):
        self.clear_content()
        ttk.Label(self.content, text="Delete Account", style="Heading.TLabel").pack(anchor="w", pady=5)
        frame = ttk.Frame(self.content)
        frame.pack(anchor="nw", pady=10)
        ttk.Label(frame, text="Account ID").grid(row=0, column=0)
        aid = ttk.Entry(frame, width=10)
        aid.grid(row=0, column=1, padx=8)
        ttk.Label(frame, text="PIN").grid(row=1, column=0)
        pin = ttk.Entry(frame, width=10, show="*")
        pin.grid(row=1, column=1, padx=8)

        def delete():
            a, p = to_int(aid.get()), pin.get().strip()
            if a <= 0 or not p:
                return messagebox.showerror("Error", "Account ID and PIN required")
            acc = models.get_account(a)
            if not acc:
                return messagebox.showerror("Error", "Account not found")
            if not verify_pin(p, acc["pin_hash"]):
                return messagebox.showerror("Error", "Invalid PIN")
            if messagebox.askyesno("Confirm", "Are you sure you want to delete this account?"):
                models.delete_account(a)
                messagebox.showinfo("Deleted", "Account deleted successfully!")

        ttk.Button(frame, text="Delete", style="Primary.TButton", command=delete).grid(row=2, column=1, pady=8, sticky="e")


# ---------- Run GUI ----------
if __name__ == "__main__":
    app = BankGUI()
    app.mainloop()


