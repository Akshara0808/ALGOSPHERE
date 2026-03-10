/* ============================================================
   dashboard.js – stats, charts and report download
   ============================================================ */

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const PALETTE = [
  "#4F46E5","#7C3AED","#10B981","#F59E0B","#EF4444",
  "#06B6D4","#84CC16","#F97316","#EC4899","#8B5CF6"
];

const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

// ── Populate year selector ────────────────────────────────────
const yearSel  = document.getElementById("report-year");
const monthSel = document.getElementById("report-month");
if (yearSel) {
  const now = new Date();
  for (let y = now.getFullYear(); y >= now.getFullYear() - 4; y--) {
    const opt = document.createElement("option");
    opt.value = y; opt.textContent = y;
    yearSel.appendChild(opt);
  }
  yearSel.value = now.getFullYear();
  if (monthSel) monthSel.value = now.getMonth() + 1;
}

// ── Load dashboard data ───────────────────────────────────────
async function loadDashboard() {
  const { ok, data } = await apiFetch("/api/dashboard/stats");
  if (!ok) {
    showToast("Failed to load dashboard data", "error");
    return;
  }

  // Stat cards
  document.getElementById("stat-total").textContent    = inrFormatter.format(data.total_spent || 0);
  document.getElementById("stat-receipts").textContent = data.total_receipts ?? 0;
  document.getElementById("stat-category").textContent = data.top_category || "N/A";

  // Category doughnut chart
  const catLabels = data.category_breakdown.map(c => c.category);
  const catValues = data.category_breakdown.map(c => c.total);
  const catCtx    = document.getElementById("categoryChart");
  const noCategory= document.getElementById("no-category-data");

  if (catValues.length === 0) {
    catCtx && (catCtx.style.display = "none");
    noCategory && noCategory.classList.remove("hidden");
  } else {
    noCategory && noCategory.classList.add("hidden");
    new Chart(catCtx, {
      type: "doughnut",
      data: {
        labels: catLabels,
        datasets: [{ data: catValues, backgroundColor: PALETTE, borderWidth: 0 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { color: "#9CA3AF", padding: 12, font: { size: 12 } } },
          tooltip: {
            callbacks: {
              label: ctx => ` ${inrFormatter.format(ctx.parsed)}`
            }
          }
        },
        cutout: "65%",
      }
    });
  }

  // Monthly bar chart
  const mLabels = data.monthly_totals.map(m => {
    const [y, mo] = m.month.split("-");
    return `${MONTHS[parseInt(mo) - 1]} ${y}`;
  });
  const mValues  = data.monthly_totals.map(m => m.total);
  const monCtx   = document.getElementById("monthlyChart");
  const noMonthly= document.getElementById("no-monthly-data");

  if (mValues.length === 0) {
    monCtx && (monCtx.style.display = "none");
    noMonthly && noMonthly.classList.remove("hidden");
  } else {
    noMonthly && noMonthly.classList.add("hidden");
    new Chart(monCtx, {
      type: "bar",
      data: {
        labels: mLabels,
        datasets: [{
          label: "Total (₹)",
          data: mValues,
          backgroundColor: "rgba(79,70,229,.7)",
          borderRadius: 6, borderSkipped: false,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => ` ${inrFormatter.format(ctx.parsed.y)}` } }
        },
        scales: {
          x: { grid: { color: "rgba(255,255,255,.05)" }, ticks: { color: "#9CA3AF" } },
          y: { grid: { color: "rgba(255,255,255,.05)" }, ticks: { color: "#9CA3AF", callback: v => inrFormatter.format(v) } }
        }
      }
    });
  }

  // Recent receipts table
  const tbody = document.getElementById("recent-tbody");
  if (tbody) {
    if (!data.recent_receipts?.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="loading-cell">No receipts yet. <a href="/upload">Upload one!</a></td></tr>`;
    } else {
      tbody.innerHTML = data.recent_receipts.map(r => `
        <tr>
          <td>${r.receipt_date || "—"}</td>
          <td>${escHtml(r.vendor)}</td>
          <td><span class="badge-category">${escHtml(r.category)}</span></td>
          <td>${inrFormatter.format(r.tax || 0)}</td>
          <td><strong>${inrFormatter.format(r.total || 0)}</strong></td>
        </tr>
      `).join("");
    }
  }
}

// ── PDF report download ───────────────────────────────────────
const dlBtn = document.getElementById("download-report-btn");
if (dlBtn) {
  dlBtn.addEventListener("click", async () => {
    const year  = yearSel?.value;
    const month = monthSel?.value;
    if (!year || !month) { showToast("Select a year and month", "error"); return; }

    dlBtn.disabled = true;
    dlBtn.textContent = "⏳ Generating…";

    const token = Auth.getToken();
    const res = await fetch(`/api/reports/monthly?year=${year}&month=${month}`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    dlBtn.disabled = false;
    dlBtn.textContent = "📄 Download PDF";

    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      showToast(j.error || "No receipts for this period", "error");
      return;
    }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url;
    a.download = `ExpenseEye_${year}-${String(month).padStart(2,"0")}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Report downloaded!");
  });
}

function escHtml(str) {
  const d = document.createElement("div");
  d.textContent = str || "";
  return d.innerHTML;
}

loadDashboard();
