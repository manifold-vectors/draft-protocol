/**
 * DRAFT Protocol — Background Service Worker
 *
 * Manages communication between content scripts and the local DRAFT REST API.
 * Handles server health checks, session state, and badge updates.
 */

const DEFAULT_API = "http://127.0.0.1:8420";

// ── API Communication ──────────────────────────────────────

async function getApiBase() {
  const result = await chrome.storage.local.get("apiBase");
  return result.apiBase || DEFAULT_API;
}

async function apiCall(endpoint, method = "GET", body = null) {
  const base = await getApiBase();
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);

  try {
    const resp = await fetch(`${base}${endpoint}`, opts);
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: resp.statusText }));
      return { error: err.error || resp.statusText, ok: false };
    }
    const data = await resp.json();
    return { ...data, ok: true };
  } catch (e) {
    return { error: "DRAFT server unreachable. Start it with: python -m draft_protocol --transport rest", ok: false };
  }
}

// ── Badge Management ───────────────────────────────────────

const TIER_COLORS = {
  CASUAL: "#22c55e",       // green
  STANDARD: "#f59e0b",     // amber
  CONSEQUENTIAL: "#ef4444", // red
  REJECTED: "#6b7280",     // gray
};

const TIER_BADGES = {
  CASUAL: "C",
  STANDARD: "S",
  CONSEQUENTIAL: "!",
  REJECTED: "X",
};

async function updateBadge(tier, tabId) {
  const color = TIER_COLORS[tier] || "#6b7280";
  const text = TIER_BADGES[tier] || "?";
  await chrome.action.setBadgeBackgroundColor({ color, tabId });
  await chrome.action.setBadgeText({ text, tabId });
}

async function clearBadge(tabId) {
  await chrome.action.setBadgeText({ text: "", tabId });
}

// ── Health Check ───────────────────────────────────────────

async function checkHealth() {
  const result = await apiCall("/health");
  return result.ok && result.status === "ok";
}

// ── Message Handler ────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const tabId = sender.tab?.id;

  if (msg.type === "classify") {
    apiCall("/classify", "POST", { message: msg.message }).then((result) => {
      if (result.ok && result.tier) {
        updateBadge(result.tier, tabId);
      }
      sendResponse(result);
    });
    return true; // async
  }

  if (msg.type === "create_session") {
    apiCall("/session", "POST", { message: msg.message }).then((result) => {
      if (result.ok && result.tier) {
        updateBadge(result.tier, tabId);
      }
      sendResponse(result);
    });
    return true;
  }

  if (msg.type === "map") {
    apiCall("/map", "POST", {
      session_id: msg.session_id,
      context: msg.context,
    }).then(sendResponse);
    return true;
  }

  if (msg.type === "confirm") {
    apiCall("/confirm", "POST", {
      session_id: msg.session_id,
      field_key: msg.field_key,
      value: msg.value,
    }).then(sendResponse);
    return true;
  }

  if (msg.type === "gate") {
    apiCall("/gate", "POST", { session_id: msg.session_id }).then(sendResponse);
    return true;
  }

  if (msg.type === "status") {
    apiCall("/status").then(sendResponse);
    return true;
  }

  if (msg.type === "health") {
    checkHealth().then((ok) => sendResponse({ ok }));
    return true;
  }

  if (msg.type === "clear_badge") {
    clearBadge(tabId);
    sendResponse({ ok: true });
    return false;
  }
});

// ── Side Panel ─────────────────────────────────────────────

chrome.action.onClicked.addListener(async (tab) => {
  await chrome.sidePanel.open({ tabId: tab.id });
});

// ── Startup Health Check ───────────────────────────────────

chrome.runtime.onInstalled.addListener(async () => {
  const healthy = await checkHealth();
  if (!healthy) {
    console.log("DRAFT Protocol: Server not running. Start with: python -m draft_protocol --transport rest");
  }
});
