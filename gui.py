import os
print(">>> Loaded gui.py FROM:", os.path.abspath(__file__))
import tkinter as tk
from tkinter import ttk, messagebox
import qrcode
from PIL import Image, ImageTk
import webbrowser
from pathlib import Path
import models
import datetime
from utils import verify_pin
from live_pincode_lookup import lookup_pin
import re
import winsound

UPI_REGEX = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")
DAILY_ATM_LIMIT = 25000
BANK_MASTER_UPI = "bank@upi"
RUPEE = "₹"
FREE_ATM_WITHDRAWALS = 3
ATM_CHARGE_AFTER_FREE = 20
DAILY_TRANSFER_LIMIT = 50000
THEMES = {
    "light": {
        "bg": "#f8fafc",
        "card": "#ffffff",
        "sidebar": "#1e293b",
        "sidebar_hover": "#334155",
        "header": "#1e3a8a",
        "text": "#1e293b",
        "muted": "#475569",
        "primary": "#2563eb",
        "success": "#16a34a",
        "danger": "#dc2626",
        "panel": "#eef6ff",
        "icon_panel": "#e0ecff",
    },
    "dark": {
        "bg": "#0f172a",
        "card": "#111827",
        "sidebar": "#020617",
        "sidebar_hover": "#020617",
        "header": "#020617",
        "text": "#e5e7eb",
        "muted": "#9ca3af",
        "primary": "#3b82f6",
        "success": "#22c55e",
        "danger": "#ef4444",
        "panel": "#020617",
        "icon_panel": "#020617",
    }
}

# ---------- Supported image formats ----------
SUPPORTED_IMAGE_EXTS = (
    ".jpg", ".jpeg", ".png", ".bmp",
    ".tiff", ".webp", ".gif", ".ico"
)

def theme_color(self, key):
    return self.theme.get(key, "#ffffff")

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

# ---------- Global Currency Formatter ----------
def format_currency(value):
    """
    Formats number into Indian currency format with ₹
    Example: 1234567 -> ₹12,34,567
    """
    try:
        value = float(str(value).replace(",", ""))
    except:
        return "₹0"

    value = int(value)
    s = str(value)

    if len(s) <= 3:
        return f"₹{s}"

    last3 = s[-3:]
    rest = s[:-3]
    parts = []

    while len(rest) > 2:
        parts.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.append(rest)

    return "₹" + ",".join(reversed(parts)) + "," + last3

#----------- Login UI---------------
class LoginGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("360x260")
        self.resizable(False, False)

        tk.Label(self, text="🏦 Banking Login", font=("Segoe UI", 16, "bold")).pack(pady=20)
        # Login type selection
        self.login_type = tk.StringVar(value="USER")

        type_frame = tk.Frame(self)
        type_frame.pack(pady=5)

        tk.Radiobutton(
            type_frame, text="Login as User",
            variable=self.login_type, value="USER"
        ).pack(side="left", padx=10)

        tk.Radiobutton(
            type_frame, text="Login as Admin",
            variable=self.login_type, value="ADMIN"
        ).pack(side="left", padx=10)

        self.acc_label = tk.Label(self, text="Account No.")
        self.acc_label.pack()
        self.acc = tk.Entry(self)
        self.acc.pack()

        self.pin_label = tk.Label(self, text="PIN / Password")
        self.pin_label.pack(pady=(10, 0))
        self.pin = tk.Entry(self, show="*")
        self.pin.pack()

        tk.Button(self, text="Login", command=self.login).pack(pady=20)

    def login(self):
        login_mode = self.login_type.get()
        user_id = self.acc.get().strip()
        password = self.pin.get().strip()

        # ---------- ADMIN LOGIN ----------
        if login_mode == "ADMIN":
            if not user_id or not password:
                return messagebox.showerror("Login Failed", "Admin ID and password required")

            if not models.verify_admin(user_id, password):
                return messagebox.showerror("Login Failed", "Invalid admin credentials")

            # ✅ ADMIN LOGIN SUCCESS
            self.destroy()

            app = BankGUI()
            app.session["account_id"] = "ADMIN"
            app.session["role"] = "ADMIN"
            app.build_sidebar()

            app.welcome_label.config(text="👋 Welcome, Bank Admin")
            app.after(300, lambda: app.show_welcome_popup("Bank Admin"))

            app.mainloop()
            return

        # ---------- USER LOGIN ----------
        aid = to_int(user_id)
        if aid <= 0:
            return messagebox.showerror("Login Failed", "Invalid Account Number")

        acc = models.get_account(aid)
        if not acc:
            return messagebox.showerror("Login Failed", "Invalid Account Number")

        # 🔒 Lock check ONLY for USER
        if acc.get("is_locked") :
            return messagebox.showerror(
                "Account Locked",
                "This account is locked due to 3 failed PIN attempts.\nPlease contact bank support."
            )

        # 🔑 VERIFY PIN
        if not verify_pin(password, acc["pin_hash"]):
            models.register_failed_attempt(aid)
            return messagebox.showerror("Login Failed", "Invalid PIN")

        # ✅ SUCCESS
        models.reset_failed_attempts(aid)

        self.destroy()

        app = BankGUI()
        app.session["account_id"] = aid
        app.session["role"] = "USER"
        app.build_sidebar()

        acc_name = acc.get("name", "User")
        app.welcome_label.config(text=f"👋 Welcome, {acc_name}")
        app.after(300, lambda: app.show_welcome_popup(acc_name))
        app.mainloop()


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
        # Background container (ALWAYS at back)
        self.bg_frame = tk.Frame(self)
        self.bg_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_canvas = tk.Canvas(self.bg_frame, highlightthickness=0, bd=0)
        self.bg_canvas.pack(fill="both", expand=True)
        # ----- Deposit State -----
        self.deposit_method = None
        self.deposit_upi_verified = False
        # ---------- Session ----------
        self.session = {
            "account_id": None,
            "role": "USER"   # default
        }
        self.current_theme = "light"
        self.theme = THEMES[self.current_theme]

        def draw_gradient():
            # 🔒 SAFETY CHECK
            if not self.bg_canvas.winfo_exists():
                return

            self.bg_canvas.delete("grad")

            height = self.winfo_height()
            width = self.winfo_width()

            for i in range(height):
                r1, g1, b1 = 230, 242, 255
                r2, g2, b2 = 255, 255, 255

                r = int(r1 + (r2 - r1) * (i / height))
                g = int(g1 + (g2 - g1) * (i / height))
                b = int(b1 + (b2 - b1) * (i / height))

                color = f"#{r:02x}{g:02x}{b:02x}"
                self.bg_canvas.create_line(0, i, width, i, fill=color, tags="grad")

        # ---------- SAFE RESIZE HANDLER FOR GRADIENT ----------
        self._gradient_job = None

        def on_resize(event=None):
            if not self.bg_canvas.winfo_exists():
                return
            if self._gradient_job:
                self.after_cancel(self._gradient_job)
            self._gradient_job = self.after(40, draw_gradient)

        self.bind("<Configure>", on_resize)

        # draw once initially
        self.after(100, draw_gradient)

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
        def apply_ttk_theme():
            bg = self.theme["card"]
            fg = self.theme["text"]

            style.configure(
                "TLabel",
                background=bg,
                foreground=fg
            )
            style.configure(
                "TEntry",
                fieldbackground=bg,
                foreground=fg
            )
            style.configure(
                "TButton",
                background=self.theme["primary"],
                foreground="white"
            )

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

        # --- Modern Centered Header ---
        header_frame = tk.Frame(self, bg="#1e3a8a")
        header_frame.pack(fill="x")

        header_label = tk.Label(
            header_frame,
            text="🏦  Banking Management System",
            font=("Segoe UI", 22, "bold"),
            fg="white",
            bg="#1e3a8a",
            pady=20
        )
        header_label.pack(anchor="center")

        container = tk.Frame(self, bg="#f0f2f5")
        container.pack(fill="both", expand=True)

        # ---------- LEFT SIDEBAR ----------
        self.sidebar = tk.Frame(container, bg="#1e293b", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ---------- RIGHT CONTENT ----------
        self.content = tk.Frame(container, bg="#f8fafc")
        self.content.pack(side="right", fill="both", expand=True)

        # ---------- TOP HEADER (INSIDE CONTENT) ----------
        self.topbar = tk.Frame(self.content, bg="#ffffff", height=60)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        self.welcome_label = tk.Label(
            self.topbar,
            text="👋 Welcome",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#1e293b"
        )
        self.welcome_label.pack(anchor="w", padx=20, pady=15)
        toggle_btn = tk.Label(
            self.topbar,
            text="🌙",
            font=("Segoe UI", 14),
            bg="white",
            cursor="hand2"
        )
        toggle_btn.pack(anchor="e", padx=20)

        def toggle_theme(event=None):
            self.current_theme = "dark" if self.current_theme == "light" else "light"
            self.theme = THEMES[self.current_theme]
            toggle_btn.config(text="☀️" if self.current_theme == "dark" else "🌙")
            apply_ttk_theme()
            self.apply_theme()

        toggle_btn.bind("<Button-1>", toggle_theme)
        
        # Track currently active sidebar button
        self.active_button = None
        # Track active tab button
        self.active_tab_button = None
        self.tab_buttons = {}
        # Build sidebar on startup (empty until login sets session)
        self.build_sidebar()
        self.apply_theme()

    def build_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()

        def add_btn(text, cmd):
            btn = tk.Button(
                self.sidebar,
                text=text,
                font=("Segoe UI", 11, "bold"),
                bg="#1e293b",
                fg="white",
                relief="flat",
                anchor="w",
                padx=20,
                pady=12,
                cursor="hand2",
                command=cmd
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e: btn.config(bg="#334155"))
            btn.bind("<Leave>", lambda e: btn.config(bg="#1e293b"))

        # ---- USER SERVICES ----
        if self.session["role"] == "ADMIN":
            add_btn("🆕 Create Account", self.show_create)

        add_btn("🔍 View Account", self.show_view)
        add_btn("💰 Deposit", self.show_deposit)
        add_btn("💸 Withdraw", self.show_withdraw)
        add_btn("🔁 Transfer", self.show_transfer)
        add_btn("📊 Transactions", self.show_transactions)
        add_btn("📞 Support", self.show_support)

        if self.session["role"] == "ADMIN":
            add_btn("❌ Delete Account", self.show_delete)

        tk.Frame(self.sidebar, bg="#1e293b").pack(expand=True, fill="both")

        add_btn("🚪 Logout", self.logout)


    def only_numbers(self, P):
        """Allow only digits (0–9). P = proposed value."""
        return P.isdigit() or P == ""
    
    def logout(self):
        self.destroy()
        LoginGUI().mainloop()

    def attach_rupee_formatter(self, var: tk.StringVar):
        def on_change(*_):
            val = var.get().replace(",", "")
            if val.isdigit():
                formatted = self.format_indian_number(val)
                if formatted != var.get():
                    var.set(formatted)
        var.trace_add("write", on_change)
    
    def apply_theme(self):
        t = self.theme

        # Root areas
        self.configure(bg=t["bg"])
        self.content.configure(bg=t["bg"])
        self.sidebar.configure(bg=t["sidebar"])
        self.topbar.configure(bg=t["card"])

        self.welcome_label.config(
            bg=t["card"],
            fg=t["text"]
        )

        # 🔁 Update sidebar buttons
        for w in self.sidebar.winfo_children():
            if isinstance(w, tk.Button):
                w.config(
                    bg=t["sidebar"],
                    fg="white",
                    activebackground=t["sidebar_hover"]
                )

        # 🔁 Update visible cards/content dynamically
        def recolor(parent):
            for w in parent.winfo_children():
                try:
                    if isinstance(w, tk.Frame):
                        if w.cget("bg") in ("white", "#ffffff", "#f8fafc"):
                            w.config(bg=t["card"])
                    elif isinstance(w, tk.Label):
                        w.config(
                            bg=w.cget("bg") if w.cget("bg") != "white" else t["card"],
                            fg=t["text"]
                        )
                except:
                    pass
                recolor(w)

        recolor(self.content)
    
    def format_indian_number(self, num_str):
        """
        Format number with Indian comma system (1,23,456).
        """
        num_str = num_str.replace(",", "")
        if not num_str.isdigit():
            return num_str

        # Convert to int → back to string
        n = int(num_str)
        s = str(n)

        if len(s) <= 3:
            return s

        # Indian formatting
        last3 = s[-3:]
        rest = s[:-3]
        parts = []

        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.append(rest)

        return ",".join(reversed(parts)) + "," + last3
    
    def on_deposit_change(self, *args):
        value = self.initial_deposit_var.get()
        raw = value.replace(",", "")
        if raw.isdigit():
            formatted = self.format_indian_number(raw)
            if formatted != value:
                self.initial_deposit_var.set(formatted)

    def show_welcome_popup(self, name):
        popup = tk.Toplevel(self)
        popup.title("Welcome")
        popup.transient(self)     # stay on top of main window
        popup.grab_set()          # focus only on popup
        popup.resizable(False, False)

        w, h = 360, 180
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")

        popup.configure(bg="white")

        # Header
        header = tk.Frame(popup, bg="#1e3a8a", height=40)
        header.pack(fill="x")

        tk.Label(
            header,
            text="🏦 Banking Management System",
            fg="white",
            bg="#1e3a8a",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=10)

        close_btn = tk.Label(
            header,
            text="✖",
            fg="white",
            bg="#1e3a8a",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        )
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", lambda e: popup.destroy())

        # Body
        body = tk.Frame(popup, bg="white")
        body.pack(expand=True, fill="both", pady=20)

        tk.Label(
            body,
            text=f"👋 Welcome, {name}",
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="#1e293b"
        ).pack(pady=5)

        tk.Label(
            body,
            text="We’re glad to have you back!",
            font=("Segoe UI", 11),
            bg="white",
            fg="#475569"
        ).pack()

        # Close button
        btn = tk.Label(
            body,
            text="Continue",
            bg="#2563eb",
            fg="white",
            font=("Segoe UI", 14, "bold"),
            padx=50,
            pady=16,
            cursor="hand2"
        )
        btn.pack(pady=15)

        btn.bind("<Enter>", lambda e: btn.config(bg="#1e3a8a"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#2563eb"))
        btn.bind("<Button-1>", lambda e: popup.destroy())

    def ask_pin_and_proceed(self, account_no, on_success):
        popup = tk.Toplevel(self)
        popup.title("Enter PIN")
        popup.transient(self)
        popup.grab_set()
        popup.resizable(False, False)
        popup.configure(bg="white")

        w, h = 320, 180
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(
            popup,
            text="🔐 Enter Transaction PIN",
            font=("Segoe UI", 13, "bold"),
            bg="white"
        ).pack(pady=15)

        pin_var = tk.StringVar()

        pin_entry = tk.Entry(
            popup,
            textvariable=pin_var,
            show="*",
            width=20
        )
        pin_entry.pack()
        pin_entry.focus()

        def verify():
            acc = models.get_account(account_no)
            if not acc:
                popup.destroy()
                return messagebox.showerror("Error", "Account not found")

            if not verify_pin(pin_var.get(), acc["pin_hash"]):
                models.register_failed_attempt(account_no)

                if acc.get("is_locked"):
                    popup.destroy()
                    return messagebox.showerror(
                        "Account Locked",
                        "3 wrong PIN attempts.\nAccount has been locked."
                    )

                messagebox.showerror("Wrong PIN", "Incorrect PIN")
                pin_var.set("")
                return

            # ✅ Correct PIN
            models.reset_failed_attempts(account_no)
            popup.destroy()
            on_success()

        tk.Button(
            popup,
            text="Confirm",
            bg="#2563eb",
            fg="white",
            command=verify
        ).pack(pady=15)

    def show_withdraw_receipt(self, acc_id, amount, fee, balance):
        win = tk.Toplevel(self)
        win.title("ATM Receipt")
        win.resizable(False, False)
        win.configure(bg="white")

        tk.Label(
            win,
            text="🏧 ATM Withdrawal Receipt",
            font=("Segoe UI", 14, "bold"),
            bg="white"
        ).pack(pady=10)

        details = [
            f"Account ID: {acc_id}",
            f"Amount: ₹{amount}",
            f"Charges: ₹{fee}",
            f"Date: {datetime.datetime.now().strftime('%d-%m-%Y %I:%M %p')}",
            f"Available Balance: ₹{balance}",
        ]

        for d in details:
            tk.Label(win, text=d, bg="white").pack(anchor="w", padx=20)

        tk.Button(win, text="Close", command=win.destroy).pack(pady=15)

    def show_transfer_receipt(self, from_acc, to_acc, amount, balance_after):
        win = tk.Toplevel(self)
        win.title("Transfer Receipt")
        win.resizable(False, False)
        win.configure(bg="white")

        tk.Label(
            win,
            text="🔁 Fund Transfer Receipt",
            font=("Segoe UI", 14, "bold"),
            bg="white"
        ).pack(pady=10)

        details = [
            f"From Account No.: {from_acc}",
            f"To Account No.: {to_acc}",
            f"Amount Transferred: ₹{amount}",
            f"Date: {datetime.datetime.now().strftime('%d-%m-%Y %I:%M %p')}",
            f"Available Balance: ₹{balance_after}",
        ]

        for d in details:
            tk.Label(win, text=d, bg="white").pack(anchor="w", padx=20, pady=2)

        tk.Button(win, text="Close", command=win.destroy).pack(pady=15)


    def show_atm_simulation_popup(self, on_continue):
        win = tk.Toplevel(self)
        win.title("ATM Withdrawal Simulation")
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)
        win.configure(bg="white")

        w, h = 420, 460
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(
            win,
            text="🏧 ATM Withdrawal Simulation",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(pady=10)

        # ---- GIF / IMAGE ----
        gif_path = Path(__file__).parent / "atm_cash_dispense.gif"
        if gif_path.exists():
            img = Image.open(gif_path)
            self._atm_frames = []

            try:
                while True:
                    frame = img.copy().resize((300, 300))
                    self._atm_frames.append(ImageTk.PhotoImage(frame))
                    img.seek(len(self._atm_frames))
            except EOFError:
                pass
            try:
                winsound.PlaySound("atm_cash.wav", winsound.SND_ASYNC)
            except:
                pass

            lbl = tk.Label(win, bg="white")
            lbl.pack(pady=10)

            def animate(i=0):
                lbl.config(image=self._atm_frames[i])
                win.after(120, animate, (i + 1) % len(self._atm_frames))

            animate()
        else:
            tk.Label(
                win,
                text="(ATM Simulation Visual)",
                fg="gray",
                bg="white"
            ).pack(pady=40)

        tk.Label(
            win,
            text="⚠ This is a simulation only.\nNo physical cash is dispensed.",
            font=("Segoe UI", 9),
            bg="white",
            fg="#475569"
        ).pack(pady=10)

        btn_frame = tk.Frame(win, bg="white")
        btn_frame.pack(pady=10)
        # ⏱ Auto close after 2 seconds and continue
        win.after(2000, lambda: (win.destroy(), on_continue()))
        tk.Button(
            btn_frame,
            text="Cancel",
            command=win.destroy
        ).pack(side="left", padx=10)


    def show_success_animation(self):
        win = tk.Toplevel(self)
        win.title("Success")
        win.geometry("300x200")
        win.config(bg="white")
    
        lbl = tk.Label(win, text="🎉 Account Created!", font=("Segoe UI", 16, "bold"), bg="white")
        lbl.pack(pady=20)
    
        win.after(2000, win.destroy)

    def on_view_tab_clicked(self, tab_name, command):
        # reset all tabs
        for name, btn in self.view_tab_buttons.items():
            btn.config(bg="#e2e8f0", fg="#1e293b", relief="solid", bd=1)

        # activate clicked tab
        active_btn = self.view_tab_buttons.get(tab_name)
        if active_btn:
            active_btn.config(bg="#2563eb", fg="white", relief="ridge", bd=2)
            self.active_view_tab = active_btn

        # clear content
        if self.view_tab_content:
            for w in self.view_tab_content.winfo_children():
                w.destroy()

        # load tab UI
        command()

    def show_support(self):
        frame = self.make_scrollable()

        # Header (same style as others)
        self.make_section_header(frame, "📞", "Customer Support")

        # Main card
        card = self.make_shadow_card(frame)

        content = tk.Frame(card, bg="white")
        content.pack(padx=30, pady=30, anchor="w")

        tk.Label(
            content,
            text="Customer Care Details",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(anchor="w", pady=(0, 15))

        tk.Label(
            content,
            text="📞 Toll Free Number: 1800-123-456",
            font=("Segoe UI", 11),
            bg="white"
        ).pack(anchor="w", pady=5)

        tk.Label(
            content,
            text="✉ Email Support: support@bankingsystem.in",
            font=("Segoe UI", 11),
            bg="white"
        ).pack(anchor="w", pady=5)

        tk.Label(
            content,
            text="🏦 Branch Address:",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            pady=10
        ).pack(anchor="w")

        tk.Label(
            content,
            text=(
                "Main Branch,\n"
                "Banking Management System,\n"
                "Sector 15, New Delhi – 110001\n"
                "India"
            ),
            font=("Segoe UI", 11),
            bg="white",
            justify="left"
        ).pack(anchor="w")

    def save_account_pdf(self, acc_id):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.utils import ImageReader
        except ImportError:
            messagebox.showerror(
                "PDF Error",
                "ReportLab is not installed.\n\nInstall using:\n pip install reportlab"
            )
            return

        file_path = f"account_{acc_id}.pdf"

        # PDF setup
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        y = height - 50

        # Title
        # Header banner
        c.setFillColorRGB(0.12, 0.23, 0.54)
        c.rect(0, height-80, width, 80, fill=1)
        c.setFillColorRGB(1, 1, 1)

        c.setFont("Helvetica-Bold", 22)
        c.drawString(50, height-50, "BANK ACCOUNT STATEMENT")

        c.setFont("Helvetica", 10)
        c.drawString(50, height-70, f"Generated on: {datetime.date.today()}")    
        y -= 30

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"Account ID: {acc_id}")
        y -= 40

        c.setFont("Helvetica", 11)

        # ------------------ BASIC DETAILS ------------------
        data = {
            "Full Name": self.full_name_var.get(),
            "Email": self.email_var.get(),
            "Phone Number": self.phone_var.get(),
            "DOB": self.dob_var.get(),
            "Gender": self.gender_var.get(),
            "Address Line 1": self.addr_line1_var.get(),
            "Village / Town": self.village_var.get(),
            "Tehsil": self.tehsil_var.get(),
            "District": self.district_var.get(),
            "State": self.state_var.get(),
            "Postal Code": self.postal_code_var.get(),
            "Initial Deposit": self.initial_deposit_var.get(),
            "Account Type": self.account_type_var.get(),
        }

        for field, value in data.items():
            c.drawString(50, y, f"{field}: {value}")
            y -= 22

            # Page break
            if y < 80:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 11)

        # ------------------ ADD IMAGES SECTION ------------------
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y - 10, "Attached KYC Documents:")
        y -= 40

        # ID Document Photo
        id_path = self.id_doc_path_var.get().strip()
        photo_path = self.photo_path_var.get().strip()

        if id_path:
            try:
                img = ImageReader(id_path)
                c.drawImage(img, 50, y - 180, width=200, height=180, preserveAspectRatio=True)
                c.setFont("Helvetica", 11)
                c.drawString(50, y - 200, "ID Document")
            except:
                c.drawString(50, y, "ID Document: (Unable to load image file)")
            y -= 230

        if photo_path:
            try:
                img = ImageReader(photo_path)
                c.drawImage(img, 50, y - 180, width=200, height=180, preserveAspectRatio=True)
                c.setFont("Helvetica", 11)
                c.drawString(50, y - 200, "Passport Photo")
            except:
                c.drawString(50, y, "Passport Photo: (Unable to load image file)")
            y -= 230

        # ---- TRANSACTION SUMMARY ----
        y -= 30
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Recent Transactions")

        y -= 20
        c.setFont("Helvetica", 10)

        txs = models.get_transactions(acc_id, limit=10)
        for t in txs:
            c.drawString(
                50, y,
                f"{t['created_at']} | {t['type']} | ₹{t['amount']} | Bal ₹{t['balance_after']}"
            )
            y -= 15
            if y < 80:
                c.showPage()
                y = height - 50

        # SAVE PDF
        c.save()

        messagebox.showinfo("PDF Generated", f"PDF saved successfully as:\n{file_path}")

    
    def validate_pin_live(self, P):
        """Allow typing only digits and max 6 chars live."""
        return (P.isdigit() and len(P) <= 6) or P == ""

    
    def only_10_digits(self, P):
        """Allow only digits and limit to 10 characters."""
        return (P.isdigit() and len(P) <= 10) or P == ""

    def validate_dob(self, P):
        """Auto-format DOB and validate only. No UI updates here."""

        # Allow empty
        if P == "":
            return True

        # Reject alphabets
        if any(not (c.isdigit() or c == "-") for c in P):
            return False

        # Digits only without hyphens
        raw = P.replace("-", "")

        # Max 8 digits: YYYYMMDD
        if len(raw) > 8:
            return False

        # Construct formatted DOB
        if len(raw) <= 4:
            formatted = raw
        elif len(raw) <= 6:
            formatted = raw[:4] + "-" + raw[4:]
        else:
            formatted = raw[:4] + "-" + raw[4:6] + "-" + raw[6:]

        # Update field if text differs
        if formatted != P:
            self.after(1, lambda: self.dob_var.set(formatted))
            return False

        # Full DOB auto-validation when 8 digits entered
        if len(raw) == 8:
            try:
                dob = datetime.date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
            except:
                return False

            today = datetime.date.today()

            # Cannot be future date
            if dob > today:
                return False

            # Must be 18+
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                return False

        return True
    
    def validate_pin_final(self, event=None):
        pin = self.pin_var.get().strip()
        confirm = self.confirm_pin_var.get().strip()

        # Length check
        if pin and (len(pin) < 4 or len(pin) > 6):
            messagebox.showerror("Invalid PIN", "PIN must be 4–6 digits.")
            self.pin_var.set("")
            return

        # Check confirm match
        if confirm and pin and pin != confirm:
            messagebox.showerror("PIN Error", "PIN and Confirm PIN do not match.")
            self.confirm_pin_var.set("")


    def live_pin_check(self, *args):
        pin = self.pin_var.get().strip()
        confirm = self.confirm_pin_var.get().strip()

        # Reset
        self.pin_error.config(text="")
        self.confirm_error.config(text="")
        self.match_label.config(text="", fg="green")

        # PIN length rule
        if pin and not (4 <= len(pin) <= 6):
            self.pin_error.config(text="❗ PIN must be 4–6 digits")
        elif pin and not pin.isdigit():
            self.pin_error.config(text="❗ PIN must contain only numbers")

        # Confirm PIN checks
        if confirm and not confirm.isdigit():
            self.confirm_error.config(text="❗ Confirm PIN must contain only numbers")

        # Match check (only if both valid length)
        if pin and confirm:
            if pin == confirm:
                self.match_label.config(text="✔ PIN Matched", fg="green")
            else:
                self.match_label.config(text="✖ PINs do not match", fg="red")
    
    def toggle_pin_visibility(self):
        if self.pin_visible:
            self.pin_entry.config(show="*")
            self.pin_visible = False
        else:
            self.pin_entry.config(show="")
            self.pin_visible = True

    def toggle_confirm_visibility(self):
        if self.confirm_visible:
            self.confirm_pin_entry.config(show="*")
            self.confirm_visible = False
        else:
            self.confirm_pin_entry.config(show="")
            self.confirm_visible = True

    def make_card(self, parent, width=500):
        """Creates a bordered card with padding — same style for all tabs."""
        outer = tk.Frame(parent, bg="#000000", bd=1)   # thin black border
        outer.pack(anchor="center", pady=20)

        inner = tk.Frame(outer, bg="white", width=width, padx=30, pady=25)
        inner.pack()

        return inner
    
    def make_shadow_card(self, parent, fill="both"):
        shadow = tk.Frame(parent, bg="#d1d5db")
        shadow.pack(
            anchor="n",
            padx=20,
            pady=20,
            fill="both",   # 🔑 NOT just x
            expand=True,
        )

        shadow.pack_propagate(False)   # 🔒 prevent shrinking
        card = tk.Frame(shadow, bg="white")
        card.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        shadow.grid_columnconfigure(0, weight=1)
        shadow.grid_rowconfigure(0, weight=1)

        return card

    def make_section_header(self, parent, icon_text, title_text):
        """
        Creates a centered header with icon + title + accent bar,
        matching the 'Create New Account' page design.
        """
        # Header panel background
        header_panel = tk.Frame(parent, bg="#eef6ff")
        header_panel.pack(fill="x", pady=(0, 5))

        # Content container inside header
        header_inner = tk.Frame(header_panel, bg="#eef6ff")
        header_inner.pack(anchor="center", pady=10)

        # Icon
        icon_label = tk.Label(
            header_inner,
            text=icon_text,
            font=("Segoe UI", 22),
            bg="#eef6ff",
            fg="#1e3a8a"
        )
        icon_label.pack(side="left", padx=(0, 10))

        # Title text
        title_label = tk.Label(
            header_inner,
            text=title_text,
            font=("Segoe UI", 20, "bold"),
            bg="#eef6ff",
            fg="#1e3a8a"
        )
        title_label.pack(side="left")

        # Blue accent bar
        accent = tk.Frame(parent, bg="#2563eb", height=3)
        accent.pack(fill="x", pady=(0, 15))

    def open_contact_support(self):
        win = tk.Toplevel(self)
        win.title("Contact Support")
        win.geometry("360x200")
        win.resizable(False, False)
    
        tk.Label(
            win,
            text="📞 Customer Support",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)
    
        tk.Label(win, text="Phone: 1800-123-456", font=("Segoe UI", 11)).pack(pady=5)
        tk.Label(win, text="Email: support@bankingsystem.in", font=("Segoe UI", 11)).pack(pady=5)
        tk.Label(win, text="Working Hours: 9 AM – 5 PM", fg="gray").pack(pady=5)
    
        tk.Button(win, text="Close", command=win.destroy).pack(pady=10)
    
    def make_scrollable(self):
        """Creates and returns a scrollable frame inside self.content"""
        self.clear_content()

        canvas = tk.Canvas(self.content, bg="#f8fafc", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        scroll_frame = tk.Frame(canvas, bg="#f8fafc")
        scroll_frame.grid_columnconfigure(0, weight=1)
        canvas_window = canvas.create_window(
            (0, 0),
            window=scroll_frame,
            anchor="nw",
            width=canvas.winfo_width()
        )

        def resize_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", resize_canvas)

        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scroll_frame.bind("<Configure>", update_scroll_region)

        # Mouse Wheel Scroll
        def _on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mouse_wheel)

        return scroll_frame

    # ---------- Utility ----------
    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()


    # Smooth fade-in animation for pages
    def fade_in(self, widget, duration=150):
        # fade from 0.7 → 1.0 opacity
        steps = 10
        delay = duration // steps

        for i in range(steps):
            alpha = 0.7 + (i / steps) * 0.3
            try:
                widget.update()
                self.update_idletasks()
                self.attributes('-alpha', alpha)
            except:
                pass
            widget.after(delay)

        self.attributes('-alpha', 1.0)

    # ---------- Clear tab ----------
    def clear_tab(self):
        if hasattr(self, "tab_content"):
            for widget in self.tab_content.winfo_children():
                widget.destroy()

    # ---------- Personal info tab ----------
    def load_tab_personal(self):
        self.clear_tab()
        card = self.make_card(self.tab_content)
        # Ensure dictionary exists
        if not hasattr(self, "field_widgets"):
            self.field_widgets = {}

        # Row spacing value
        ROW_PAD = 8

        # Full Name
        tk.Label(card, text="Full Name").grid(row=0, column=0, sticky="w", pady=ROW_PAD)
        full_name_entry = tk.Entry(card, width=35, textvariable=self.full_name_var, highlightthickness=2)
        full_name_entry.grid(row=0, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["Full Name"] = full_name_entry

        # Email
        tk.Label(card, text="Email").grid(row=1, column=0, sticky="w", pady=ROW_PAD)
        email_entry = tk.Entry(card, width=35, textvariable=self.email_var, highlightthickness=2)
        email_entry.grid(row=1, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["Email"] = email_entry

        # Phone
        tk.Label(card, text="Phone").grid(row=2, column=0, sticky="w", pady=ROW_PAD)
        phone_frame = tk.Frame(card, bg="white")
        phone_frame.grid(row=2, column=1, sticky="w", padx=10, pady=ROW_PAD)
        tk.Label(
            phone_frame,
            text="+91",
            bg="white",
            fg="#1e3a8a",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(0, 5))

        phone_entry = tk.Entry(phone_frame, width=25, textvariable=self.phone_var, validate="key",validatecommand=self.phone_validate, highlightthickness=2)
        phone_entry.pack(side="left")
        self.field_widgets["Phone Number"] = phone_entry

        # Date of Birth
        tk.Label(card, text="Date of Birth (YYYY-MM-DD)").grid(
            row=3, column=0, sticky="w", pady=ROW_PAD
        )

        self.dob_entry_widget = tk.Entry(card, width=30, textvariable=self.dob_var,validate="key", validatecommand=(self.register(self.validate_dob), "%P"),highlightthickness=2)
        self.dob_entry_widget.grid(row=3, column=1, padx=10, pady=5)
        self.field_widgets["Date of Birth"] = self.dob_entry_widget
        def update_dob_ui(*args):
            val = self.dob_var.get()
            raw = val.replace("-", "")

            # Reset UI
            self.dob_entry_widget.config(highlightbackground="#ccc")
            self.age_label_var.set("")

            # Only act when full 8 digits
            if len(raw) == 8:
                try:
                    dob = datetime.date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
                except:
                    self.dob_entry_widget.config(highlightbackground="red")
                    return

                today = datetime.date.today()

                # Future DOB
                if dob > today:
                    self.dob_entry_widget.config(highlightbackground="red")
                    messagebox.showerror("Invalid DOB", "DOB cannot be in the future.")
                    return

                # Age check
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if age < 18:
                    self.dob_entry_widget.config(highlightbackground="red")
                    messagebox.showerror("Age Error", "User must be 18+.")
                    return

                # Valid DOB
                self.dob_entry_widget.config(highlightbackground="green")
                self.age_label_var.set(f"Age: {age} years")

        # Trigger UI feedback when DOB changes
        self.dob_var.trace("w", update_dob_ui)

        # --- Live Age Display Below DOB ---
        self.age_label_var.set("")
        tk.Label(card, textvariable=self.age_label_var, fg="gray").grid(
            row=4, column=1, sticky="w", padx=10
        )

        # Gender (Radio Buttons)
        tk.Label(card, text="Gender").grid(row=4, column=0, sticky="w", pady=ROW_PAD)

        gender_frame = tk.Frame(card, bg="white")
        gender_frame.grid(row=4, column=1, sticky="w", padx=10, pady=ROW_PAD)

        tk.Radiobutton(
            gender_frame,
            text="Male",
            variable=self.gender_var,
            value="Male",
            bg="white"
        ).pack(side="left", padx=10)

        tk.Radiobutton(
            gender_frame,
            text="Female",
            variable=self.gender_var,
            value="Female",
            bg="white"
        ).pack(side="left", padx=10)

        tk.Radiobutton(
            gender_frame,
            text="Other",
            variable=self.gender_var,
            value="Other",
            bg="white"
        ).pack(side="left", padx=10)

        # Track for validation highlighting
        self.field_widgets["Gender"] = gender_frame

        # ID Type
        tk.Label(card, text="ID Document Type").grid(row=5, column=0, sticky="w", pady=ROW_PAD)
        id_type_box = ttk.Combobox(card, values=["Aadhaar","Passport","PAN","Driving License","Other"],
                           width=33, textvariable=self.id_type_var)
        id_type_box.grid(row=5, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["ID Document Type"] = id_type_box

        # Upload ID Document
        tk.Label(card, text="Upload ID Document").grid(row=6, column=0, sticky="w", pady=ROW_PAD)
        tk.Button(card, text="Browse…", command=self.choose_id_doc).grid(row=6, column=1, sticky="w", padx=10, pady=ROW_PAD)
        tk.Label(card, textvariable=self.id_doc_path_var, fg="gray").grid(row=7, column=0, columnspan=2, sticky="w", padx=10)
        self.field_widgets["ID Document Upload"] = tk.Label(card)

        # Upload Passport Photo
        tk.Label(card, text="Upload Passport Photo").grid(row=8, column=0, sticky="w", pady=ROW_PAD)
        tk.Button(card, text="Browse…", command=self.choose_photo).grid(row=8, column=1, sticky="w", padx=10, pady=ROW_PAD)
        tk.Label(card, textvariable=self.photo_path_var, fg="gray").grid(row=9, column=0, columnspan=2, sticky="w", padx=10)
        self.field_widgets["Passport Photo Upload"] = tk.Label(card)

    # ---------- Contact Tab ----------
    def load_tab_contact(self):
        self.clear_tab()
        ROW_PAD = 8

        # Alternate Phone
        tk.Label(self.tab_content, text="Alternate Phone").grid(row=0, column=0, sticky="w", pady=ROW_PAD)
        alt_phone_frame = tk.Frame(self.tab_content, bg="white")
        alt_phone_frame.grid(row=0, column=1, sticky="w", padx=10, pady=ROW_PAD)
        tk.Label(alt_phone_frame, text="+91", bg="white", fg="#1e3a8a",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0,5))
        
        tk.Entry(alt_phone_frame, width=25, textvariable=self.alt_phone_var,
         validate="key", validatecommand=self.phone_validate).pack(side="left")

        # Address Line 1
        tk.Label(self.tab_content, text="Address Line 1").grid(row=1, column=0, sticky="w", pady=ROW_PAD)
        
        addr1_entry = tk.Entry(self.tab_content, width=35, textvariable=self.addr_line1_var, highlightthickness=2)
        addr1_entry.grid(row=1, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["Address Line 1"] = addr1_entry

        # Village / Town (manual input)
        tk.Label(self.tab_content, text="Village / Town").grid(row=2, column=0, sticky="w", pady=ROW_PAD)
        
        village_entry = tk.Entry(self.tab_content, width=35, textvariable=self.village_var, highlightthickness=2)
        village_entry.grid(row=2, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["Village / Town"] = village_entry

        # Tehsil (auto-fill from API Block)
        tk.Label(self.tab_content, text="Tehsil").grid(row=4, column=0, sticky="w", pady=ROW_PAD)
        
        tehsil_entry = tk.Entry(self.tab_content, width=35, textvariable=self.tehsil_var, state="readonly", highlightthickness=2)
        tehsil_entry.grid(row=4, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["Tehsil"] = tehsil_entry

        # Postal Code / PIN Code (triggers lookup)
        tk.Label(self.tab_content, text="Postal Code / PIN Code").grid(row=3, column=0, sticky="w", pady=ROW_PAD)
        self.postal_entry = tk.Entry(self.tab_content, width=35, textvariable=self.postal_code_var,validate="key", validatecommand=self.num_validate, highlightthickness=2)
        self.postal_entry.grid(row=3, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["Postal Code"] = self.postal_entry
        
        # District (auto-fill)
        tk.Label(self.tab_content, text="District").grid(row=5, column=0, sticky="w", pady=ROW_PAD)
        district_entry = tk.Entry(self.tab_content, width=35, textvariable=self.district_var, state="readonly", highlightthickness=2)
        district_entry.grid(row=5, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["District"] = district_entry

        # State (auto-fill)
        tk.Label(self.tab_content, text="State").grid(row=6, column=0, sticky="w", pady=ROW_PAD)
        
        state_entry = tk.Entry(self.tab_content, width=35, textvariable=self.state_var, state="readonly", highlightthickness=2)
        state_entry.grid(row=6, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["State"] = state_entry

        # ---- Auto-fill Logic ----
        def autofill_from_pin(event=None):
            pin = self.postal_code_var.get().strip()

            if len(pin) != 6 or not pin.isdigit():
                return

            # Show loading text
            self.district_var.set("Searching...")
            self.state_var.set("Searching...")

            def do_lookup():
                from live_pincode_lookup import lookup_pin
                data = lookup_pin(pin)

                if data:
                    self.tehsil_var.set(data["tehsil"])       # Block → Tehsil
                    self.district_var.set(data["district"])
                    self.state_var.set(data["state"])
                else:
                    self.tehsil_var.set("")
                    self.district_var.set("")
                    self.state_var.set("")

            self.after(100, do_lookup)

        self.postal_entry.bind("<FocusOut>", autofill_from_pin)
        self.postal_entry.bind("<Return>", autofill_from_pin)

    # ---------- Security Tab ----------
    def load_tab_security(self):
        self.clear_tab()
        ROW_PAD = 8

        # --- Labels ---
        tk.Label(self.tab_content, text="PIN (4–6 digits)").grid(row=0, column=0, sticky="w", pady=ROW_PAD)
        tk.Label(self.tab_content, text="Confirm PIN").grid(row=2, column=0, sticky="w", pady=ROW_PAD)

        # --- Error labels ---
        self.pin_error = tk.Label(self.tab_content, text="", fg="red", bg="white")
        self.confirm_error = tk.Label(self.tab_content, text="", fg="red", bg="white")
        self.match_label = tk.Label(self.tab_content, text="", fg="green", bg="white")

        # --- PIN Entry ---
        self.pin_entry = tk.Entry(
            self.tab_content,
            width=30,
            show="*",
            highlightthickness=2,
            highlightbackground="#ccc",
            textvariable=self.pin_var,
            validate="key",
            validatecommand=(self.register(self.validate_pin_live), "%P")
        )
        self.field_widgets["PIN"] = self.pin_entry

        self.pin_entry.grid(row=0, column=1, padx=10, pady=ROW_PAD)

        # Show/Hide PIN button
        self.pin_visible = False
        btn_pin_toggle = tk.Button(
            self.tab_content,
            text="👁",
            command=self.toggle_pin_visibility,
            relief="flat",
            bg="white"
        )
        btn_pin_toggle.grid(row=0, column=2, padx=5)

        self.pin_error.grid(row=1, column=1, sticky="w")

        # --- Confirm PIN Entry ---
        self.confirm_pin_entry = tk.Entry(
            self.tab_content,
            width=30,
            show="*",
            highlightthickness=2,
            highlightbackground="#ccc",
            textvariable=self.confirm_pin_var,
            validate="key",
            validatecommand=(self.register(self.validate_pin_live), "%P")
        )
        self.field_widgets["Confirm PIN"] = self.confirm_pin_entry

        self.confirm_pin_entry.grid(row=2, column=1, padx=10, pady=ROW_PAD)

        # Show/Hide Confirm PIN button
        self.confirm_visible = False
        btn_confirm_toggle = tk.Button(
            self.tab_content,
            text="👁",
            command=self.toggle_confirm_visibility,
            relief="flat",
            bg="white"
        )
        btn_confirm_toggle.grid(row=2, column=2, padx=5)

        self.confirm_error.grid(row=3, column=1, sticky="w")
        self.match_label.grid(row=4, column=1, sticky="w")

        # Bind validation on typing
        self.pin_var.trace("w", self.live_pin_check)
        self.confirm_pin_var.trace("w", self.live_pin_check)

    # ---------- Deposit Tab ----------
    def load_tab_deposit(self):
        self.clear_tab()
        ROW_PAD = 8

        # --- Initial Deposit ---
        tk.Label(self.tab_content, text="Initial Deposit").grid(row=0, column=0, sticky="w", pady=ROW_PAD)

        deposit_frame = tk.Frame(self.tab_content, bg="white")
        deposit_frame.grid(row=0, column=1, sticky="w", padx=10, pady=ROW_PAD)
        
        tk.Label(
            deposit_frame,
            text="₹",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(side="left", padx=(0, 5))
        # Enable auto-format once
        self.initial_deposit_var.trace_add("write", self.on_deposit_change)
    
        deposit_entry = tk.Entry(
            deposit_frame,
            width=27,
            highlightthickness=2,
            highlightbackground="#ccc",
            textvariable=self.initial_deposit_var
        )
        deposit_entry.pack(side="left")
        self.field_widgets["Initial Deposit"] = deposit_entry

        # --- Account Type ---
        tk.Label(self.tab_content, text="Account Type").grid(row=1, column=0, sticky="w", pady=ROW_PAD)

        acc_type_box = ttk.Combobox(
            self.tab_content,
            values=["Savings", "Current"],
            width=27,
            textvariable=self.account_type_var
        )
        acc_type_box.grid(row=1, column=1, padx=10, pady=ROW_PAD)
        self.field_widgets["Account Type"] = acc_type_box


    def set_active_tab(self, tab_name):
        # Reset all buttons
        for name, btn in self.tab_buttons.items():
            btn.config(bg="#e2e8f0", fg="#1e293b", relief="solid", bd=1)
        # Activate clicked tab
        clicked_btn = self.tab_buttons[tab_name]
        clicked_btn.config(bg="#2563eb", fg="white", relief="ridge", bd=2)
        self.active_tab_button = clicked_btn

    def on_tab_clicked(self, tab_name, command):
        # Prevent reloading same tab (removes lag)
        if self.active_tab_button == self.tab_buttons.get(tab_name):
            return

        self.set_active_tab(tab_name)

        # Clear content smoothly
        if hasattr(self, "tab_content"):
            for w in self.tab_content.winfo_children():
                w.destroy()
        command()
    
    def choose_id_doc(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select ID Document",
            filetypes=[("Images/PDF", "*.jpg;*.jpeg;*.png;*.pdf"), ("All files", "*.*")]
        )
        if path:
            self.id_doc_path_var.set(path)

    def choose_photo(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select Passport Photo",
            filetypes=[("Images", "*.jpg;*.jpeg;*.png"), ("All files", "*.*")]
        )
        if path:
            self.photo_path_var.set(path)

    def load_tab_submit(self):
        self.clear_tab()

        submit_frame = tk.Frame(self.tab_content, bg="white")
        submit_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            submit_frame,
            text="Review all details and click Create Account",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#1e3a8a",
            pady=10
        ).pack(anchor="w")

        # Final Create Button
        submit_btn = tk.Label(
            submit_frame,
            text="✔  Create Account",
            font=("Segoe UI", 14, "bold"),
            bg="#2563eb",
            fg="white",
            padx=25,
            pady=12,
            cursor="hand2"
        )
        submit_btn.pack(anchor="center", pady=30)
        submit_btn.bind("<Enter>", lambda e: submit_btn.config(bg="#1e3a8a"))
        submit_btn.bind("<Leave>", lambda e: submit_btn.config(bg="#2563eb"))
        submit_btn.bind("<Button-1>", lambda e: self.final_submit())

    # ---------- Create Account ----------
    def show_create(self):
        self.clear_content()

        # --- Main Card Container ---
        # === Scrollable Form Wrapper ===
        canvas = tk.Canvas(self.content, bg="#f8fafc", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        # Inner frame inside canvas
    
        scroll_frame = tk.Frame(canvas, bg="#f8fafc")
        scroll_frame.grid_columnconfigure(0, weight=1)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scroll_frame.bind("<Configure>", update_scroll_region)

        # Attach mouse wheel scroll
        def _on_mouse_wheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", _on_mouse_wheel)

        # === NOW your normal form container goes inside scroll_frame ===
                # Full-width gray shadow card that stretches edge-to-edge
        shadow = tk.Frame(scroll_frame, bg="#d1d5db")
        shadow.pack(side="top", padx=20, pady=20, fill="both", expand=True)

        card = tk.Frame(shadow, bg="white")
        card.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Allow card to expand fully inside shadow
        shadow.grid_columnconfigure(0, weight=1)
        shadow.grid_rowconfigure(0, weight=1)

        # IMPORTANT:  now grid works correctly
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)
        card.grid_rowconfigure(4, weight=1)

        # Decorative gradient panel on the right side
                # Decorative right panel that stays on the far right
        right_panel = tk.Frame(card, bg="#e0ecff")
        right_panel.grid(row=0, column=1, sticky="ns", rowspan=5, padx=(0, 30), pady=30)
        
        # Configure columns properly: left expands, right fixed by content
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)
        
        # Large centered bank icon in the right panel
        icon_label = tk.Label(
            right_panel,
            text="🏦",
            font=("Segoe UI", 70),
            fg="#94a3b8",
            bg="#e0ecff"
        )
        icon_label.pack(expand=True)

        # --- Card Header Title---
        header_holder = tk.Frame(card, bg="#eef6ff")
        header_holder.grid(row=0, column=0, sticky="we", padx=10, pady=(10, 0))

        title = tk.Label(
            header_holder,
            text="🆕  Create New Account",
            font=("Segoe UI", 18, "bold"),
            fg="#1e3a8a",
            bg="#eef6ff",
            pady=12
        )
        title.pack(anchor="w", padx=20)

        # --- Accent Bar ---
        accent = tk.Frame(card, bg="#2563eb", height=3)
        accent.grid(row=1, column=0, sticky="we", padx=20, pady=(0, 10))

        tabs = tk.Frame(card, bg="white")
        tabs.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 15))
        
        tab_buttons = {
            "Personal Info": self.load_tab_personal,
            "Contact": self.load_tab_contact,
            "Security": self.load_tab_security,
            "Deposit": self.load_tab_deposit,
            "Submit": self.load_tab_submit,     # NEW TAB
        }

        for name, cmd in tab_buttons.items():
            btn = tk.Label(
                tabs,
                text=name,
                font=("Segoe UI", 10, "bold"),
                bg="#e2e8f0",
                fg="#1e293b",
                padx=12,
                pady=6,
                bd=1,
                relief="solid",
                cursor="hand2"
            )
            btn.pack(side="left", padx=5)

            self.tab_buttons[name] = btn

            # CLICK → switch tab
            btn.bind("<Button-1>", lambda e, n=name, c=cmd: self.on_tab_clicked(n, c))

            # HOVER EFFECT
            def on_enter(e, b=btn, n=name):
                if self.active_tab_button != b:
                    b.config(bg="#f1f5f9")  # light hover

            def on_leave(e, b=btn, n=name):
                if self.active_tab_button != b:
                    b.config(bg="#e2e8f0")  # default color

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        subtitle = tk.Label(
            card,
            text="Fill out the details below to create a new bank account.",
            font=("Segoe UI", 10),
            fg="#475569",
            bg="white"
        )
        subtitle.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 10))

        # This frame will show the content of selected tab
        self.tab_content = tk.Frame(
            card,
            bg="white",
            height=420   # 👈 FIXED HEIGHT FOR ALL TABS
        )
        self.tab_content.grid(row=4, column=0, sticky="nsew", padx=20, pady=10)

        # Prevent auto-shrinking
        self.tab_content.grid_propagate(False)
        # ✅ RESET TAB STATE & FORCE FIRST LOAD
        self.active_tab_button = None
        self.set_active_tab("Personal Info")
        self.load_tab_personal()
        

    def highlight_error(self, field_name):
        """Highlights a missing required field in RED."""
        widget = self.field_widgets.get(field_name)
        if not widget:
            return
        try:
            widget.config(highlightbackground="red")
        except:
            pass

    def clear_all_highlights(self):
        """Resets highlight borders to normal."""
        for w in self.field_widgets.values():
            try:
                w.config(highlightbackground="#ccc")
            except:
                pass

    def scroll_to_widget(self, widget):
        try:
            widget.update_idletasks()
            y = widget.winfo_rooty() - self.content.winfo_rooty()
            self.content.yview_moveto(y / self.content.winfo_height())
        except:
            pass

    def final_submit(self):
        missing = []

        # ---------------- PERSONAL TAB ----------------
        if not self.full_name_var.get().strip():
            missing.append("Full Name")

        if not self.email_var.get().strip():
            missing.append("Email")

        if not self.phone_var.get().strip():
            missing.append("Phone Number")

        if not self.dob_var.get().strip():
            missing.append("Date of Birth")

        if not self.gender_var.get().strip():
            missing.append("Gender")

        if not self.id_type_var.get().strip():
            missing.append("ID Document Type")

        if not self.id_doc_path_var.get().strip():
            missing.append("ID Document Upload")

        if not self.photo_path_var.get().strip():
            missing.append("Passport Photo Upload")

        # ---------------- CONTACT TAB ----------------
        if not self.addr_line1_var.get().strip():
            missing.append("Address Line 1")

        if not self.village_var.get().strip():
            missing.append("Village / Town")

        if not self.tehsil_var.get().strip():
            missing.append("Tehsil")

        if not self.postal_code_var.get().strip():
            missing.append("Postal Code")

        if not self.district_var.get().strip():
            missing.append("District")

        if not self.state_var.get().strip():
            missing.append("State")

        # ---------------- SECURITY TAB ----------------
        pin = self.pin_var.get().strip()
        confirm_pin = self.confirm_pin_var.get().strip()

        if not pin:
            missing.append("PIN")

        if not confirm_pin:
            missing.append("Confirm PIN")

        if pin and (len(pin) < 4 or len(pin) > 6 or not pin.isdigit()):
            return messagebox.showerror("Invalid PIN", "PIN must be 4–6 digits and numeric.")

        if pin and confirm_pin and pin != confirm_pin:
            return messagebox.showerror("PIN Error", "PIN and Confirm PIN do not match.")

        # ---------------- DEPOSIT TAB ----------------
        deposit_raw = self.initial_deposit_var.get().replace(",", "").strip()

        if not deposit_raw:
            missing.append("Initial Deposit")
        elif not deposit_raw.isdigit():
            return messagebox.showerror("Invalid Deposit", "Deposit must be a valid number.")

        if not self.account_type_var.get().strip():
            missing.append("Account Type")

        # ---------------- IF ANY MISSING FIELD ----------------
        if missing:
            self.clear_all_highlights()

            first_widget = None
            for field in missing:
                self.highlight_error(field)
                if not first_widget:
                    first_widget = self.field_widgets.get(field)

            # Auto-scroll to first missing
            if first_widget:
                self.scroll_to_widget(first_widget)

            messagebox.showerror(
                "Missing Required Fields",
                "Please fill the following:\n\n" + "\n".join(f"• {m}" for m in missing)
            )
            return

        # ---------------- CONFIRMATION POPUP ----------------
        if not messagebox.askyesno(
            "Confirm Submission",
            "Are you sure all details are correct?\n\nDo you want to create this account?"
        ):
            return

        # ---------------- CREATE ACCOUNT ----------------
        try:
            acc_id = models.create_account(
                name=self.full_name_var.get().strip(),
                email=self.email_var.get().strip(),
                phone=self.phone_var.get().strip(),
                pin=pin,
                initial_deposit=float(deposit_raw),
                dob=self.dob_var.get().strip(),
                gender=self.gender_var.get().strip(),
                id_type=self.id_type_var.get().strip(),
                id_document_path=self.id_doc_path_var.get().strip(),
                photo_path=self.photo_path_var.get().strip(),
                addr_line1=self.addr_line1_var.get().strip(),
                village=self.village_var.get().strip(),
                tehsil=self.tehsil_var.get().strip(),
                district=self.district_var.get().strip(),
                state=self.state_var.get().strip(),
                postal_code=self.postal_code_var.get().strip(),
                account_type=self.account_type_var.get().strip()
            )

            # SUCCESS POPUP
            messagebox.showinfo(
                "Account Created Successfully!",
                f"🎉 Your account has been created successfully!\n\nYour Account ID is:\n\n   {acc_id}\n\nPlease save it safely."
            )
            self.show_success_animation()
            self.save_account_pdf(acc_id)
            # AUTO-LOGIN USER
            self.session["account_id"] = acc_id
            self.session["role"] = "USER"
            # CLEAR ALL INPUT FIELDS
            self.full_name_var.set("")
            self.email_var.set("")
            self.phone_var.set("")
            self.pin_var.set("")
            self.confirm_pin_var.set("")
            self.initial_deposit_var.set("")
            self.gender_var.set("")
            self.id_type_var.set("")
            self.id_doc_path_var.set("")
            self.photo_path_var.set("")
            self.addr_line1_var.set("")
            self.village_var.set("")
            self.tehsil_var.set("")
            self.postal_code_var.set("")
            self.state_var.set("")
            self.district_var.set("")
            self.account_type_var.set("")

        except Exception as e:
            messagebox.showerror("Error", str(e))


    # ---------- View Account ----------
    def show_view(self):
        self.current_account = None
        frame = self.make_scrollable()

        # Header (same as Create Account)
        self.make_section_header(frame, "🔍", "View Account Details")

        # === OUTER CARD (ALWAYS VISIBLE) ===
        shadow = tk.Frame(frame, bg="#d1d5db")
        shadow.pack(anchor="nw", padx=20, pady=20, fill="x")

        card = tk.Frame(shadow, bg="white")
        card.pack(padx=2, pady=2, fill="both")

        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)

        # ---------- Right Decorative Panel ----------
        right_panel = tk.Frame(card, bg="#e0ecff", width=120)
        right_panel.grid(row=0, column=1, sticky="ns", padx=10, pady=10)

        icon_label = tk.Label(
            right_panel,
            text="🔍",
            font=("Segoe UI", 36),
            fg="#94a3b8",
            bg="#e0ecff"
        )
        icon_label.place(relx=0.5, rely=0.1, anchor="n")

        # ================= MAIN VIEW CONTAINER =================
        left_container = tk.Frame(card, bg="white")
        left_container.grid(row=0, column=0, sticky="nsew")

        # ================= ADMIN SEARCH ONLY =================
        if self.session["role"] == "ADMIN":
        
            search = tk.Frame(left_container, bg="white")
            search.pack(fill="x", padx=30, pady=25)

            tk.Label(search, text="Account No.", bg="white").grid(row=0, column=0, sticky="w")
            acc_entry = tk.Entry(search, width=14)
            acc_entry.grid(row=0, column=1, padx=10)

            load_btn = tk.Label(
                search,
                text="Load Account",
                font=("Segoe UI", 12, "bold"),
                bg="#2563eb",
                fg="white",
                padx=30,
                pady=12,
                cursor="hand2"
            )
            load_btn.grid(row=0, column=4, padx=20)

            load_btn.bind("<Enter>", lambda e: load_btn.config(bg="#1e3a8a"))
            load_btn.bind("<Leave>", lambda e: load_btn.config(bg="#2563eb"))
            load_btn.bind(
                "<Button-1>",
                lambda e: self.load_account(
                    acc_entry.get(),
                    "",           # 🔑 NO PIN FOR ADMIN
                    result_frame
                )
            )


        # ================= RESULT AREA (PRE-CREATED) =================
        result_frame = tk.Frame(left_container, bg="white")
        result_frame.pack(fill="both", expand=True, padx=30, pady=(0, 25))

        # ---------- AUTO LOAD FOR USER ----------
        if self.session["role"] == "USER":
            self.load_account(
                self.session["account_id"],
                "",        # PIN already verified at login
                result_frame
            )


    # ---------- LOAD ACCOUNT ----------
    def load_account(self, account_id, pin_input, result_frame):
        aid = to_int(account_id)
        # Clear previous result
        for w in result_frame.winfo_children():
            w.destroy()
        if aid <= 0:
            return messagebox.showerror("Error", "Enter a valid Account ID")

        acc = models.get_account(aid)
        if not acc:
            return messagebox.showerror("Error", "Account not found")

        # 🔒 Block ONLY USER — Admin must still see account
        if acc.get("is_locked") and self.session["role"] == "USER":
            return messagebox.showerror(
                "Account Locked",
                "This account is locked due to 3 failed PIN attempts.\nPlease contact bank support."
            )

        
        self.current_account = acc
        # ---------- SET SESSION ----------
        # Update session ONLY for USER login
        if self.session["role"] == "USER":
            self.session["account_id"] = acc["account_id"]


        # ================= HEADER STRIP =================
        header = tk.Frame(result_frame, bg="#eef6ff")
        header.pack(fill="x")

        # 🔴 LOCK STATUS BADGE
        if acc.get("is_locked"):
            tk.Label(
                header,
                text="LOCKED",
                bg="#dc2626",
                fg="white",
                font=("Segoe UI", 9, "bold"),
                padx=10,
                pady=4
            ).pack(side="right", padx=10)

        status = "Active" if acc["balance"] >= 0 else "Closed"
        color = "#16a34a" if status == "Active" else "#dc2626"

        tk.Label(
            header,
            text=status,
            bg=color,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4
        ).pack(side="right", padx=20)

        # ================= ACTION BUTTONS =================
        actions = tk.Frame(result_frame, bg="white")
        actions.pack(anchor="e", padx=20, pady=5)
        # 🔓 UNLOCK ACCOUNT (ADMIN ONLY)
        if self.session["role"] == "ADMIN" and acc.get("is_locked"):
        
            unlock_btn = tk.Label(
                actions,
                text="🔓 Unlock Account",
                font=("Segoe UI", 12, "bold"),
                bg="#16a34a",
                fg="white",
                padx=26,
                pady=10,
                cursor="hand2"
            )
            unlock_btn.pack(side="left", padx=10)

            unlock_btn.bind("<Enter>", lambda e: unlock_btn.config(bg="#15803d"))
            unlock_btn.bind("<Leave>", lambda e: unlock_btn.config(bg="#16a34a"))

            def unlock_action():
                if messagebox.askyesno(
                    "Confirm Unlock",
                    "Unlock this account?\n\nUser will be able to login again."
                ):
                    models.unlock_account(acc["account_id"])
                    messagebox.showinfo("Unlocked", "Account unlocked successfully.")
                    self.show_view()   # refresh view

            unlock_btn.bind("<Button-1>", lambda e: unlock_action())

        pdf_btn = tk.Label(
            actions,
            text="⬇  Download Statement (PDF)",
            font=("Segoe UI", 12, "bold"),
            bg="#2563eb",
            fg="white",
            padx=26,
            pady=10,
            cursor="hand2"
        )
        pdf_btn.pack(side="left", padx=10)

        pdf_btn.bind("<Enter>", lambda e: pdf_btn.config(bg="#1e3a8a"))
        pdf_btn.bind("<Leave>", lambda e: pdf_btn.config(bg="#2563eb"))
        pdf_btn.bind(
            "<Button-1>",
            lambda e: self.save_account_pdf(acc["account_id"])
        )

        # ================= TABS =================
        tabs = tk.Frame(result_frame, bg="white")
        tabs.pack(anchor="w", padx=20, pady=(10, 15))

        # TAB CONTENT FIRST (IMPORTANT)
        
        self.view_tab_content = tk.Frame(
            result_frame,
            bg="white",
            height=420     # 🔒 fixed height
        )
        self.view_tab_content.pack(fill="both", expand=False, padx=20, pady=10)
        self.view_tab_content.pack_propagate(False)
        self.view_tab_buttons.clear()


        view_tabs = {
            "Overview": self.load_view_overview,
            "Personal Info": self.load_view_personal,
            "Address": self.load_view_address,
            "Account": self.load_view_account,
            "Documents": self.load_view_documents,
            "Transactions": self.load_view_transactions,
            "Security": self.load_view_security,
            "Chart (30 Days)": self.load_view_chart,
        }

        for name, cmd in view_tabs.items():
            btn = tk.Label(
                tabs,
                text=name,
                font=("Segoe UI", 10, "bold"),
                bg="#e2e8f0",
                fg="#1e293b",
                padx=16,
                pady=8,
                bd=1,
                relief="solid",
                cursor="hand2"
            )
            btn.pack(side="left", padx=6)

            self.view_tab_buttons[name] = btn

            # CLICK → switch tab
            btn.bind(
                "<Button-1>",
                lambda e, n=name, c=cmd: self.on_view_tab_clicked(n, c)
            )

            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#e0f2fe"))
            btn.bind(
                "<Leave>",
                lambda e, b=btn: b.config(
                    bg="#2563eb" if b == self.active_view_tab else "#e2e8f0"
                )
            )
        self.on_view_tab_clicked("Overview", self.load_view_overview)

    def load_view_overview(self):
        f = self.view_tab_content
        acc = self.current_account

        tk.Label(
            f,
            text=f"Balance: ₹{acc['balance']}",
            font=("Segoe UI", 18, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(anchor="w", pady=10)

        canvas = tk.Canvas(f, height=70, bg="white", highlightthickness=0)
        canvas.pack(fill="x")
        width = min(acc["balance"] / 100, 400)
        canvas.create_rectangle(10, 25, 10 + width, 55, fill="#2563eb")


    def load_view_personal(self):
        f = self.view_tab_content
        acc = self.current_account
        for k in ["name", "email", "phone", "dob", "gender"]:
            tk.Label(f, text=f"{k.title()}: {acc.get(k,'')}", bg="white").pack(anchor="w", pady=3)


    def load_view_address(self):
        f = self.view_tab_content
        acc = self.current_account
        for k in ["addr_line1", "village", "tehsil", "district", "state", "postal_code"]:
            tk.Label(f, text=f"{k.replace('_',' ').title()}: {acc.get(k,'')}", bg="white").pack(anchor="w", pady=3)


    def load_view_account(self):
        f = self.view_tab_content
        acc = self.current_account
        for k in ["account_id", "account_type", "created_at", "balance"]:
            tk.Label(f, text=f"{k.replace('_',' ').title()}: {acc.get(k,'')}", bg="white").pack(anchor="w", pady=3)


    def load_view_documents(self):
        f = self.view_tab_content
        acc = self.current_account

        # Title
        tk.Label(
            f,
            text="Uploaded Documents",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(anchor="w", padx=20, pady=(10, 15))

        # Grid container (2 columns)
        grid = tk.Frame(f, bg="white")
        grid.pack(fill="x", padx=20)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        def document_card(parent, title, path, col):
            card = tk.Frame(
                parent,
                bg="#f8fafc",
                bd=1,
                relief="solid",
                width=360,
                height=300
            )
            card.grid(row=0, column=col, padx=15, sticky="n")
            card.grid_propagate(False)

            tk.Label(
                card,
                text=title,
                font=("Segoe UI", 12, "bold"),
                bg="#f8fafc"
            ).pack(pady=(10, 6))

            if not path or not os.path.exists(path):
                tk.Label(
                    card,
                    text="Not available",
                    fg="gray",
                    bg="#f8fafc"
                ).pack(expand=True)
                return

            ext = os.path.splitext(path)[1].lower()

            if ext in SUPPORTED_IMAGE_EXTS:
                try:
                    img = Image.open(path)

                    # 🔒 SAFE preview size (fits in view)
                    img.thumbnail((300, 200), Image.LANCZOS)

                    photo = ImageTk.PhotoImage(img)

                    lbl = tk.Label(card, image=photo, bg="#f8fafc")
                    lbl.image = photo  # IMPORTANT: keep reference
                    lbl.pack(expand=True)
                except Exception:
                    tk.Label(
                        card,
                        text="Preview not available",
                        fg="red",
                        bg="#f8fafc"
                    ).pack(expand=True)
            else:
                tk.Label(
                    card,
                    text=os.path.basename(path),
                    wraplength=260,
                    bg="#f8fafc"
                ).pack(expand=True)

        # ---- Two documents in ONE ROW ----
        document_card(grid, "ID Document", acc.get("id_document_path"), 0)
        document_card(grid, "Passport Photo", acc.get("photo_path"), 1)

    def load_view_transactions(self):
        f = self.view_tab_content
        acc = self.current_account

        cols = ("Date", "Description", "Debit", "Credit", "Balance")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=8)

        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="center")

        tree.pack(fill="x", pady=10)

        txs = models.get_transactions(acc["account_id"], limit=20)

        for t in txs:
            debit = t["amount"] if t["type"] in ("Withdraw", "Transfer-Out") else ""
            credit = t["amount"] if t["type"] in ("Deposit", "Transfer-In") else ""

            tree.insert("", "end", values=(
                t["created_at"][:16],
                t.get("note") or t["type"],
                debit,
                credit,
                t["balance_after"]
            ))

    def load_view_chart(self):
        f = self.view_tab_content
        acc = self.current_account
    
        txs = models.get_transactions(acc["account_id"], limit=30)
        amounts = [t["amount"] for t in txs if t["type"] in ("Deposit", "Withdraw")]
    
        if not amounts:
            tk.Label(f, text="No recent transactions", bg="white").pack()
            return
    
        max_amt = max(amounts)
    
        canvas = tk.Canvas(f, height=200, bg="white", highlightthickness=0)
        canvas.pack(fill="x", pady=10)
    
        x = 20
        for amt in amounts:
            h = int((amt / max_amt) * 150)
            canvas.create_rectangle(x, 180 - h, x + 15, 180, fill="#2563eb")
            x += 20
    
    def load_view_security(self):
        f = self.view_tab_content
        acc = self.current_account

        tk.Label(f, text="Change PIN", font=("Segoe UI", 12, "bold"), bg="white").pack(anchor="w", pady=10)

        old = ttk.Entry(f, show="*")
        new = ttk.Entry(f, show="*")

        ttk.Label(f, text="Old PIN").pack(anchor="w")
        old.pack(anchor="w")
        ttk.Label(f, text="New PIN").pack(anchor="w")
        new.pack(anchor="w")

        def update_pin():
            if self.session["role"] == "USER":
                if not verify_pin(old.get(), acc["pin_hash"]):
                    messagebox.showerror(
                        "PIN Mismatch",
                        "Old PIN is incorrect."
                    )
                    return

            if not new.get().isdigit() or not (4 <= len(new.get()) <= 6):
                messagebox.showerror("Invalid PIN", "New PIN must be 4–6 digits.")
                return

            models.update_pin(acc["account_id"], new.get())
            messagebox.showinfo("Success", "PIN updated successfully")

        update_btn = tk.Label(
            f,
            text="🔐  Update PIN",
            font=("Segoe UI", 12, "bold"),
            bg="#2563eb",
            fg="white",
            padx=30,
            pady=12,
            cursor="hand2"
        )
        update_btn.pack(pady=20)

        update_btn.bind("<Enter>", lambda e: update_btn.config(bg="#1e3a8a"))
        update_btn.bind("<Leave>", lambda e: update_btn.config(bg="#2563eb"))
        update_btn.bind("<Button-1>", lambda e: update_pin())

    def clear_dynamic_frame(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def update_summary(self, amount_lbl, method_lbl, status_lbl, amount, method, verified):
        amount_lbl.config(text=f"Amount: ₹{amount if amount else 0}")
        method_lbl.config(text=f"Method: {method}")
        status_lbl.config(
            text=f"Status: {'Verified' if verified else 'Not Verified'}",
            fg="#16a34a" if verified else "#dc2626"
        )

    def clear_dynamic_frame(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def make_two_column_layout(self, card, right_icon=""):
        # Configure card grid
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)
        card.grid_rowconfigure(0, weight=1)

        # LEFT (main content)
        left = tk.Frame(card, bg="white")
        left.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)

        # RIGHT (decorative)
        right = tk.Frame(card, bg="#e0ecff", width=140)
        right.grid(row=0, column=1, sticky="ns", padx=(0, 30), pady=30)
        right.grid_propagate(False)

        if right_icon:
            tk.Label(
                right,
                text=right_icon,
                font=("Segoe UI", 42),
                fg="#94a3b8",
                bg="#e0ecff"
            ).pack(expand=True)

        return left


    # ---------- Deposit ----------
    def show_deposit(self):
        frame = self.make_scrollable()
        self.make_section_header(frame, "💰", "Deposit Amount")

        card = self.make_shadow_card(frame)

        # ================= 3 COLUMN LAYOUT =================
        card.grid_columnconfigure(0, weight=50)
        card.grid_columnconfigure(1, weight=40)
        card.grid_columnconfigure(2, weight=10)
        
        card.grid_rowconfigure(0, weight=1)   # main content
        card.grid_rowconfigure(1, weight=0)   # confirm button
        card.grid_rowconfigure(2, weight=1)   # spacer
        
        # -------- LEFT (FORM) --------
        form = tk.Frame(card, bg="white")
        form.grid(row=0, column=0, sticky="nsew", padx=(40, 20), pady=30)
        
        # -------- MIDDLE (SUMMARY + HELP) --------
        middle = tk.Frame(card, bg="#f8fafc")
        middle.grid(row=0, column=1, sticky="nsew", padx=20, pady=30)
        
        # -------- RIGHT (ICON) --------
        right = tk.Frame(card, bg="#e0ecff")
        right.grid(row=0, column=2, sticky="nsew", padx=(10, 40), pady=30)
        
        tk.Label(
            right,
            text="💰",
            font=("Segoe UI", 60),
            fg="#94a3b8",
            bg="#e0ecff"
        ).pack(expand=True)
        
    
        ROW_PAD = 12

        # Account ID (Admin only)
        if self.session["role"] == "ADMIN":
            ttk.Label(form, text="Account No.").grid(row=0, column=0, sticky="w", pady=ROW_PAD)
            aid = ttk.Entry(form, width=18)
            aid.grid(row=0, column=1, sticky="w")
        else:
            aid = None

        # Amount
        ttk.Label(form, text="Amount").grid(row=1, column=0, sticky="w", pady=ROW_PAD)

        amount_frame = tk.Frame(form, bg="white")
        amount_frame.grid(row=1, column=1, sticky="w")

        tk.Label(
            amount_frame,
            text=RUPEE,
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(side="left", padx=(0, 5))

        amt_var = tk.StringVar()
        amt = ttk.Entry(amount_frame, width=22, textvariable=amt_var)
        self.attach_rupee_formatter(amt_var)
        amt.pack(side="left")

        def on_amount_change(*args):
            self.update_summary(
                summary_amount,
                summary_method,
                summary_status,
                amt_var.get(),
                method.get(),
                self.deposit_upi_verified
            )
        amt_var.trace_add("write", on_amount_change)

        # Deposit Method
        method = tk.StringVar(value="UPI")
        self.deposit_method = method
        self.deposit_upi_verified = False

        ttk.Label(form, text="Deposit Method").grid(row=2, column=0, sticky="w", pady=ROW_PAD)

        methods_frame = tk.Frame(form, bg="white")
        methods_frame.grid(row=2, column=1, sticky="w")

        dynamic_frame = tk.Frame(form, bg="white")
        dynamic_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 20))

        summary = tk.Frame(middle, bg="#f8fafc")
        summary.pack(fill="x", pady=(0, 20))

        tk.Label(
            summary,
            text="📊 Deposit Summary",
            font=("Segoe UI", 14, "bold"),
            bg="#f8fafc",
            fg="#1e3a8a"
        ).pack(anchor="w", pady=(10, 5))

        summary_amount = tk.Label(summary, text="Amount: ₹0", bg="#f8fafc")
        summary_amount.pack(anchor="w")

        summary_method = tk.Label(summary, text="Method: UPI", bg="#f8fafc")
        summary_method.pack(anchor="w")

        summary_status = tk.Label(
            summary, text="Status: Not Verified", bg="#f8fafc", fg="#dc2626"
        )
        summary_status.pack(anchor="w")

        help_box = tk.Frame(middle, bg="#f8fafc")
        help_box.pack(fill="x", pady=(10, 0))

        tk.Label(
            help_box,
            text="🔒 Safety & Info",
            font=("Segoe UI", 11, "bold"),
            bg="#f8fafc",
            fg="#1e3a8a"
        ).pack(anchor="w", pady=(0, 5))

        tips = [
            "• Never share your UPI PIN",
            "• Bank never asks for OTP",
            "• Verify UPI before deposit",
            "• All deposits are securely logged"
        ]

        for t in tips:
            tk.Label(
                help_box,
                text=t,
                bg="#f8fafc",
                fg="#475569"
            ).pack(anchor="w")


        # ================= LOGIC =================
        def update_ui():
            self.clear_dynamic_frame(dynamic_frame)
            selected = method.get()

            self.update_summary(
                summary_amount,
                summary_method,
                summary_status,
                amt.get(),
                selected,
                self.deposit_upi_verified
            )

            if selected == "UPI":
                ttk.Label(dynamic_frame, text="Enter UPI ID").pack(anchor="w")

                upi_frame = tk.Frame(dynamic_frame, bg="white")
                upi_frame.pack(anchor="w", pady=5)

                upi_entry = ttk.Entry(upi_frame, width=30)
                upi_entry.pack(side="left")

                status = tk.Label(upi_frame, text="❔", bg="white")
                status.pack(side="left", padx=10)

                def verify_upi():
                    upi = upi_entry.get().strip().lower()
                    if not UPI_REGEX.match(upi):
                        status.config(text="✖", fg="red")
                        self.deposit_upi_verified = False
                        return messagebox.showerror("Invalid UPI", "Invalid UPI format")

                    status.config(text="✔", fg="green")
                    self.deposit_upi_verified = True
                    self.qr_reference = None
                    self.update_summary(
                        summary_amount, summary_method, summary_status,
                        amt.get(), "UPI", True
                    )

                ttk.Button(dynamic_frame, text="Verify UPI", command=verify_upi).pack(anchor="w")

            elif selected == "QR":
                ttk.Label(
                    dynamic_frame,
                    text="Generate QR and scan using any UPI app",
                    foreground="#475569"
                ).pack(anchor="w", pady=(0, 6))

                ttk.Button(
                    dynamic_frame,
                    text="Generate QR",
                    command=lambda: generate_qr(to_float(amt.get()))
                ).pack(anchor="w")

                # QR does not need verification
                self.deposit_upi_verified = True
                self.qr_reference = None
                self.update_summary(
                    summary_amount, summary_method, summary_status,
                    amt.get(), "QR", True
                )

            else:  # Cash / Cheque
                ttk.Label(
                    dynamic_frame,
                    text="This method requires branch visit.",
                    foreground="#475569"
                ).pack(anchor="w")


        for m in ("Cash", "Cheque", "UPI", "QR"):
            ttk.Radiobutton(
                methods_frame,
                text=m,
                value=m,
                variable=method,
                command=update_ui
            ).pack(side="left", padx=10)

        # ================= CONFIRM BUTTON =================
        def confirm():
            amount = to_float(amt.get())
            acc = self.session["account_id"] if self.session["role"] == "USER" else to_int(aid.get())

            if amount <= 0 or acc <= 0:
                return messagebox.showerror("Error", "Valid amount and account required")

            if method.get() in ("UPI", "QR") and not self.deposit_upi_verified:
                return messagebox.showerror("Payment Not Verified", "Complete verification before deposit")

            def do_deposit():
                try:
                    note = None
                    if method.get() == "QR":
                        note = f"QR Deposit Ref: {getattr(self, 'qr_reference', '')}"

                    new = models.deposit(acc, amount, note=note)
                    messagebox.showinfo("Success", f"₹{amount} deposited\nNew Balance: ₹{new}")
                    amt.delete(0, tk.END)
                    self.deposit_upi_verified = False
                    update_ui()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            self.ask_pin_and_proceed(acc, do_deposit)

        confirm_btn = tk.Label(
            card,
            text="✔  Confirm Deposit",
            font=("Segoe UI", 17, "bold"),
            bg="#16a34a",
            fg="white",
            padx=70,
            pady=20,
            cursor="hand2"
        )
        confirm_btn.grid(row=1, column=0, columnspan=3, pady=(10, 30))
        confirm_btn.bind("<Button-1>", lambda e: confirm())
        confirm_btn.bind("<Enter>", lambda e: confirm_btn.config(bg="#15803d"))
        confirm_btn.bind("<Leave>", lambda e: confirm_btn.config(bg="#16a34a"))

        # Spacer to allow vertical expansion & scrolling
        spacer = tk.Frame(card, bg="white", height=20)
        spacer.grid(row=2, column=0, columnspan=3, sticky="nsew")

        update_ui()
        def generate_qr(amount):
            if amount <= 0:
                return messagebox.showerror("Invalid Amount", "Enter amount before generating QR")

            # ⏱️ Expiry (5 minutes) — 12 hour format
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
            expiry_ts = expiry_time.strftime("%I:%M %p")

            # Unique reference
            ref_id = f"QR{int(datetime.datetime.now().timestamp())}"

            upi_uri = (
                f"upi://pay?"
                f"pa={BANK_MASTER_UPI}&"
                f"pn=Bank%20Deposit&"
                f"am={amount}&"
                f"cu=INR&"
                f"tr={ref_id}"
            )

            qr = qrcode.make(upi_uri)

            # 🪟 POPUP WINDOW (MODAL)
            qr_win = tk.Toplevel(self)
            qr_win.title("Scan QR to Deposit")
            qr_win.transient(self)
            qr_win.grab_set()
            qr_win.resizable(False, False)
            qr_win.configure(bg="white")

            w, h = 420, 520
            x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
            qr_win.geometry(f"{w}x{h}+{x}+{y}")

            img = qr.resize((320, 320))
            qr_img = ImageTk.PhotoImage(img)

            tk.Label(qr_win, image=qr_img, bg="white").pack(pady=(20, 10))
            qr_win.qr_img = qr_img  # keep reference

            # 🔤 TEXT CHANGE
            tk.Label(
                qr_win,
                text="Scan to deposit",
                font=("Segoe UI", 15, "bold"),
                bg="white",
                fg="#1e3a8a"
            ).pack(pady=(0, 6))

            tk.Label(
                qr_win,
                text=f"Amount: {format_currency(amount)}",
                font=("Segoe UI", 11),
                bg="white",
                fg="#475569"
            ).pack()

            tk.Label(
                qr_win,
                text=f"Valid till {expiry_ts}",
                font=("Segoe UI", 11),
                fg="#dc2626",
                bg="white"
            ).pack(pady=10)

            ttk.Button(
                qr_win,
                text="Close",
                command=qr_win.destroy
            ).pack(pady=15)

            # 🧾 STORE QR REFERENCE
            self.qr_reference = ref_id

    # ---------- Withdraw ----------
    def show_withdraw(self):
        frame = self.make_scrollable()
        self.make_section_header(frame, "🏧", "ATM Withdrawal (Simulation)")

        card = self.make_shadow_card(frame)

        # ================= 3 COLUMN LAYOUT =================
        card.grid_columnconfigure(0, weight=50)   # Form
        card.grid_columnconfigure(1, weight=35)   # Summary
        card.grid_columnconfigure(2, weight=15)   # Icon

        card.grid_rowconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=0)
        card.grid_rowconfigure(2, weight=1)

        # -------- LEFT (FORM) --------
        form = tk.Frame(card, bg="white")
        form.grid(row=0, column=0, sticky="nsew", padx=(40, 20), pady=30)

        # -------- MIDDLE (SUMMARY) --------
        middle = tk.Frame(card, bg="#f8fafc")
        middle.grid(row=0, column=1, sticky="nsew", padx=20, pady=30)

        # -------- RIGHT (ICON) --------
        right = tk.Frame(card, bg="#e0ecff")
        right.grid(row=0, column=2, sticky="nsew", padx=(10, 40), pady=30)

        tk.Label(
            right,
            text="🏧",
            font=("Segoe UI", 60),
            fg="#94a3b8",
            bg="#e0ecff"
        ).pack(expand=True)

        ROW_PAD = 12

        # Account ID (Admin only)
        if self.session["role"] == "ADMIN":
            ttk.Label(form, text="Account No.").grid(row=0, column=0, sticky="w", pady=ROW_PAD)
            aid = ttk.Entry(form, width=18)
            aid.grid(row=0, column=1, sticky="w")
        else:
            aid = None

        # Amount
        ttk.Label(form, text="Withdrawal Amount").grid(row=1, column=0, sticky="w", pady=ROW_PAD)

        amount_frame = tk.Frame(form, bg="white")
        amount_frame.grid(row=1, column=1, sticky="w")

        tk.Label(
            amount_frame,
            text=RUPEE,
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(side="left", padx=(0, 5))

        amt_var = tk.StringVar()
        amt = ttk.Entry(amount_frame, width=22, textvariable=amt_var)
        self.attach_rupee_formatter(amt_var)
        amt.pack(side="left")

        # ATM Type
        atm_type = tk.StringVar(value="Bank ATM")

        ttk.Label(form, text="ATM Type").grid(row=2, column=0, sticky="w", pady=ROW_PAD)

        atm_frame = tk.Frame(form, bg="white")
        atm_frame.grid(row=2, column=1, sticky="w")

        ttk.Radiobutton(atm_frame, text="Bank ATM", variable=atm_type, value="Bank ATM").pack(side="left", padx=10)
        ttk.Radiobutton(atm_frame, text="Other Bank ATM", variable=atm_type, value="Other Bank ATM").pack(side="left", padx=10)

        # Location (Optional)
        ttk.Label(form, text="ATM Location (Optional)").grid(row=3, column=0, sticky="w", pady=ROW_PAD)
        location = ttk.Entry(form, width=25)
        location.grid(row=3, column=1, sticky="w")

        # ================= SUMMARY =================
        summary = tk.Frame(middle, bg="#f8fafc")
        summary.pack(fill="x")

        tk.Label(
            summary,
            text="📊 Withdrawal Summary",
            font=("Segoe UI", 14, "bold"),
            bg="#f8fafc",
            fg="#1e3a8a"
        ).pack(anchor="w", pady=(0, 10))

        s_amount = tk.Label(summary, text="Amount: ₹0", bg="#f8fafc")
        s_amount.pack(anchor="w")

        s_type = tk.Label(summary, text="ATM Type: Bank ATM", bg="#f8fafc")
        s_type.pack(anchor="w")

        s_fee = tk.Label(summary, text="Charges: ₹0", bg="#f8fafc")
        s_fee.pack(anchor="w")

        s_balance = tk.Label(summary, text="Balance After: —", bg="#f8fafc")
        s_balance.pack(anchor="w")

        s_status = tk.Label(summary, text="Status: Ready", fg="#16a34a", bg="#f8fafc")
        s_status.pack(anchor="w")

        # Disclaimer
        tk.Label(
            middle,
            text="⚠ This is a simulated ATM withdrawal.\nNo physical cash is dispensed.",
            fg="#475569",
            bg="#f8fafc",
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(20, 0))

        # ================= LIVE UPDATE =================
        def update_summary(*args):
            amt_val = to_float(amt_var.get())
            acc_id = self.session["account_id"] if self.session["role"] == "USER" else to_int(aid.get())
            acc = models.get_account(acc_id) if acc_id else None

            month = datetime.date.today().strftime("%Y-%m")
            txs = models.get_transactions(acc_id, limit=200)

            monthly_count = sum(
                1 for t in txs
                if t["type"] == "Withdraw" and t["created_at"].startswith(month)
            )

            fee = 0
            if monthly_count >= FREE_ATM_WITHDRAWALS:
                fee = ATM_CHARGE_AFTER_FREE

            bal_after = acc["balance"] - amt_val - fee if acc else None

            s_amount.config(text=f"Amount: {format_currency(amt_val)}")
            s_type.config(text=f"ATM Type: {atm_type.get()}")
            s_fee.config(text=f"Charges: ₹{fee}")

            if acc and bal_after >= 0:
                s_balance.config(text=f"Balance After: ₹{bal_after}")
                s_status.config(text="Status: Ready", fg="#16a34a")
            else:
                s_balance.config(text="Balance After: —")
                s_status.config(text="Status: Insufficient Balance", fg="#dc2626")

        amt_var.trace_add("write", update_summary)
        atm_type.trace_add("write", update_summary)

        def start_withdraw_flow():
            amt_val = to_float(amt_var.get())
            acc_id = self.session["account_id"] if self.session["role"] == "USER" else to_int(aid.get())
        
            if acc_id <= 0 or amt_val <= 0:
                return messagebox.showerror("Error", "Valid account and amount required")
        
            self.ask_pin_and_proceed(
                acc_id,
                lambda: self.show_atm_simulation_popup(
                    lambda: confirm(acc_id, amt_val)
                )
            )
        
        # ================= CONFIRM =================
        def confirm(acc_id, amt_val):
            if acc_id <= 0 or amt_val <= 0:
                return messagebox.showerror("Error", "Valid account and amount required")

            fee = 20 if atm_type.get() == "Other Bank ATM" else 0
            total = amt_val + fee
            # ----- DAILY LIMIT CHECK -----
            today = datetime.date.today().isoformat()
            txs = models.get_transactions(acc_id, limit=100)

            today_withdrawn = sum(
                t["amount"]
                for t in txs
                if t["type"] == "Withdraw" and t["created_at"].startswith(today)
            )

            if today_withdrawn + total > DAILY_ATM_LIMIT:
                return messagebox.showerror(
                    "Daily Limit Exceeded",
                    f"Daily ATM withdrawal limit is ₹{DAILY_ATM_LIMIT}.\n"
                    f"Already withdrawn today: ₹{today_withdrawn}"
                )

            acc = models.get_account(acc_id)

            # 🔒 FINAL SAFETY CHECK
            if acc.get("is_locked"):
                return messagebox.showerror(
                    "Account Locked",
                    "This account is locked.\nWithdrawals are disabled."
                )
            if acc["balance"] < total:
                return messagebox.showerror("Error", "Insufficient balance")
            try:
                note = f"ATM Withdrawal – {atm_type.get()} – {location.get()}"
                new_bal = models.withdraw(acc_id, total, note=note)
                self.show_withdraw_receipt(acc_id, amt_val, fee, new_bal)
                amt_var.set("")
                update_summary()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        confirm_btn = tk.Label(
            card,
            text="🏧  Withdraw",
            font=("Segoe UI", 17, "bold"),
            bg="#dc2626",
            fg="white",
            padx=70,
            pady=20,
            cursor="hand2"
        )
        confirm_btn.grid(row=1, column=0, columnspan=3, pady=(10, 30))

        def start_withdraw_flow():
            amt_val = to_float(amt_var.get())
            acc_id = self.session["account_id"] if self.session["role"] == "USER" else to_int(aid.get())

            if acc_id <= 0 or amt_val <= 0:
                return messagebox.showerror("Error", "Valid account and amount required")

            self.ask_pin_and_proceed(
                acc_id,
                lambda: self.show_atm_simulation_popup(
                    lambda: confirm(acc_id, amt_val)
                )
            )

        confirm_btn.bind("<Button-1>", lambda e: start_withdraw_flow())
        confirm_btn.bind("<Enter>", lambda e: confirm_btn.config(bg="#b91c1c"))
        confirm_btn.bind("<Leave>", lambda e: confirm_btn.config(bg="#dc2626"))
        # 🔒 Disable withdraw if locked
        if self.session["role"] == "USER":
            acc = models.get_account(self.session["account_id"])
            if acc and acc.get("is_locked"):
                confirm_btn.config(
                    bg="#9ca3af",
                    fg="white",
                    cursor="arrow",
                    text="🔒 Withdraw Disabled"
                )
                confirm_btn.unbind("<Button-1>")

        spacer = tk.Frame(card, bg="white", height=20)
        spacer.grid(row=2, column=0, columnspan=3, sticky="nsew")
        # 🔒 BLOCK WITHDRAW IF ACCOUNT IS LOCKED
        acc_id = self.session["account_id"]
        if self.session["role"] == "USER":
            acc = models.get_account(acc_id)
            if acc and acc.get("is_locked"):
                frame = self.make_scrollable()
                self.make_section_header(frame, "🏧", "ATM Withdrawal (Simulation)")

                card = self.make_shadow_card(frame)

                tk.Label(
                    card,
                    text="🔒 Account Locked",
                    font=("Segoe UI", 18, "bold"),
                    fg="#dc2626",
                    bg="white",
                    pady=30
                ).pack()

                tk.Label(
                    card,
                    text=(
                        "This account is locked due to multiple failed PIN attempts.\n\n"
                        "Withdrawals are temporarily disabled.\n\n"
                        "Please contact bank support or visit a branch."
                    ),
                    font=("Segoe UI", 11),
                    fg="#475569",
                    bg="white",
                    justify="center"
                ).pack(pady=10)

                return   # ⛔ STOP loading withdraw UI

        update_summary()


    # ---------- Transfer ----------
    def show_transfer(self):
        frame = self.make_scrollable()
        self.make_section_header(frame, "🔁", "Transfer Funds")

        card = self.make_shadow_card(frame)

        card.grid_columnconfigure(0, weight=50)
        card.grid_columnconfigure(1, weight=35)
        card.grid_columnconfigure(2, weight=15)

        # LEFT
        form = tk.Frame(card, bg="white")
        form.grid(row=0, column=0, sticky="nsew", padx=40, pady=30)

        # MIDDLE
        middle = tk.Frame(card, bg="#f8fafc")
        middle.grid(row=0, column=1, sticky="nsew", padx=20, pady=30)

        # RIGHT
        right = tk.Frame(card, bg="#e0ecff")
        right.grid(row=0, column=2, sticky="nsew", padx=20, pady=30)

        tk.Label(right, text="🔁", font=("Segoe UI", 60), bg="#e0ecff", fg="#94a3b8").pack(expand=True)

        ROW_PAD = 12

        ttk.Label(form, text="Transfer To (Account No.)").grid(row=0, column=0, sticky="w", pady=ROW_PAD)
        to_acc = ttk.Entry(form, width=25)
        to_acc.grid(row=0, column=1)

        ttk.Label(form, text="IFSC Code").grid(row=1, column=0, sticky="w", pady=ROW_PAD)
        ifsc = ttk.Entry(form, width=25)
        ifsc.grid(row=1, column=1)

        ttk.Label(form, text="Amount").grid(row=2, column=0, sticky="w", pady=ROW_PAD)
        amt_var = tk.StringVar()
        amt = ttk.Entry(form, width=25, textvariable=amt_var)
        self.attach_rupee_formatter(amt_var)
        amt.grid(row=2, column=1)

        # SUMMARY
        tk.Label(middle, text="📊 Transfer Summary", font=("Segoe UI", 14, "bold"),
                 bg="#f8fafc", fg="#1e3a8a").pack(anchor="w", pady=10)

        s_from = tk.Label(middle, text=f"From: {self.session['account_id']}", bg="#f8fafc")
        s_to = tk.Label(middle, text="To: —", bg="#f8fafc")
        s_amt = tk.Label(middle, text="Amount: ₹0", bg="#f8fafc")
        s_status = tk.Label(middle, text="Status: Ready", fg="#16a34a", bg="#f8fafc")

        for lbl in (s_from, s_to, s_amt, s_status):
            lbl.pack(anchor="w")

        def update_summary(*_):
            s_to.config(text=f"To: {to_acc.get()}")
            s_amt.config(text=f"Amount: ₹{amt_var.get()}")

        amt_var.trace_add("write", update_summary)
        to_acc.bind("<KeyRelease>", update_summary)

        def confirm_transfer():
            f = self.session["account_id"]
            t = to_int(to_acc.get())
            a = to_float(amt_var.get())

            if t <= 0 or a <= 0:
                return messagebox.showerror("Error", "Enter valid details")
            # ----- DAILY TRANSFER LIMIT CHECK -----
            today = datetime.date.today().isoformat()
            txs = models.get_transactions(f, limit=200)

            today_transferred = sum(
                t["amount"]
                for t in txs
                if t["type"] == "Transfer-Out" and t["created_at"].startswith(today)
            )

            if today_transferred + a > DAILY_TRANSFER_LIMIT:
                return messagebox.showerror(
                    "Daily Transfer Limit Exceeded",
                    f"Daily transfer limit is ₹{DAILY_TRANSFER_LIMIT}.\n"
                    f"Already transferred today: ₹{today_transferred}"
                )

            def do_transfer():
                try:
                    new_from_balance, _ = models.transfer(f, t, a)
                    self.show_transfer_receipt(f, t, a, new_from_balance)
                    amt_var.set("")
                    to_acc.delete(0, tk.END)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            self.ask_pin_and_proceed(f, do_transfer)

        confirm_btn = tk.Label(
            card,
            text="🔁  Confirm Transfer",
            font=("Segoe UI", 17, "bold"),
            bg="#2563eb",
            fg="white",
            padx=70,
            pady=20,
            cursor="hand2"
        )
        confirm_btn.grid(row=1, column=0, columnspan=3, pady=20)

        confirm_btn.bind("<Button-1>", lambda e: confirm_transfer())
        confirm_btn.bind("<Enter>", lambda e: confirm_btn.config(bg="#1e3a8a"))
        confirm_btn.bind("<Leave>", lambda e: confirm_btn.config(bg="#2563eb"))

    # ---------- Transactions ----------
    def show_transactions(self):
        frame = self.make_scrollable()

        # Same centered header style as Create Account
        self.make_section_header(frame, "📊", "Transaction History")

        # MAIN CARD (gray border + white body)
        card = self.make_shadow_card(frame, fill="both")

        # --- TOP INPUT AREA ---
        left = self.make_two_column_layout(card, right_icon="📊")
        box = left

        ttk.Label(box, text="Account No.").grid(row=0, column=0, sticky="w")
        aid = ttk.Entry(box, width=14)
        aid.grid(row=0, column=1, padx=10)
        if self.session["role"] == "USER":
            aid.insert(0, self.session["account_id"])
            aid.config(state="disabled")

        ttk.Button(
            box,
            text="Load",
            style="Primary.TButton",
            command=lambda: self.load_tx(
            self.session["account_id"] if self.session["role"] == "USER" else aid.get()
        )
        ).grid(row=0, column=2, padx=10)

        # --- TABLE AREA (INSIDE SAME CARD STYLE) ---
        table_card = self.make_shadow_card(frame)

        # 🔒 NEW INNER FRAME (pack-only zone)
        table_container = tk.Frame(table_card, bg="white")
        table_container.pack(fill="both", expand=True, padx=20, pady=20)

        cols = ("created_at", "type", "amount", "balance_after", "note")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings")

        for c in cols:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=150, anchor="w")

        yscroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        yscroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

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
        if self.session["role"] != "ADMIN":
            messagebox.showerror("Access Denied", "Admin access required.")
            return

        frame = self.make_scrollable()

        self.make_section_header(frame, "❌", "Delete Account")
        card = self.make_shadow_card(frame)

        left = self.make_two_column_layout(card, right_icon="❌")
        box = left
        box.grid_columnconfigure(0, weight=1)
        box.grid_columnconfigure(1, weight=1)

        ttk.Label(box, text="Account No.").grid(row=0, column=0)
        aid = ttk.Entry(box, width=10)
        aid.grid(row=0, column=1, padx=8)

        def delete():
            a = to_int(aid.get())
            if a <= 0:
                return messagebox.showerror("Error", "Valid Account ID required")

            acc = models.get_account(a)
            if not acc:
                return messagebox.showerror("Error", "Account not found")

        ttk.Button(frame, text="Delete", style="Primary.TButton", command=delete)\
            .pack(anchor="e", pady=10)
        self.after(100, lambda: self.build_sidebar())

# ---------- Run GUI ----------
if __name__ == "__main__":
    LoginGUI().mainloop()
