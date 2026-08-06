document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("name");
    const email = document.getElementById("email");
    const phone = document.getElementById("phone");
    const deposit = document.getElementById("deposit");
    const pin = document.getElementById("pin");

    let ok = true;
    if (!name.value.trim()) { markInvalid(name, "Enter your full name"); ok = false; }
    if (!/^\S+@\S+\.\S+$/.test(email.value)) { markInvalid(email, "Enter a valid email"); ok = false; }
    if (!/^\d{10}$/.test(phone.value)) { markInvalid(phone, "Enter a 10 digit phone number"); ok = false; }
    if (deposit.value === "" || Number(deposit.value) < 0) { markInvalid(deposit, "Enter a valid opening deposit"); ok = false; }
    if (!validatePin(pin.value)) { markInvalid(pin, "PIN must be 4–6 digits"); ok = false; }
    if (!ok) return;

    const confirmed = await confirmModal({
      title: "Confirm account creation",
      body: `Open a new account for ${name.value.trim()} with an opening deposit of ₹${fmt.inr(deposit.value)}?`,
      confirmLabel: "Yes, create it",
    });
    if (!confirmed) return;

    Loader.show("Opening your account…");
    try {
      // Backend field is `initial_deposit`, not `deposit` — the original
      // form sent the latter and the account was silently opened with ₹0.
      const res = await BankAPI.createAccount({
        name: name.value.trim(),
        email: email.value.trim(),
        phone: phone.value.trim(),
        initial_deposit: deposit.value,
        pin: pin.value,
      });
      Session.setAccountId(res.account_id);
      Toast.success(`Account created! Your account ID is ${res.account_id} — save it.`);
      setTimeout(() => (window.location.href = "dashboard.html"), 1400);
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  });
});
