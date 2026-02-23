/* ============================================================
   main.js – shared helpers loaded on every page
   ============================================================ */

const API = "";   // same origin – Flask serves both HTML and API

// ── Token helpers ──────────────────────────────────────────────
const Auth = {
  getToken:  ()  => localStorage.getItem("as_token"),
  setToken:  (t) => localStorage.setItem("as_token", t),
  setUser:   (u) => localStorage.setItem("as_user", JSON.stringify(u)),
  getUser:   ()  => { try { return JSON.parse(localStorage.getItem("as_user")); } catch { return null; } },
  clear:     ()  => { localStorage.removeItem("as_token"); localStorage.removeItem("as_user"); },
  isLoggedIn:()  => !!localStorage.getItem("as_token"),
};

// ── Fetch wrapper ──────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = Auth.getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(API + path, { ...options, headers });
  const json = await res.json().catch(() => ({}));

  // Auto-logout and redirect on expired / invalid token
  if (res.status === 401) {
    Auth.clear();
    showToast("Session expired. Please log in again.", "error");
    setTimeout(() => window.location.href = "/login", 1500);
  }

  return { ok: res.ok, status: res.status, data: json };
}

// ── Toast ──────────────────────────────────────────────────────
const toast = document.getElementById("toast");
let toastTimer;
function showToast(msg, type = "success") {
  if (!toast) return;
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.className = "toast"; }, 3500);
}

// ── Nav state ──────────────────────────────────────────────────
function updateNav() {
  const loggedIn = Auth.isLoggedIn();
  document.querySelectorAll("[data-auth]").forEach(el => {
    el.style.display = loggedIn ? "" : "none";
  });
  document.querySelectorAll("[data-guest]").forEach(el => {
    el.style.display = loggedIn ? "none" : "";
  });
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.style.display = loggedIn ? "" : "none";
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      Auth.clear();
      showToast("Logged out successfully");
      setTimeout(() => window.location.href = "/", 800);
    });
  }
}

// ── Hamburger ──────────────────────────────────────────────────
const hamburger = document.getElementById("hamburger");
const navLinks  = document.getElementById("nav-links");
if (hamburger && navLinks) {
  hamburger.addEventListener("click", () => navLinks.classList.toggle("open"));
}

// ── Guard protected pages ─────────────────────────────────────
const PROTECTED = ["/dashboard", "/upload", "/receipts"];
if (PROTECTED.includes(window.location.pathname) && !Auth.isLoggedIn()) {
  window.location.href = "/login";
}

// ── Toggle password visibility ─────────────────────────────────
document.querySelectorAll(".toggle-pw").forEach(btn => {
  btn.addEventListener("click", () => {
    const input = document.getElementById(btn.dataset.target);
    if (input) input.type = input.type === "password" ? "text" : "password";
  });
});

updateNav();

// Expose globals
window.Auth = Auth;
window.apiFetch = apiFetch;
window.showToast = showToast;
