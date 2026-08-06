document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("txForm");
  const body = document.getElementById("txBody");
  const accIdInput = document.getElementById("account_id");

  const savedId = Session.getAccountId();
  if (savedId) { accIdInput.value = savedId; loadTx(savedId); }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!accIdInput.value) { markInvalid(accIdInput, "Enter an account ID"); return; }
    loadTx(accIdInput.value);
  });

  async function loadTx(id) {
    body.innerHTML = `<tr><td colspan="5"><div class="skeleton" style="height:16px;"></div></td></tr>`;
    try {
      const txs = await BankAPI.transactions(id, 200);
      if (!txs.length) {
        body.innerHTML = `<tr><td colspan="5"><div class="empty-state"><i class="fa-solid fa-inbox"></i>No transactions for this account yet</div></td></tr>`;
        return;
      }
      body.innerHTML = txs.map(rowHTML).join("");
    } catch (err) {
      body.innerHTML = `<tr><td colspan="5"><div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i>${err.message}</div></td></tr>`;
    }
  }

  function rowHTML(tx) {
    const negative = /Withdraw|Transfer-Out/i.test(tx.type);
    return `<tr>
      <td class="mono">${fmt.date(tx.created_at)}</td>
      <td><span class="type-chip">${tx.type}</span></td>
      <td class="${negative ? "amt-neg" : "amt-pos"}">${negative ? "−" : "+"}₹${fmt.inr(tx.amount)}</td>
      <td class="mono">₹${fmt.inr(tx.balance_after)}</td>
      <td>${tx.note || ""}</td>
    </tr>`;
  }
});
