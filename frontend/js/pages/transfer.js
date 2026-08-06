document.addEventListener("DOMContentLoaded", () => {
  const fromInput = document.getElementById("from_account");
  const savedId = Session.getAccountId();
  if (savedId) fromInput.value = savedId;

  document.getElementById("transferForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const to = document.getElementById("to_account");
    const amount = document.getElementById("amount");
    const pin = document.getElementById("pin");
    let ok = true;
    if (!fromInput.value) { markInvalid(fromInput, "Enter the sender's account ID"); ok = false; }
    if (!to.value) { markInvalid(to, "Enter the recipient's account ID"); ok = false; }
    if (fromInput.value && to.value && fromInput.value === to.value) { markInvalid(to, "Can't transfer to the same account"); ok = false; }
    if (!validateAmount(amount.value)) { markInvalid(amount, "Enter an amount greater than 0"); ok = false; }
    if (!validatePin(pin.value)) { markInvalid(pin, "PIN must be 4–6 digits"); ok = false; }
    if (!ok) return;

    Loader.show("Transferring…");
    try {
      // Backend expects { from_id, to_id, amount, pin } — the original
      // markup posted from_account/to_account, which the API silently
      // ignored (both fields defaulted to 0 and the transfer failed).
      const res = await BankAPI.transfer(fromInput.value, to.value, amount.value, pin.value);
      Toast.success(`Transfer complete. Your balance is now ₹${fmt.inr(res.from_balance)}.`);
      to.value = ""; amount.value = ""; pin.value = "";
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  });
});
