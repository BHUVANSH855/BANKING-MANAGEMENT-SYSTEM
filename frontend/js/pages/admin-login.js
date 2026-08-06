document.addEventListener("DOMContentLoaded", () => {
  // If already signed in this session, skip straight to the console.
  if (Session.getAdminPin()) {
    window.location.href = "admin_dashboard.html";
    return;
  }

  document.getElementById("adminLoginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const pin = document.getElementById("pin");
    if (!validatePin(pin.value)) { markInvalid(pin, "PIN must be 4–6 digits"); return; }

    Loader.show("Verifying admin PIN…");
    try {
      await BankAPI.adminLogin(pin.value);
      Session.setAdminPin(pin.value);
      Toast.success("Welcome back, admin.");
      setTimeout(() => (window.location.href = "admin_dashboard.html"), 500);
    } catch (err) {
      Toast.error(err.message);
    } finally {
      Loader.hide();
    }
  });
});
