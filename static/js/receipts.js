/* ============================================================
   receipts.js – list, filter, detail modal, delete
   ============================================================ */

let allReceipts = [];
let currentReceiptId = null;

const grid       = document.getElementById("receipts-grid");
const loadingEl  = document.getElementById("receipts-loading");
const emptyEl    = document.getElementById("empty-state");
const searchInp  = document.getElementById("search-input");
const catFilter  = document.getElementById("category-filter");
const overlay    = document.getElementById("modal-overlay");
const modalClose = document.getElementById("modal-close");
const deleteBtn  = document.getElementById("modal-delete-btn");
const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

// ── Load receipts ─────────────────────────────────────────────
async function loadReceipts() {
  const { ok, data } = await apiFetch("/api/receipts/");
  if (loadingEl) loadingEl.remove();
  if (!ok) { showToast("Failed to load receipts", "error"); return; }

  allReceipts = data.receipts || [];
  renderReceipts(allReceipts);
}

function renderReceipts(receipts) {
  // Clear existing cards (not loading/empty els)
  grid.querySelectorAll(".receipt-card").forEach(c => c.remove());

  if (!receipts.length) {
    emptyEl && emptyEl.classList.remove("hidden");
    return;
  }
  emptyEl && emptyEl.classList.add("hidden");

  receipts.forEach(r => {
    const card = document.createElement("div");
    card.className = "receipt-card";
    card.dataset.id = r.id;
    card.innerHTML = `
      <div class="receipt-card-vendor">${escHtml(r.vendor)}</div>
      <div class="receipt-card-date">${r.receipt_date || "No date"}</div>
      <span class="badge-category">${escHtml(r.category)}</span>
      <div class="receipt-card-footer">
        <span class="receipt-card-total">${inrFormatter.format(r.total || 0)}</span>
        <span style="color:var(--text-dim);font-size:.8rem">${r.items?.length || 0} item(s)</span>
      </div>
    `;
    card.addEventListener("click", () => openModal(r));
    grid.appendChild(card);
  });
}

// ── Filters ───────────────────────────────────────────────────
function applyFilters() {
  const query = (searchInp?.value || "").toLowerCase();
  const cat   = catFilter?.value || "";
  const filtered = allReceipts.filter(r => {
    const matchSearch = !query || r.vendor.toLowerCase().includes(query) || r.category.toLowerCase().includes(query);
    const matchCat    = !cat   || r.category === cat;
    return matchSearch && matchCat;
  });
  renderReceipts(filtered);
}

searchInp?.addEventListener("input",  applyFilters);
catFilter?.addEventListener("change", applyFilters);

// ── Modal ─────────────────────────────────────────────────────
function openModal(r) {
  currentReceiptId = r.id;
  document.getElementById("modal-vendor").textContent   = r.vendor || "Receipt";
  document.getElementById("modal-date").textContent     = r.receipt_date || "—";
  document.getElementById("modal-category").textContent = r.category || "—";
  document.getElementById("modal-tax").textContent      = inrFormatter.format(r.tax || 0);
  document.getElementById("modal-total").textContent    = inrFormatter.format(r.total || 0);

  const tbody = document.getElementById("modal-items-tbody");
  tbody.innerHTML = (r.items || []).map(it => `
    <tr>
      <td>${escHtml(it.name)}</td>
      <td>${it.qty ?? 1}</td>
      <td>${inrFormatter.format(it.price || 0)}</td>
    </tr>
  `).join("") || `<tr><td colspan="3" style="color:var(--text-dim)">No item details</td></tr>`;

  overlay.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  overlay.classList.add("hidden");
  document.body.style.overflow = "";
  currentReceiptId = null;
}

modalClose?.addEventListener("click", closeModal);
overlay?.addEventListener("click", e => { if (e.target === overlay) closeModal(); });

// ── Delete ────────────────────────────────────────────────────
deleteBtn?.addEventListener("click", async () => {
  if (!currentReceiptId) return;
  if (!confirm("Delete this receipt? This action cannot be undone.")) return;

  deleteBtn.disabled = true;
  deleteBtn.textContent = "Deleting…";

  const { ok } = await apiFetch(`/api/receipts/${currentReceiptId}`, { method: "DELETE" });

  deleteBtn.disabled = false;
  deleteBtn.textContent = "🗑 Delete";

  if (ok) {
    allReceipts = allReceipts.filter(r => r.id !== currentReceiptId);
    closeModal();
    applyFilters();
    showToast("Receipt deleted");
  } else {
    showToast("Failed to delete receipt", "error");
  }
});

function escHtml(str) {
  const d = document.createElement("div");
  d.textContent = str || "";
  return d.innerHTML;
}

loadReceipts();
