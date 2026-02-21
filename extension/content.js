/**
 * DRAFT Protocol — Content Script
 *
 * Detects AI chat interfaces and injects a governance badge.
 * Classifies messages in real-time as the user types.
 */

// ── Site Detection ─────────────────────────────────────────

const SITE_CONFIGS = {
  "chatgpt.com": {
    inputSelector: "#prompt-textarea, [data-testid='composer-text-input']",
    sendSelector: "[data-testid='send-button'], button[aria-label='Send prompt']",
    name: "ChatGPT",
  },
  "chat.openai.com": {
    inputSelector: "#prompt-textarea",
    sendSelector: "[data-testid='send-button']",
    name: "ChatGPT",
  },
  "claude.ai": {
    inputSelector: "[contenteditable='true'].ProseMirror, div[contenteditable='true']",
    sendSelector: "button[aria-label='Send Message'], button[data-testid='send-button']",
    name: "Claude",
  },
  "gemini.google.com": {
    inputSelector: ".ql-editor, rich-textarea .textarea",
    sendSelector: "button.send-button, button[aria-label='Send message']",
    name: "Gemini",
  },
  "copilot.microsoft.com": {
    inputSelector: "#searchbox, textarea[name='searchbox']",
    sendSelector: "button[aria-label='Submit']",
    name: "Copilot",
  },
  "chat.mistral.ai": {
    inputSelector: "textarea",
    sendSelector: "button[type='submit']",
    name: "Mistral",
  },
};

function getSiteConfig() {
  const host = window.location.hostname.replace("www.", "");
  return SITE_CONFIGS[host] || null;
}

// ── Badge Creation ─────────────────────────────────────────

const TIER_STYLES = {
  CASUAL: { bg: "#22c55e", label: "CASUAL" },
  STANDARD: { bg: "#f59e0b", label: "STANDARD" },
  CONSEQUENTIAL: { bg: "#ef4444", label: "CONSEQUENTIAL" },
  REJECTED: { bg: "#6b7280", label: "REJECTED" },
};

let badge = null;
let classifyTimeout = null;
let lastClassified = "";

function createBadge() {
  if (badge) return badge;
  badge = document.createElement("div");
  badge.id = "draft-protocol-badge";
  badge.innerHTML = `
    <div class="draft-badge-inner">
      <span class="draft-badge-icon">⬡</span>
      <span class="draft-badge-tier">DRAFT</span>
      <span class="draft-badge-confidence"></span>
    </div>
  `;
  badge.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "status" }, (result) => {
      if (result && result.ok !== false) {
        showTooltip(result);
      }
    });
  });
  document.body.appendChild(badge);
  return badge;
}

function updateBadge(tier, confidence) {
  if (!badge) createBadge();
  const style = TIER_STYLES[tier] || TIER_STYLES.REJECTED;
  const inner = badge.querySelector(".draft-badge-inner");
  inner.style.borderColor = style.bg;
  badge.querySelector(".draft-badge-tier").textContent = style.label;
  badge.querySelector(".draft-badge-tier").style.color = style.bg;

  const confEl = badge.querySelector(".draft-badge-confidence");
  if (confidence !== undefined) {
    confEl.textContent = `${Math.round(confidence * 100)}%`;
  }
  badge.classList.add("draft-badge-visible");
}

function hideBadge() {
  if (badge) badge.classList.remove("draft-badge-visible");
}

// ── Tooltip ────────────────────────────────────────────────

let tooltip = null;

function showTooltip(data) {
  if (tooltip) tooltip.remove();
  tooltip = document.createElement("div");
  tooltip.id = "draft-protocol-tooltip";

  let html = `<div class="draft-tooltip-header">DRAFT Session</div>`;
  if (data.session_id) {
    html += `<div class="draft-tooltip-row"><b>Tier:</b> ${data.tier || "—"}</div>`;
    html += `<div class="draft-tooltip-row"><b>Status:</b> ${data.status || "—"}</div>`;
    if (data.fields) {
      const confirmed = Object.values(data.fields).filter((f) => f.status === "CONFIRMED").length;
      const total = Object.keys(data.fields).length;
      html += `<div class="draft-tooltip-row"><b>Fields:</b> ${confirmed}/${total} confirmed</div>`;
    }
    if (data.gate) {
      const gateColor = data.gate.status === "GO" ? "#22c55e" : "#ef4444";
      html += `<div class="draft-tooltip-row"><b>Gate:</b> <span style="color:${gateColor}">${data.gate.status}</span></div>`;
    }
  } else {
    html += `<div class="draft-tooltip-row">No active session</div>`;
  }
  html += `<div class="draft-tooltip-footer">Click badge or press Ctrl+Shift+D to open panel</div>`;

  tooltip.innerHTML = html;
  document.body.appendChild(tooltip);

  // Auto-dismiss
  setTimeout(() => {
    if (tooltip) tooltip.remove();
    tooltip = null;
  }, 5000);
}

// ── Input Monitoring ───────────────────────────────────────

function getInputText(input) {
  if (!input) return "";
  // contenteditable divs
  if (input.getAttribute("contenteditable") === "true") {
    return input.innerText || "";
  }
  // textarea / input
  return input.value || "";
}

function onInputChange(input) {
  const text = getInputText(input).trim();
  if (!text || text === lastClassified || text.length < 5) {
    if (!text) hideBadge();
    return;
  }

  // Debounce: classify 500ms after user stops typing
  clearTimeout(classifyTimeout);
  classifyTimeout = setTimeout(() => {
    lastClassified = text;
    chrome.runtime.sendMessage(
      { type: "classify", message: text },
      (result) => {
        if (chrome.runtime.lastError) {
          // Extension context invalidated
          return;
        }
        if (result && result.ok !== false && result.tier) {
          updateBadge(result.tier, result.confidence);
        }
      }
    );
  }, 500);
}

// ── Initialization ─────────────────────────────────────────

function init() {
  const config = getSiteConfig();
  if (!config) return;

  // Check server health first
  chrome.runtime.sendMessage({ type: "health" }, (result) => {
    if (chrome.runtime.lastError || !result?.ok) {
      console.log("DRAFT Protocol: Server not running. Start with: python -m draft_protocol --transport rest");
      return;
    }

    // Wait for chat input to appear (SPAs load dynamically)
    const observer = new MutationObserver(() => {
      const input = document.querySelector(config.inputSelector);
      if (input && !input.dataset.draftMonitored) {
        input.dataset.draftMonitored = "true";
        createBadge();

        // Monitor input changes
        input.addEventListener("input", () => onInputChange(input));
        input.addEventListener("keyup", () => onInputChange(input));

        // For contenteditable
        const mutObs = new MutationObserver(() => onInputChange(input));
        mutObs.observe(input, { childList: true, subtree: true, characterData: true });

        console.log(`DRAFT Protocol: Monitoring ${config.name} input`);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Also check immediately
    const input = document.querySelector(config.inputSelector);
    if (input && !input.dataset.draftMonitored) {
      input.dataset.draftMonitored = "true";
      createBadge();
      input.addEventListener("input", () => onInputChange(input));
      input.addEventListener("keyup", () => onInputChange(input));
      console.log(`DRAFT Protocol: Monitoring ${config.name} input`);
    }
  });
}

// Run on load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
