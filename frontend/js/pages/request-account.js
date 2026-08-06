document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("requestForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("name");
    const email = document.getElementById("email");
    const phone = document.getElementById("phone");
    const balance = document.getElementById("initial_balance");
    const pin = document.getElementById("pin");

    let ok = true;
    if (!name.value.trim()) { markInvalid(name, "Enter your full name"); ok = false; }
    if (!/^\S+@\S+\.\S+$/.test(email.value)) { markInvalid(email, "Enter a valid email"); ok = false; }
    if (!/^\d{10}$/.test(phone.value)) { markInvalid(phone, "Enter a 10 digit phone number"); ok = false; }
    if (balance.value === "" || Number(balance.value) < 0) { markInvalid(balance, "Enter a valid opening deposit"); ok = false; }
    if (!validatePin(pin.value)) { markInvalid(pin, "PIN must be 4–6 digits"); ok = false; }
    if (!ok) return;

    Loader.show("Submitting request…");
    try {
      const res = await BankAPI.createAccount({
        name: name.value.trim(),
        email: email.value.trim(),
        phone: phone.value.trim(),
        initial_deposit: balance.value,
        pin: pin.value,
      });
      Session.setAccountId(res.account_id);
      Toast.success(`Approved instantly — your account ID is ${res.account_id}.`);
      setTimeout(() => (window.location.href = "dashboard.html"), 1400);
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  });
});
