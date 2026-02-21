/**
 * DRAFT Protocol — Side Panel Controller
 *
 * Full DRAFT workflow: Create → Map → Elicit → Confirm → Gate
 */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

let currentSessionId = null;

// ── API Helper ─────────────────────────────────────────────

function send(type, data = {}) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type, ...data }, (resp) => {
      if (chrome.runtime.lastError) {
        resolve({ ok: false, error: chrome.runtime.lastError.message });
      } else {
        resolve(resp || { ok: false, error: "No response" });
      }
    });
  });
}

// ── Server Status ──────────────────────────────────────────

async function checkServer() {
  const result = await send("health");
  const el = $("#serverStatusText");
  if (result.ok) {
    el.innerHTML = '<span class="status-dot dot-green"></span>Connected';
  } else {
    el.innerHTML = '<span class="status-dot dot-red"></span>Offline — run: <code>python -m draft_protocol --transport rest</code>';
  }
}

// ── Create Session ─────────────────────────────────────────

$("#createBtn").addEventListener("click", async () => {
  const message = $("#intentInput").value.trim();
  if (!message) return;

  const btn = $("#createBtn");
  btn.disabled = true;
  btn.textContent = "Creating...";
  $("#createError").classList.add("hidden");

  const result = await send("create_session", { message });

  btn.disabled = false;
  btn.textContent = "Start DRAFT Session";

  if (!result.ok || result.error) {
    $("#createError").textContent = result.error || "Failed to create session";
    $("#createError").classList.remove("hidden");
    return;
  }

  currentSessionId = result.session_id;

  // Show session info
  $("#sessionMeta").innerHTML = `
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
      <span class="tier tier-${result.tier}">${result.tier}</span>
      <span style="font-size:11px;color:var(--text-dim)">${result.reasoning}</span>
    </div>
    <div style="font-size:10px;color:var(--text-dim);font-family:monospace">${result.session_id}</div>
  `;
  $("#sessionCard").classList.remove("hidden");

  // Auto-map dimensions
  await mapDimensions(message);
});

// ── Map Dimensions ─────────────────────────────────────────

async function mapDimensions(context) {
  if (!currentSessionId) return;

  const result = await send("map", { session_id: currentSessionId, context });
  if (!result.ok || result.error) return;

  renderFields(result);
  $("#fieldsCard").classList.remove("hidden");
}

function renderFields(mapResult) {
  const container = $("#fieldsContainer");
  container.innerHTML = "";

  // mapResult has dimension keys like D, R, A, F, T with nested fields
  const fields = mapResult.fields || mapResult;

  for (const [key, field] of Object.entries(fields)) {
    if (typeof field !== "object" || !field.status) continue;
    const statusClass = `status-${field.status}`;
    const row = document.createElement("div");
    row.className = "field-row";
    row.innerHTML = `
      <span>
        <span class="field-key">${key}</span>
        <span style="color:var(--text-dim);font-size:11px;margin-left:6px">${field.label || ""}</span>
      </span>
      <span class="field-status ${statusClass}">${field.status}</span>
    `;
    container.appendChild(row);
  }
}

// ── Elicitation ────────────────────────────────────────────

$("#elicitBtn").addEventListener("click", async () => {
  if (!currentSessionId) return;

  const btn = $("#elicitBtn");
  btn.disabled = true;
  btn.textContent = "Loading...";

  const result = await send("map", {
    session_id: currentSessionId,
    context: "elicit",
  });

  // Get elicitation questions via classify since we don't have a direct elicit message type yet
  // Actually we need the elicit endpoint
  const elicitResult = await new Promise((resolve) => {
    const base = "http://127.0.0.1:8420";
    fetch(`${base}/elicit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: currentSessionId }),
    })
      .then((r) => r.json())
      .then(resolve)
      .catch(() => resolve({ questions: [] }));
  });

  btn.disabled = false;
  btn.textContent = "Get Questions";

  const questions = elicitResult.questions || [];
  if (questions.length === 0) {
    $("#questionsCard").classList.add("hidden");
    return;
  }

  const container = $("#questionsContainer");
  container.innerHTML = "";

  for (const q of questions) {
    const card = document.createElement("div");
    card.className = "question-card";
    card.innerHTML = `
      <div class="question-field">${q.field}</div>
      <div class="question-text">${q.question}</div>
      <div style="display:flex;gap:6px;margin-top:6px">
        <input type="text" class="confirm-input" data-field="${q.field}"
               placeholder="Your answer..." style="flex:1">
        <button class="btn btn-sm btn-primary confirm-btn" data-field="${q.field}">Confirm</button>
      </div>
    `;
    container.appendChild(card);
  }

  // Bind confirm buttons
  container.querySelectorAll(".confirm-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const field = btn.dataset.field;
      const input = container.querySelector(`.confirm-input[data-field="${field}"]`);
      const value = input.value.trim();
      if (!value) return;

      btn.disabled = true;
      const result = await send("confirm", {
        session_id: currentSessionId,
        field_key: field,
        value,
      });
      btn.disabled = false;

      if (result.ok !== false && !result.error) {
        btn.textContent = "✓";
        btn.style.background = "var(--green)";
        input.disabled = true;
      }
    });
  });

  $("#questionsCard").classList.remove("hidden");
});

// ── Gate Check ─────────────────────────────────────────────

$("#gateBtn").addEventListener("click", async () => {
  if (!currentSessionId) return;

  const btn = $("#gateBtn");
  btn.disabled = true;
  btn.textContent = "Checking...";

  const result = await send("gate", { session_id: currentSessionId });

  btn.disabled = false;
  btn.textContent = "Check Gate";

  const container = $("#gateResult");
  if (result.ok !== false && !result.error) {
    const status = result.status || "NO-GO";
    const isGo = status === "GO";
    container.innerHTML = `
      <div style="text-align:center;padding:16px">
        <span class="gate gate-${status}" style="font-size:16px;padding:6px 20px">${status}</span>
        ${isGo
          ? '<div class="success" style="margin-top:12px">All fields confirmed. Safe to proceed.</div>'
          : `<div class="error" style="margin-top:12px">${(result.blockers || []).join(", ") || "Missing field confirmations"}</div>`
        }
      </div>
    `;
  } else {
    container.innerHTML = `<div class="error">${result.error || "Gate check failed"}</div>`;
  }

  $("#gateCard").classList.remove("hidden");
});

// ── Load Existing Session ──────────────────────────────────

async function loadExisting() {
  const result = await send("status");
  if (result.ok !== false && result.session_id) {
    currentSessionId = result.session_id;
    $("#sessionMeta").innerHTML = `
      <div style="display:flex;gap:8px;align-items:center">
        <span class="tier tier-${result.tier}">${result.tier}</span>
        <span style="font-size:10px;color:var(--text-dim);font-family:monospace">${result.session_id}</span>
      </div>
    `;
    $("#sessionCard").classList.remove("hidden");

    if (result.fields) {
      renderFields(result);
      $("#fieldsCard").classList.remove("hidden");
    }
  }
}

// ── Init ───────────────────────────────────────────────────

checkServer();
loadExisting();
