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

  // Auto-logout and redirect on expired / invalid token (but not for password change failures)
  if (res.status === 401 && !path.includes("/change-password")) {
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
  
  // Update user name display
  const userNameEl = document.getElementById("user-name");
  if (userNameEl && loggedIn) {
    const user = Auth.getUser();
    if (user && user.name) {
      userNameEl.textContent = `Welcome, ${user.name}`;
      userNameEl.style.display = "";
    }
  }

  // Update profile dropdown info
  const profileName = document.getElementById("profile-name");
  const profileEmail = document.getElementById("profile-email");
  if (loggedIn) {
    const user = Auth.getUser();
    if (user) {
      if (profileName) profileName.textContent = user.name || "User";
      if (profileEmail) profileEmail.textContent = user.email || "";
    }
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

// ── Profile Dropdown ───────────────────────────────────────────
const profileBtn = document.getElementById("profile-btn");
const profileDropdown = document.getElementById("profile-dropdown");

if (profileBtn && profileDropdown) {
  profileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    profileDropdown.classList.toggle("show");
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!profileDropdown.contains(e.target) && !profileBtn.contains(e.target)) {
      profileDropdown.classList.remove("show");
    }
  });
}

// Logout from dropdown
const logoutDropdownBtn = document.getElementById("logout-dropdown-btn");
if (logoutDropdownBtn) {
  logoutDropdownBtn.addEventListener("click", (e) => {
    e.preventDefault();
    Auth.clear();
    showToast("Logged out successfully");
    setTimeout(() => window.location.href = "/", 800);
  });
}

// ── Change Password Modal ──────────────────────────────────────
const passwordModal = document.getElementById("password-modal");
const passwordModalOverlay = document.getElementById("password-modal-overlay");
const passwordModalClose = document.getElementById("password-modal-close");
const changePasswordBtn = document.getElementById("change-password-btn");
const passwordCancelBtn = document.getElementById("password-cancel-btn");
const changePasswordForm = document.getElementById("change-password-form");

function openPasswordModal() {
  if (passwordModal) {
    passwordModal.classList.add("show");
    document.getElementById("current-password").value = "";
    document.getElementById("new-password").value = "";
    document.getElementById("confirm-new-password").value = "";
    document.getElementById("password-error").textContent = "";
    if (profileDropdown) profileDropdown.classList.remove("show");
  }
}

function closePasswordModal() {
  if (passwordModal) passwordModal.classList.remove("show");
}

if (changePasswordBtn) {
  changePasswordBtn.addEventListener("click", openPasswordModal);
}

if (passwordModalClose) {
  passwordModalClose.addEventListener("click", closePasswordModal);
}

if (passwordCancelBtn) {
  passwordCancelBtn.addEventListener("click", closePasswordModal);
}

if (passwordModalOverlay) {
  passwordModalOverlay.addEventListener("click", closePasswordModal);
}

if (changePasswordForm) {
  changePasswordForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("password-error");
    errorEl.textContent = "";

    const currentPassword = document.getElementById("current-password").value;
    const newPassword = document.getElementById("new-password").value;
    const confirmPassword = document.getElementById("confirm-new-password").value;

    if (!currentPassword || !newPassword || !confirmPassword) {
      errorEl.textContent = "Please fill in all fields.";
      return;
    }

    if (newPassword.length < 6) {
      errorEl.textContent = "New password must be at least 6 characters.";
      return;
    }

    if (newPassword !== confirmPassword) {
      errorEl.textContent = "New passwords do not match.";
      return;
    }

    const submitBtn = document.getElementById("password-submit-btn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnSpinner = submitBtn.querySelector(".btn-spinner");
    
    submitBtn.disabled = true;
    if (btnText) btnText.classList.add("hidden");
    if (btnSpinner) btnSpinner.classList.remove("hidden");

    const { ok, data } = await apiFetch("/api/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        old_password: currentPassword,
        new_password: newPassword,
      }),
    });

    submitBtn.disabled = false;
    if (btnText) btnText.classList.remove("hidden");
    if (btnSpinner) btnSpinner.classList.add("hidden");

    if (ok) {
      showToast("Password changed successfully!");
      closePasswordModal();
    } else {
      errorEl.textContent = data.error || "Failed to change password.";
    }
  });
}

updateNav();

// Expose globals
window.Auth = Auth;
window.apiFetch = apiFetch;
window.showToast = showToast;
