/* ---------------- DASHBOARD ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  const accountId = Session.getAccountId();
  if (!accountId) {
    Toast.error("Please log in first.");
    setTimeout(() => (window.location.href = "index.html"), 800);
    return;
  }

  loadAccount();
  loadTransactions();

  document.getElementById("logoutBtn").addEventListener("click", async () => {
    const ok = await confirmModal({ title: "Log out?", body: "You'll need your account ID and PIN to sign back in.", confirmLabel: "Log out", danger: true });
    if (ok) {
      Session.clearAccountId();
      window.location.href = "index.html";
    }
  });

  async function loadAccount() {
    try {
      const acc = await BankAPI.getAccount(accountId);
      document.getElementById("accId").textContent = acc.account_id;
      document.getElementById("accName").textContent = acc.name;
      const statusEl = document.getElementById("accStatus");
      statusEl.textContent = acc.is_locked ? "Locked" : "Active";
      statusEl.style.color = acc.is_locked ? "var(--rose-light)" : "var(--emerald-light)";
      countUp(document.getElementById("accBalance"), Number(acc.balance || 0), { decimals: 2 });
    } catch (err) {
      Toast.error(err.message);
    }
  }

  async function loadTransactions() {
    const body = document.getElementById("txBody");
    try {
      const txs = await BankAPI.transactions(accountId, 25);
      if (!txs.length) {
        body.innerHTML = `<tr><td colspan="5"><div class="empty-state" style="padding:20px;"><i class="fa-solid fa-inbox"></i>No transactions yet</div></td></tr>`;
        return;
      }
      body.innerHTML = txs.map(rowHTML).join("");
    } catch (err) {
      body.innerHTML = `<tr><td colspan="5">Could not load transactions.</td></tr>`;
    }
  }

  function rowHTML(tx) {
    const negative = /Withdraw|Transfer-Out/i.test(tx.type);
    return `<tr>
      <td><span class="type-chip">${tx.type}</span></td>
      <td class="${negative ? "amt-neg" : "amt-pos"}">${negative ? "−" : "+"}₹${fmt.inr(tx.amount)}</td>
      <td class="mono">₹${fmt.inr(tx.balance_after)}</td>
      <td>${tx.note || ""}</td>
      <td class="mono">${fmt.date(tx.created_at)}</td>
    </tr>`;
  }

  /* ---------- DEPOSIT ---------- */
  document.getElementById("depositForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("depositAmount");
    if (!validateAmount(input.value)) { markInvalid(input, "Enter an amount greater than 0"); return; }
    Loader.show("Depositing…");
    try {
      const res = await BankAPI.deposit(accountId, input.value);
      Toast.success(`Deposited ₹${fmt.inr(input.value)}. New balance ₹${fmt.inr(res.balance)}.`);
      input.value = "";
      loadAccount(); loadTransactions();
    } catch (err) { Toast.error(err.message); }
    finally { Loader.hide(); }
  });

  /* ---------- WITHDRAW ---------- */
  document.getElementById("withdrawForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const amount = document.getElementById("withdrawAmount");
    const pin = document.getElementById("withdrawPin");
    let ok = true;
    if (!validateAmount(amount.value)) { markInvalid(amount, "Enter an amount greater than 0"); ok = false; }
    if (!validatePin(pin.value)) { markInvalid(pin, "PIN must be 4–6 digits"); ok = false; }
    if (!ok) return;
    Loader.show("Withdrawing…");
    try {
      const res = await BankAPI.withdraw(accountId, amount.value, pin.value);
      Toast.success(`Withdrew ₹${fmt.inr(amount.value)}. New balance ₹${fmt.inr(res.balance)}.`);
      amount.value = ""; pin.value = "";
      loadAccount(); loadTransactions();
    } catch (err) { Toast.error(err.message); }
    finally { Loader.hide(); }
  });

  /* ---------- TRANSFER ---------- */
  document.getElementById("transferForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const to = document.getElementById("transferTo");
    const amount = document.getElementById("transferAmount");
    const pin = document.getElementById("transferPin");
    let ok = true;
    if (!to.value) { markInvalid(to, "Enter a recipient account ID"); ok = false; }
    if (!validateAmount(amount.value)) { markInvalid(amount, "Enter an amount greater than 0"); ok = false; }
    if (!validatePin(pin.value)) { markInvalid(pin, "PIN must be 4–6 digits"); ok = false; }
    if (!ok) return;
    Loader.show("Transferring…");
    try {
      const res = await BankAPI.transfer(accountId, to.value, amount.value, pin.value);
      Toast.success(`Transferred ₹${fmt.inr(amount.value)} to account ${to.value}.`);
      to.value = ""; amount.value = ""; pin.value = "";
      loadAccount(); loadTransactions();
    } catch (err) { Toast.error(err.message); }
    finally { Loader.hide(); }
  });
});
