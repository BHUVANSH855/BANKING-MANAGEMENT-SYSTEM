# 🏦 Banking Management System

A **feature-rich Banking Management System** built using **Python (Tkinter GUI)** with **SQLite database**, supporting **User & Admin roles**, secure transactions, real-time notifications, and a modern UI.

---

## 🚀 Project Overview

This project simulates a real-world banking system where:

* **Users** can securely manage their bank accounts
* **Admins** can create, monitor, and control accounts
* All transactions are logged and reflected instantly
* Email & SMS notifications are triggered for important activities

The system focuses on **security, usability, and realistic banking workflows**.

---

## ✨ Key Features

### 👤 User Features

* Secure login using **Account Number & PIN**
* View account details and balance
* Deposit money (UPI / QR / Cash / Cheque – simulated)
* Withdraw money (ATM simulation with limits & charges)
* Transfer funds between accounts
* View transaction history
* Change PIN securely
* Download account statement (PDF)
* Instant **Email & SMS alerts** for:

  * Deposits
  * Withdrawals
  * Transfers
  * PIN change
  * Account lock

---

### 🛠️ Admin Features

* Admin login with separate credentials
* Create new bank accounts
* View any customer account
* Edit account balance
* Unlock locked accounts
* Delete accounts permanently
* Download customer account statements

---

## 🔐 Security Features

* PIN stored using **secure hashing**
* Account auto-lock after **3 failed PIN attempts**
* Daily limits for:

  * ATM withdrawals
  * Fund transfers
* Monthly maintenance & SMS charges
* Admin-only access to sensitive actions

---

## 🧱 System Architecture

* **Frontend (GUI):** Tkinter (Python)
* **Backend Logic:** Python modules
* **Database:** SQLite (`banking.db`)
* **Notifications:**

  * Email via SMTP (Gmail)
  * SMS via Fast2SMS API
* **Reports:** PDF generation using ReportLab

---

## 📂 Project Structure

```
BANK/
│
├── gui.py                  # Main GUI application
├── models.py               # Database & business logic
├── db.py                   # Database connection
├── utils.py                # Utility functions (PIN, helpers)
├── main.py                 # Entry point (if used)
│
├── admin_gui.py             # Admin interface
├── admin_gui_dashboard.py   # Admin dashboard
│
├── banking.db               # Main database
├── init_db.sql              # Database schema
│
├── atm_cash_dispense.gif    # ATM simulation
├── atm_cash.wav             # ATM sound
├── atm.mp4                  # Demo video asset
│
├── index.html               # Web UI (optional)
├── create_account.html
├── deposit.html
├── withdraw.html
├── transfer.html
├── transactions.html
├── styles.css
│
├── account_1.pdf            # Sample generated statement
└── README.md                # Project documentation
```

---

## ⚙️ How to Run the Project

### 1️⃣ Install Requirements

```bash
pip install pillow qrcode reportlab requests
```

### 2️⃣ Run the Application

```bash
python gui.py
```

---

## 📧 Email & 📱 SMS Configuration

> ⚠️ **Important:**
> For security reasons, do NOT commit real credentials.

* Update SMTP email & app password inside `send_email()`
* Update SMS API key inside `send_sms()`
* Use environment variables for production

---

## 📊 Notifications Triggered

* Account created
* Deposit successful
* Withdrawal successful
* Transfer successful
* PIN changed
* Account locked / unlocked
* Account deleted

All notifications are sent **instantly** via Email and SMS.

---

## 📄 Future Enhancements

* OTP-based login
* Interest calculation
* Loan & EMI module
* Mobile app integration
* Role-based permissions dashboard
* Cloud database support

---

## 👨‍💻 Developed By

**Banking Management System – Academic Project**
Developed using Python & SQLite for learning and demonstration purposes.

---

## ⭐ Final Notes

* This project is **ideal for college submission, demos, and internships**
* Shows strong understanding of **GUI, DB, security, and system design**
* Clean structure and scalable logic

---

✨ *Thank you for exploring this project!*
