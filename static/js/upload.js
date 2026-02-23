/* ============================================================
   upload.js – drag-drop upload, OCR + AI parsing, result display
   ============================================================ */

const dropZone   = document.getElementById("drop-zone");
const fileInput  = document.getElementById("file-input");
const previewArea= document.getElementById("preview-area");
const previewImg = document.getElementById("preview-img");
const previewName= document.getElementById("preview-name");
const changeBtn  = document.getElementById("change-file-btn");
const uploadBtn  = document.getElementById("upload-btn");
const progressEl = document.getElementById("upload-progress");
const progressFill=document.getElementById("progress-fill");
const progressLbl= document.getElementById("progress-label");
const resultCard = document.getElementById("result-card");
const uploadErr  = document.getElementById("upload-error");
const uploadAnother = document.getElementById("upload-another-btn");

let selectedFile = null;
const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

// ── File selection ────────────────────────────────────────────
function onFileSelected(file) {
  if (!file) return;
  const ext = file.name.split(".").pop().toLowerCase();
  if (!["jpg","jpeg","png","pdf"].includes(ext)) {
    showError("Unsupported file type. Please use JPG, PNG or PDF.");
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    showError("File is too large. Maximum size is 16 MB.");
    return;
  }
  selectedFile = file;
  uploadErr.textContent = "";
  dropZone.classList.add("hidden");
  previewArea.classList.remove("hidden");
  previewName.textContent = file.name;

  if (ext !== "pdf") {
    const reader = new FileReader();
    reader.onload = e => { previewImg.src = e.target.result; previewImg.classList.remove("hidden"); };
    reader.readAsDataURL(file);
  } else {
    previewImg.src = "";
    previewImg.classList.add("hidden");
  }
  uploadBtn.disabled = false;
}

// File input change
fileInput.addEventListener("change", () => onFileSelected(fileInput.files[0]));

// Drag-and-drop
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", ()=> dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  onFileSelected(e.dataTransfer.files[0]);
});
// Only open dialog when clicking the drop zone background, not the label/button
// (the label already opens the dialog via its "for" attribute)
dropZone.addEventListener("click", (e) => {
  if (e.target === dropZone || e.target.classList.contains("drop-icon") || e.target.classList.contains("drop-title") || e.target.classList.contains("drop-sub")) {
    fileInput.click();
  }
});

// Change file
if (changeBtn) {
  changeBtn.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    dropZone.classList.remove("hidden");
    previewArea.classList.add("hidden");
    resultCard.classList.add("hidden");
    uploadBtn.disabled = true;
    uploadErr.textContent = "";
  });
}

// Upload another
if (uploadAnother) {
  uploadAnother.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    dropZone.classList.remove("hidden");
    previewArea.classList.add("hidden");
    resultCard.classList.add("hidden");
    progressEl.classList.add("hidden");
    uploadBtn.disabled = true;
    uploadErr.textContent = "";
  });
}

// ── Upload & parse ─────────────────────────────────────────────
uploadBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  uploadErr.textContent = "";
  uploadBtn.disabled = true;
  previewArea.classList.add("hidden");
  progressEl.classList.remove("hidden");
  resultCard.classList.add("hidden");

  // Animated progress simulation
  let pct = 0;
  const steps = [
    { target: 20, label: "Uploading image…" },
    { target: 55, label: "Running OCR extraction…" },
    { target: 85, label: "AI is parsing receipt…" },
    { target: 100, label: "Finalising…" },
  ];
  let stepIdx = 0;

  const interval = setInterval(() => {
    if (pct < steps[stepIdx].target) {
      pct++;
      progressFill.style.width = pct + "%";
      progressLbl.textContent = steps[stepIdx].label;
    } else if (stepIdx < steps.length - 1) {
      stepIdx++;
    }
  }, 50);

  const formData = new FormData();
  formData.append("file", selectedFile);

  const { ok, data } = await apiFetch("/api/receipts/upload", {
    method: "POST",
    body: formData,
    headers: {},   // let browser set multipart boundary
  });

  clearInterval(interval);
  progressFill.style.width = "100%";
  progressEl.classList.add("hidden");

  if (ok) {
    showResult(data.receipt);
    showToast("Receipt processed successfully!");
  } else {
    showError(data.error || "Upload failed. Please try again.");
    dropZone.classList.remove("hidden");
    uploadBtn.disabled = false;
  }
});

// ── Result display ────────────────────────────────────────────
function showResult(r) {
  document.getElementById("res-vendor").textContent   = r.vendor   || "Unknown";
  document.getElementById("res-date").textContent     = r.receipt_date || "—";
  document.getElementById("res-category").textContent = r.category  || "—";
  document.getElementById("res-tax").textContent      = inrFormatter.format(r.tax || 0);
  document.getElementById("res-total").textContent    = inrFormatter.format(r.total || 0);

  const tbody = document.getElementById("items-tbody");
  tbody.innerHTML = (r.items || []).map(it => `
    <tr>
      <td>${escHtml(it.name)}</td>
      <td>${it.qty ?? 1}</td>
      <td>${inrFormatter.format(it.price || 0)}</td>
    </tr>
  `).join("") || `<tr><td colspan="3" style="color:var(--text-dim)">No item details parsed</td></tr>`;

  resultCard.classList.remove("hidden");
}

function showError(msg) {
  uploadErr.textContent = msg;
  uploadBtn.disabled = false;
}

function escHtml(str) {
  const d = document.createElement("div");
  d.textContent = str || "";
  return d.innerHTML;
}
