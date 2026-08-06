/* ---------------- HOME / LOGIN ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const accountId = document.getElementById("account_id");
    const pin = document.getElementById("pin");

    let ok = true;
    if (!accountId.value) { markInvalid(accountId, "Enter your account ID"); ok = false; }
    if (!validatePin(pin.value)) { markInvalid(pin, "PIN must be 4–6 digits"); ok = false; }
    if (!ok) return;

    Loader.show("Verifying account…");
    try {
      // Note: the backend does not expose a dedicated login endpoint that
      // checks the PIN — /api/account/:id only confirms the account exists.
      // The PIN is verified server-side on every sensitive action
      // (withdraw/transfer) instead. We keep the PIN in memory only for
      // this tab session so those forms can be pre-filled.
      const acc = await BankAPI.getAccount(accountId.value);
      Session.setAccountId(acc.account_id);
      Toast.success(`Welcome back, ${acc.name.split(" ")[0]}.`);
      setTimeout(() => (window.location.href = "dashboard.html"), 500);
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  });
});
