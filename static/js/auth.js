/* ============================================================
   auth.js – handles login & signup forms
   ============================================================ */

// Redirect if already logged in
if (Auth.isLoggedIn()) window.location.href = "/dashboard";

// ── Helpers ───────────────────────────────────────────────────
function setLoading(btnId, loading) {
  const btn     = document.getElementById(btnId);
  if (!btn) return;
  const text    = btn.querySelector(".btn-text");
  const spinner = btn.querySelector(".btn-spinner");
  btn.disabled  = loading;
  if (text)    text.classList.toggle("hidden", loading);
  if (spinner) spinner.classList.toggle("hidden", !loading);
}

function showError(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg;
}

// ── Login form ─────────────────────────────────────────────────
const loginForm = document.getElementById("login-form");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("login-error", "");
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!email || !password) {
      showError("login-error", "Please fill in all fields.");
      return;
    }

    setLoading("login-btn", true);
    const { ok, data } = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setLoading("login-btn", false);

    if (ok) {
      Auth.setToken(data.token);
      Auth.setUser(data.user);
      showToast("Welcome back, " + (data.user?.name || "User") + "!");
      setTimeout(() => window.location.href = "/dashboard", 600);
    } else {
      showError("login-error", data.error || "Login failed. Please try again.");
    }
  });
}

// ── Signup form ────────────────────────────────────────────────
const signupForm = document.getElementById("signup-form");
if (signupForm) {
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("signup-error", "");
    const name     = document.getElementById("name").value.trim();
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirm  = document.getElementById("confirm").value;

    if (!name || !email || !password || !confirm) {
      showError("signup-error", "Please fill in all fields.");
      return;
    }
    if (password.length < 6) {
      showError("signup-error", "Password must be at least 6 characters.");
      return;
    }
    if (password !== confirm) {
      showError("signup-error", "Passwords do not match.");
      return;
    }

    setLoading("signup-btn", true);
    const { ok, data } = await apiFetch("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    });
    setLoading("signup-btn", false);

    if (ok) {
      Auth.setToken(data.token);
      Auth.setUser(data.user);
      showToast("Account created! Welcome to Expense Eye!");
      setTimeout(() => window.location.href = "/dashboard", 700);
    } else {
      showError("signup-error", data.error || "Registration failed. Please try again.");
    }
  });
}
