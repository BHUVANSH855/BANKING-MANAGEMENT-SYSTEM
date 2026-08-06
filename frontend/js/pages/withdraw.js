document.addEventListener("DOMContentLoaded", () => {
  const accIdInput = document.getElementById("account_id");
  const savedId = Session.getAccountId();
  if (savedId) accIdInput.value = savedId;

  document.getElementById("withdrawForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const amount = document.getElementById("amount");
    const pin = document.getElementById("pin");
    let ok = true;
    if (!accIdInput.value) { markInvalid(accIdInput, "Enter an account ID"); ok = false; }
    if (!validateAmount(amount.value)) { markInvalid(amount, "Enter an amount greater than 0"); ok = false; }
    if (!validatePin(pin.value)) { markInvalid(pin, "PIN must be 4–6 digits"); ok = false; }
    if (!ok) return;

    Loader.show("Withdrawing…");
    try {
      const res = await BankAPI.withdraw(accIdInput.value, amount.value, pin.value);
      Toast.success(`Withdrawal successful. New balance ₹${fmt.inr(res.balance)}.`);
      amount.value = ""; pin.value = "";
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  });
});
