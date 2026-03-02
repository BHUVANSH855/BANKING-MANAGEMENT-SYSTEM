// =====================================
// BankSys Frontend - Central JS File
// =====================================

console.log("BankSys frontend loaded");

// ===============================
// CONFIG
// ===============================
const API_BASE = "http://127.0.0.1:5000/api";

// ===============================
// HELPERS
// ===============================
function showError(msg) {
  alert("❌ " + msg);
}

function showSuccess(msg) {
  alert("✅ " + msg);
}

function validatePin(pin) {
  return /^\d{4,6}$/.test(pin);
}

// ===============================
// API HELPER
// ===============================
async function apiRequest(endpoint, method = "POST", data = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" }
  };

  if (data) options.body = JSON.stringify(data);

  const res = await fetch(API_BASE + endpoint, options);
  const json = await res.json();

  if (!res.ok) {
    throw new Error(json.error || "Request failed");
  }
  return json;
}

// ===============================
// DOM READY
// ===============================
document.addEventListener("DOMContentLoaded", () => {

  /* ---------- THEME (DARK / LIGHT) ---------- */
  const themeBtn = document.getElementById("themeToggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      document.body.classList.toggle("dark");
      themeBtn.textContent = document.body.classList.contains("dark") ? "☀️" : "🌙";
    });
  }

  /* ---------- BASIC FORM VALIDATION ---------- */
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const inputs = form.querySelectorAll("input[required]");
      let valid = true;

      inputs.forEach((input) => {
        if (!input.value.trim()) {
          valid = false;
          input.style.border = "2px solid red";
        } else {
          input.style.border = "1px solid #ccc";
        }
      });

      if (!valid) {
        e.preventDefault();
        showError("Please fill all required fields.");
      }
    });
  });

  /* ---------- LOGIN ---------- */
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const accountId = document.getElementById("account_id").value;
      const pin = document.getElementById("pin").value;

      if (!validatePin(pin)) {
        showError("PIN must be 4–6 digits");
        return;
      }

      try {
        await apiRequest(`/account/${accountId}`, "GET");
        localStorage.setItem("account_id", accountId);
        window.location.href = "dashboard.html";
      } catch (err) {
        showError(err.message);
      }
    });
  }

  /* ---------- DEPOSIT ---------- */
  const depositForm = document.getElementById("depositForm");
  if (depositForm) {
    depositForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      try {
        const accountId = localStorage.getItem("account_id");
        const amount = document.getElementById("amount").value;

        const res = await apiRequest("/deposit", "POST", {
          account_id: accountId,
          amount: amount
        });

        showSuccess("Deposit successful. New balance: ₹" + res.balance);
      } catch (err) {
        showError(err.message);
      }
    });
  }

  /* ---------- WITHDRAW ---------- */
  const withdrawForm = document.getElementById("withdrawForm");
  if (withdrawForm) {
    withdrawForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const pin = document.getElementById("pin").value;
      if (!validatePin(pin)) {
        showError("PIN must be 4–6 digits");
        return;
      }

      try {
        const accountId = localStorage.getItem("account_id");
        const amount = document.getElementById("amount").value;

        const res = await apiRequest("/withdraw", "POST", {
          account_id: accountId,
          amount: amount,
          pin: pin
        });

        showSuccess("Withdraw successful. New balance: ₹" + res.balance);
      } catch (err) {
        showError(err.message);
      }
    });
  }

  /* ---------- TRANSFER ---------- */
  const transferForm = document.getElementById("transferForm");
  if (transferForm) {
    transferForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const pin = document.getElementById("pin").value;
      if (!validatePin(pin)) {
        showError("PIN must be 4–6 digits");
        return;
      }

      try {
        const fromId = localStorage.getItem("account_id");
        const toId = document.getElementById("to_account").value;
        const amount = document.getElementById("amount").value;

        const res = await apiRequest("/transfer", "POST", {
          from_id: fromId,
          to_id: toId,
          amount: amount,
          pin: pin
        });

        showSuccess("Transfer successful. Your balance: ₹" + res.from_balance);
      } catch (err) {
        showError(err.message);
      }
    });
  }

  /* ---------- TRANSACTIONS ---------- */
  const txBody = document.getElementById("txBody");
  if (txBody) {
    const accountId = localStorage.getItem("account_id");
    if (accountId) {
      fetch(API_BASE + `/transactions/${accountId}`)
        .then(res => res.json())
        .then(data => {
          txBody.innerHTML = "";
          if (!data.length) {
            txBody.innerHTML = "<tr><td colspan='5'>No transactions found</td></tr>";
            return;
          }

          data.forEach(tx => {
            const row = document.createElement("tr");
            row.innerHTML = `
              <td>${tx.type}</td>
              <td>₹${tx.amount}</td>
              <td>₹${tx.balance_after}</td>
              <td>${tx.note || ""}</td>
              <td>${tx.created_at}</td>
            `;
            txBody.appendChild(row);
          });
        });
    }
  }

  /* ---------- LOGOUT ---------- */
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("account_id");
      window.location.href = "index.html";
    });
  }

  /* ---------- SESSION SAFETY ---------- */
  window.addEventListener("storage", () => {
    if (!localStorage.getItem("account_id")) {
      window.location.href = "index.html";
    }
  });

  /* ---------- SCROLL REVEAL ---------- */
  const revealCards = document.querySelectorAll(".action-card");
  revealCards.forEach(card => {
    card.style.opacity = "0";
    card.style.transform = "translateY(40px)";
    card.style.transition = "all 0.6s ease";
  });

  const revealOnScroll = () => {
    const triggerPoint = window.innerHeight * 0.85;
    revealCards.forEach(card => {
      if (card.getBoundingClientRect().top < triggerPoint) {
        card.style.opacity = "1";
        card.style.transform = "translateY(0)";
      }
    });
  };

  window.addEventListener("scroll", revealOnScroll);
  revealOnScroll();
});
