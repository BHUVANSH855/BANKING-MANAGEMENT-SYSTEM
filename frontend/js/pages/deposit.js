document.addEventListener("DOMContentLoaded", () => {
  const accIdInput = document.getElementById("account_id");
  const savedId = Session.getAccountId();
  if (savedId) accIdInput.value = savedId;

  document.getElementById("depositForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const amount = document.getElementById("amount");
    let ok = true;
    if (!accIdInput.value) { markInvalid(accIdInput, "Enter an account ID"); ok = false; }
    if (!validateAmount(amount.value)) { markInvalid(amount, "Enter an amount greater than 0"); ok = false; }
    if (!ok) return;

    Loader.show("Depositing…");
    try {
      const res = await BankAPI.deposit(accIdInput.value, amount.value);
      Toast.success(`Deposit successful. New balance ₹${fmt.inr(res.balance)}.`);
      amount.value = "";
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  });
});
