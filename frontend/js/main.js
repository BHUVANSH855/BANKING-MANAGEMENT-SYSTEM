/* ==========================================================================
   BankSys — shared UI behaviors (runs on every page)
   ========================================================================== */

/* ---------------- VAULT DIAL (loader svg, injected once) ---------------- */
function vaultDialSVG() {
  return `<div class="vault-dial"><svg viewBox="0 0 56 56" fill="none">
    <circle cx="28" cy="28" r="24" stroke-width="2" stroke-opacity="0.25"/>
    <circle cx="28" cy="28" r="24" stroke-width="3" stroke-linecap="round"
      stroke-dasharray="40 110"/>
  </svg></div>`;
}

/* ---------------- LOADER ---------------- */
const Loader = (() => {
  let el;
  function ensure() {
    if (el) return el;
    el = document.createElement("div");
    el.className = "loader-overlay";
    el.innerHTML = `${vaultDialSVG()}<p id="loaderMsg">Working…</p>`;
    document.body.appendChild(el);
    return el;
  }
  return {
    show(msg = "Working…") {
      const node = ensure();
      node.querySelector("#loaderMsg").textContent = msg;
      node.classList.add("open");
    },
    hide() { if (el) el.classList.remove("open"); },
  };
})();

/* ---------------- TOAST ---------------- */
const Toast = (() => {
  function stack() {
    let s = document.getElementById("toastStack");
    if (!s) {
      s = document.createElement("div");
      s.id = "toastStack";
      document.body.appendChild(s);
    }
    return s;
  }
  function show(message, type = "info", timeout = 4200) {
    const icon = { success: "fa-circle-check", error: "fa-triangle-exclamation", info: "fa-circle-info" }[type];
    const t = document.createElement("div");
    t.className = `toast ${type}`;
    t.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;
    stack().appendChild(t);
    setTimeout(() => {
      t.classList.add("hide");
      setTimeout(() => t.remove(), 350);
    }, timeout);
  }
  return {
    success: (m) => show(m, "success"),
    error: (m) => show(m, "error"),
    info: (m) => show(m, "info"),
  };
})();

/* ---------------- CONFIRM MODAL (promise-based, replaces confirm()) ---------------- */
function confirmModal({ title = "Confirm action", body = "Are you sure?", confirmLabel = "Yes, continue", danger = false } = {}) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal-box">
        <h3>${title}</h3>
        <p>${body}</p>
        <div class="modal-actions">
          <button class="btn secondary" data-act="cancel">Cancel</button>
          <button class="btn ${danger ? "danger" : "primary"}" data-act="ok">${confirmLabel}</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add("open"));

    function close(result) {
      overlay.classList.remove("open");
      setTimeout(() => overlay.remove(), 300);
      resolve(result);
    }
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close(false);
      const act = e.target.closest("[data-act]");
      if (act) close(act.dataset.act === "ok");
    });
    document.addEventListener("keydown", function esc(e) {
      if (e.key === "Escape") { close(false); document.removeEventListener("keydown", esc); }
    });
  });
}

/* ---------------- THEME TOGGLE ---------------- */
function initTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "paper") document.body.classList.add("theme-paper");
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    updateThemeIcon(btn);
    btn.addEventListener("click", () => {
      document.body.classList.toggle("theme-paper");
      localStorage.setItem("theme", document.body.classList.contains("theme-paper") ? "paper" : "vault");
      updateThemeIcon(btn);
    });
  });
}
function updateThemeIcon(btn) {
  btn.innerHTML = document.body.classList.contains("theme-paper")
    ? '<i class="fa-solid fa-moon"></i>'
    : '<i class="fa-solid fa-sun"></i>';
}

/* ---------------- MOBILE NAV ---------------- */
function initNav() {
  const burger = document.querySelector("[data-nav-burger]");
  const links = document.querySelector("[data-nav-links]");
  if (!burger || !links) return;
  burger.addEventListener("click", () => links.classList.toggle("open"));
  links.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => links.classList.remove("open")));
}

/* ---------------- BUTTON RIPPLE ---------------- */
function initRipple() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn");
    if (!btn) return;
    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement("span");
    const size = Math.max(rect.width, rect.height);
    ripple.className = "ripple";
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 650);
  });
}

/* ---------------- SCROLL REVEAL ---------------- */
function initReveal() {
  const items = document.querySelectorAll(".reveal");
  if (!items.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  items.forEach((el) => io.observe(el));
}

/* ---------------- COUNT-UP NUMBER ---------------- */
function countUp(el, to, { duration = 900, prefix = "", decimals = 2 } = {}) {
  const from = 0;
  const start = performance.now();
  function tick(now) {
    const p = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    const val = from + (to - from) * eased;
    el.textContent = prefix + val.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ---------------- INLINE FORM VALIDATION ---------------- */
function markInvalid(input, message) {
  const field = input.closest(".field") || input.parentElement;
  input.classList.add("invalid");
  let msg = field.querySelector(".error-msg");
  if (!msg) {
    msg = document.createElement("small");
    msg.className = "error-msg";
    field.appendChild(msg);
  }
  msg.textContent = message;
  field.classList.add("has-error");
}
function clearInvalid(input) {
  const field = input.closest(".field") || input.parentElement;
  input.classList.remove("invalid");
  field.classList.remove("has-error");
}
document.addEventListener("input", (e) => {
  if (e.target.matches(".field input")) clearInvalid(e.target);
});

/* ---------------- BOOT ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initNav();
  initRipple();
  initReveal();
  const grain = document.createElement("div");
  grain.className = "grain";
  document.body.appendChild(grain);
});
