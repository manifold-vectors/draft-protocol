/**
 * DRAFT Protocol — Popup Controller
 */

const $ = (sel) => document.querySelector(sel);

// ── Server Health ──────────────────────────────────────────

async function checkServer() {
  const status = $("#serverStatus");
  chrome.runtime.sendMessage({ type: "health" }, (result) => {
    if (chrome.runtime.lastError || !result?.ok) {
      status.className = "header-status offline";
      status.title = "Server offline";
    } else {
      status.className = "header-status online";
      status.title = "Server online";
    }
  });
}

// ── Classify ───────────────────────────────────────────────

$("#classifyBtn").addEventListener("click", async () => {
  const input = $("#messageInput");
  const message = input.value.trim();
  if (!message) return;

  const btn = $("#classifyBtn");
  const result = $("#classifyResult");
  const error = $("#errorMsg");

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Classifying...';
  result.classList.remove("visible");
  error.classList.remove("visible");

  chrome.runtime.sendMessage({ type: "classify", message }, (resp) => {
    btn.disabled = false;
    btn.textContent = "Classify";

    if (chrome.runtime.lastError || !resp || resp.ok === false) {
      error.textContent = resp?.error || "Failed to connect to DRAFT server";
      error.classList.add("visible");
      return;
    }

    $("#tierLabel").textContent = resp.tier;
    $("#tierLabel").className = `tier-label tier-${resp.tier}`;
    $("#reasoning").textContent = resp.reasoning || "";
    $("#confidence").textContent = resp.confidence !== undefined
      ? `Confidence: ${Math.round(resp.confidence * 100)}%`
      : "";
    result.classList.add("visible");
  });
});

// Allow Enter to classify
$("#messageInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("#classifyBtn").click();
  }
});

// ── Active Session ─────────────────────────────────────────

function renderSession(data) {
  const section = $("#sessionSection");
  const info = $("#sessionInfo");

  if (!data || data.active === false || !data.session_id) {
    section.style.display = "none";
    return;
  }

  section.style.display = "block";

  let html = "";
  html += `<div class="session-row"><span class="session-label">Tier</span><span class="tier-label tier-${data.tier}">${data.tier}</span></div>`;
  html += `<div class="session-row"><span class="session-label">Status</span><span class="session-value">${data.status || "ACTIVE"}</span></div>`;

  if (data.fields) {
    const counts = { CONFIRMED: 0, SATISFIED: 0, MISSING: 0, AMBIGUOUS: 0 };
    for (const f of Object.values(data.fields)) {
      const s = f.status || "MISSING";
      counts[s] = (counts[s] || 0) + 1;
    }
    const total = Object.keys(data.fields).length;
    const done = counts.CONFIRMED + counts.SATISFIED;
    html += `<div class="session-row"><span class="session-label">Fields</span><span class="session-value">${done}/${total}</span></div>`;
  }

  if (data.gate) {
    html += `<div class="session-row"><span class="session-label">Gate</span><span class="gate-badge gate-${data.gate.status}">${data.gate.status}</span></div>`;
  }

  info.innerHTML = html;
}

function loadSession() {
  chrome.runtime.sendMessage({ type: "status" }, (resp) => {
    if (chrome.runtime.lastError) return;
    renderSession(resp);
  });
}

// ── Init ───────────────────────────────────────────────────

checkServer();
loadSession();
