/* ==========================================================================
   BankSys — API client
   Central place for every call this frontend makes to the Flask backend.
   Every endpoint below matches backend/app/app.py exactly:

     POST /api/create_account   { name, email, phone, pin, initial_deposit } -> { account_id }
     POST /api/deposit          { account_id, amount }                      -> { balance }
     POST /api/withdraw         { account_id, amount, pin }                 -> { balance }
     POST /api/transfer         { from_id, to_id, amount, pin }             -> { from_balance, to_balance }
     GET  /api/transactions/:id?limit=                                     -> [ ...transactions ]
     GET  /api/account/:id                                                 -> { account fields }
     POST /api/admin/login          { pin }                                -> { status }
     POST /api/admin/change-pin     { old_pin, new_pin }                   -> { status }
     POST /api/admin/bank-balance   { pin }                                -> { bank_balance }
     POST /api/admin/stats          { pin }                                -> { total_users, total_deposits, total_withdrawals }
     POST /api/admin/users          { pin }                                -> [ ...users ]
     POST /api/admin/transactions   { pin }                                -> [ ...transactions ]
     POST /api/admin/toggle-lock    { pin, account_id }                    -> { account_id, status }
   ========================================================================== */

const BankAPI = (() => {
  // The original build hardcoded http://127.0.0.1:5000/api, which breaks the
  // moment the site is deployed anywhere but localhost (e.g. Render). This
  // resolves to the local Flask dev server only when actually running
  // locally, and falls back to a same-origin relative path otherwise.
  const isLocal = ["localhost", "127.0.0.1"].includes(location.hostname);
  const BASE = isLocal ? "http://127.0.0.1:5000/api" : "/api";

  async function request(endpoint, { method = "GET", data = null } = {}) {
    const options = { method, headers: {} };
    if (data !== null) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(data);
    }
    let res;
    try {
      res = await fetch(BASE + endpoint, options);
    } catch (networkErr) {
      throw new Error("Can't reach the bank server. Is the backend running?");
    }
    let json = {};
    try { json = await res.json(); } catch (_) { /* empty body */ }
    if (!res.ok) throw new Error(json.error || `Request failed (${res.status})`);
    return json;
  }

  return {
    createAccount: (payload) => request("/create_account", { method: "POST", data: payload }),
    deposit: (account_id, amount) => request("/deposit", { method: "POST", data: { account_id, amount } }),
    withdraw: (account_id, amount, pin) => request("/withdraw", { method: "POST", data: { account_id, amount, pin } }),
    transfer: (from_id, to_id, amount, pin) => request("/transfer", { method: "POST", data: { from_id, to_id, amount, pin } }),
    transactions: (account_id, limit = 200) => request(`/transactions/${encodeURIComponent(account_id)}?limit=${limit}`),
    getAccount: (account_id) => request(`/account/${encodeURIComponent(account_id)}`),
    changePin: (account_id, old_pin, new_pin) => request(`/account/${encodeURIComponent(account_id)}/change-pin`, { method: "POST", data: { old_pin, new_pin } }),

    adminLogin: (pin) => request("/admin/login", { method: "POST", data: { pin } }),
    adminChangePin: (old_pin, new_pin) => request("/admin/change-pin", { method: "POST", data: { old_pin, new_pin } }),
    adminBankBalance: (pin) => request("/admin/bank-balance", { method: "POST", data: { pin } }),
    adminStats: (pin) => request("/admin/stats", { method: "POST", data: { pin } }),
    adminUsers: (pin) => request("/admin/users", { method: "POST", data: { pin } }),
    adminTransactions: (pin) => request("/admin/transactions", { method: "POST", data: { pin } }),
    adminToggleLock: (pin, account_id) => request("/admin/toggle-lock", { method: "POST", data: { pin, account_id } }),
    adminDeleteAccount: (pin, account_id) => request("/admin/delete-account", { method: "POST", data: { pin, account_id } }),
  };
})();

/* ---------------- SESSION HELPERS ---------------- */
const Session = {
  getAccountId: () => localStorage.getItem("account_id"),
  setAccountId: (id) => localStorage.setItem("account_id", id),
  clearAccountId: () => localStorage.removeItem("account_id"),

  // Admin PIN lives only in sessionStorage (cleared when the tab closes) —
  // every admin/* endpoint requires the PIN on each call, so we keep it in
  // memory for the session rather than asking the admin to retype it for
  // every single action.
  getAdminPin: () => sessionStorage.getItem("admin_pin"),
  setAdminPin: (pin) => sessionStorage.setItem("admin_pin", pin),
  clearAdminPin: () => sessionStorage.removeItem("admin_pin"),
};

/* ---------------- FORMATTERS ---------------- */
const fmt = {
  inr(amount) {
    const n = Number(amount || 0);
    return n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  date(iso) {
    if (!iso) return "—";
    const d = new Date(iso.replace(" ", "T"));
    if (isNaN(d)) return iso;
    return d.toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  },
};

function validatePin(pin) { return /^\d{4,6}$/.test(pin); }
function validateAmount(amount) { return !isNaN(amount) && Number(amount) > 0; }
