document.addEventListener("DOMContentLoaded", () => {
  const pin = Session.getAdminPin();
  if (!pin) {
    Toast.error("Please sign in as admin first.");
    setTimeout(() => (window.location.href = "admin_login.html"), 800);
    return;
  }

  loadStats();
  loadVault();
  loadUsers();
  loadAllTransactions();

  document.getElementById("logoutBtn").addEventListener("click", async () => {
    const ok = await confirmModal({ title: "Log out of admin?", body: "You'll need the admin PIN to sign back in.", confirmLabel: "Log out", danger: true });
    if (ok) {
      Session.clearAdminPin();
      window.location.href = "admin_login.html";
    }
  });

  async function loadStats() {
    try {
      const s = await BankAPI.adminStats(pin);
      countUp(document.getElementById("statUsers"), s.total_users, { decimals: 0 });
      countUp(document.getElementById("statDeposits"), s.total_deposits, { prefix: "₹" });
      countUp(document.getElementById("statWithdrawals"), s.total_withdrawals, { prefix: "₹" });
    } catch (err) {
      handleAuthError(err);
    }
  }

  async function loadVault() {
    try {
      const v = await BankAPI.adminBankBalance(pin);
      countUp(document.getElementById("statVault"), v.bank_balance, { prefix: "₹" });
    } catch (err) {
      handleAuthError(err);
    }
  }

  async function loadUsers() {
    const body = document.getElementById("usersBody");
    try {
      const users = await BankAPI.adminUsers(pin);
      if (!users.length) {
        body.innerHTML = `<tr><td colspan="6"><div class="empty-state"><i class="fa-solid fa-users"></i>No users yet</div></td></tr>`;
        return;
      }
      body.innerHTML = users.map(userRow).join("");
      body.querySelectorAll("[data-toggle]").forEach((btn) => {
        btn.addEventListener("click", () => toggleLock(btn.dataset.toggle, btn.dataset.name));
      });
    } catch (err) {
      handleAuthError(err);
    }
  }

  function userRow(u) {
    const locked = u.status === "Locked";
    return `<tr>
      <td class="mono">${u.account_id}</td>
      <td>${u.name}</td>
      <td><small>${u.email || "—"}<br>${u.phone || "—"}</small></td>
      <td class="mono">₹${fmt.inr(u.balance)}</td>
      <td><span class="stamp ${locked ? "locked" : "active"}">${u.status}</span></td>
      <td><button class="btn sm ${locked ? "success" : "danger"}" data-toggle="${u.account_id}" data-name="${u.name}">
        ${locked ? "Unlock" : "Lock"}
      </button></td>
    </tr>`;
  }

  async function toggleLock(accountId, name) {
    const ok = await confirmModal({
      title: "Confirm status change",
      body: `Change account access for ${name} (ID ${accountId})?`,
      confirmLabel: "Confirm",
    });
    if (!ok) return;
    Loader.show("Updating account…");
    try {
      const res = await BankAPI.adminToggleLock(pin, accountId);
      Toast.success(`Account ${res.account_id} is now ${res.status}.`);
      loadUsers();
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  }

  async function loadAllTransactions() {
    const body = document.getElementById("allTxBody");
    try {
      const txs = await BankAPI.adminTransactions(pin);
      if (!txs.length) {
        body.innerHTML = `<tr><td colspan="7"><div class="empty-state"><i class="fa-solid fa-inbox"></i>No transactions yet</div></td></tr>`;
        return;
      }
      body.innerHTML = txs.slice(0, 100).map((t) => {
        const negative = /Withdraw|Transfer-Out/i.test(t.type);
        return `<tr>
          <td class="mono">${fmt.date(t.created_at)}</td>
          <td class="mono">${t.account_id}</td>
          <td>${t.name}</td>
          <td><span class="type-chip">${t.type}</span></td>
          <td class="${negative ? "amt-neg" : "amt-pos"}">${negative ? "−" : "+"}₹${fmt.inr(t.amount)}</td>
          <td class="mono">₹${fmt.inr(t.balance_after)}</td>
          <td>${t.note || ""}</td>
        </tr>`;
      }).join("");
    } catch (err) {
      handleAuthError(err);
    }
  }

  document.getElementById("changePinForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const oldPin = document.getElementById("oldPin");
    const newPin = document.getElementById("newPin");
    let ok = true;
    if (!validatePin(oldPin.value)) { markInvalid(oldPin, "Enter your current PIN"); ok = false; }
    if (!validatePin(newPin.value)) { markInvalid(newPin, "PIN must be 4–6 digits"); ok = false; }
    if (!ok) return;

    Loader.show("Updating PIN…");
    try {
      await BankAPI.adminChangePin(oldPin.value, newPin.value);
      Session.setAdminPin(newPin.value);
      Toast.success("Admin PIN updated.");
      oldPin.value = ""; newPin.value = "";
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  });

  function handleAuthError(err) {
    Toast.error(err.message);
    if (/unauthorized|invalid/i.test(err.message)) {
      Session.clearAdminPin();
      setTimeout(() => (window.location.href = "admin_login.html"), 1000);
    }
  }
});
