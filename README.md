# DRAFT Protocol

[![CI](https://github.com/manifold-vectors/draft-protocol/actions/workflows/ci.yml/badge.svg)](https://github.com/manifold-vectors/draft-protocol/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green.svg)](https://github.com/manifold-vectors/draft-protocol/blob/main/LICENSE)
[![Typed](https://img.shields.io/badge/typing-typed-blue.svg)](https://peps.python.org/pep-0561/)

**Every AI guardrail watches what already went wrong. DRAFT prevents it from going wrong in the first place.**

DRAFT (Define, Rules, Artifacts, Flex, Test) is a structured intake governance protocol that forces AI agents to confirm they understand your intent before they act. Five dimensions. Three tiers. One rule: questions come before answers.

```bash
pip install draft-protocol
```

| | Output Guardrails | DRAFT Protocol |
|---|---|---|
| **When it acts** | After the LLM responds | Before the LLM acts |
| **What it checks** | Toxicity, format, policy | Intent, scope, assumptions |
| **Failure mode** | Catches bad output, wastes the call | Prevents bad calls entirely |
| **Evidence basis** | Synthetic benchmarks | 50+ real governed sessions |
| **Complementary?** | Yes | Yes — use both for defense-in-depth |

## The Problem

AI agents are getting powerful. They can write code, manage files, query databases, deploy infrastructure. But they all share the same failure mode: **they act on what they think you meant, not what you actually meant.**

The result? Scope creep, misunderstood requirements, wasted work, and sometimes real damage — all because no one verified intent before execution.

Current solutions focus on *output* safety (content filtering, guardrails). Almost nobody governs the *intake* — the moment where intent is captured and interpreted.

## How DRAFT Works

DRAFT maps every request across **five dimensions**:

| Dimension | Question | Why It Matters |
|-----------|----------|----------------|
| **D**efine | What exactly are we building? | Prevents vague starts |
| **R**ules | Who decides? What's forbidden? | Prevents authority drift |
| **A**rtifacts | What goes in? What comes out? | Prevents garbage-in/garbage-out |
| **F**lex | What can change? What can't? | Prevents scope creep |
| **T**est | How do we know it worked? | Prevents "done" without evidence |

Each field is labeled **SATISFIED**, **AMBIGUOUS**, or **MISSING**. Ambiguous and missing fields generate targeted questions. The **confirmation gate** blocks execution until all applicable fields are confirmed by the human.

### Three Tiers

Not every message needs the same scrutiny:

- **CASUAL** — "What's the weather?" → Internal mapping only. No visible ceremony.
- **STANDARD** — "Build a REST API" → Full pipeline. Questions for gaps. Assumptions surfaced.
- **CONSEQUENTIAL** — "Restructure the auth system" → Maximum rigor. All dimensions mandatory. Devil's Advocate on assumptions. Quality review required.

Tier classification is automatic (keyword matching + optional LLM), with manual override.

## Quick Start

```bash
pip install draft-protocol
```

### MCP Clients (stdio — default)

Works with any MCP-compatible AI client. Add to your config:

<details>
<summary><b>Claude Desktop</b> — <code>claude_desktop_config.json</code></summary>

```json
{
  "mcpServers": {
    "draft-protocol": {
      "command": "python",
      "args": ["-m", "draft_protocol"],
      "env": {}
    }
  }
}
```
</details>

<details>
<summary><b>Cursor</b> — <code>.cursor/mcp.json</code></summary>

```json
{
  "mcpServers": {
    "draft-protocol": {
      "command": "python",
      "args": ["-m", "draft_protocol"],
      "env": {}
    }
  }
}
```
</details>

<details>
<summary><b>Windsurf</b> — <code>~/.codeium/windsurf/mcp_config.json</code></summary>

```json
{
  "mcpServers": {
    "draft-protocol": {
      "command": "python",
      "args": ["-m", "draft_protocol"],
      "env": {}
    }
  }
}
```
</details>

<details>
<summary><b>Continue</b> — <code>~/.continue/config.json</code></summary>

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": { "type": "stdio", "command": "python", "args": ["-m", "draft_protocol"] }
      }
    ]
  }
}
```
</details>

<details>
<summary><b>VS Code Copilot</b> — <code>.vscode/settings.json</code></summary>

```json
{
  "github.copilot.chat.mcpServers": {
    "draft-protocol": {
      "command": "python",
      "args": ["-m", "draft_protocol"]
    }
  }
}
```
</details>

### Web & HTTP Clients (SSE / Streamable HTTP)

For web-based MCP clients, browser extensions, or remote access:

```bash
# SSE transport (Server-Sent Events)
python -m draft_protocol --transport sse --port 8420

# Streamable HTTP (new MCP standard)
python -m draft_protocol --transport streamable-http --port 8420
```

Connect any SSE-capable MCP client to `http://127.0.0.1:8420/sse`.

### REST API (for non-MCP clients & Chrome extension)

```bash
python -m draft_protocol --transport rest --port 8420
```

Endpoints: `/classify`, `/session`, `/map`, `/confirm`, `/gate`, `/elicit`, `/assumptions`, `/status`, `/health`. Full CORS support.

### Chrome Extension (any AI chat)

The included Chrome extension adds DRAFT governance to any AI chat interface:

1. Start the REST server: `python -m draft_protocol --transport rest`
2. Load the extension: Chrome → `chrome://extensions` → Developer mode → Load unpacked → select `extension/`
3. Visit any supported AI chat — a governance badge appears automatically

**Supported platforms:** ChatGPT, Claude, Gemini, Copilot, Mistral, Poe, Perplexity, HuggingFace Chat.

The badge shows real-time tier classification as you type. Click it for full session status. Open the side panel for the complete DRAFT workflow.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DRAFT_TRANSPORT` | `stdio` | Transport: `stdio`, `sse`, `streamable-http`, `rest` |
| `DRAFT_HOST` | `127.0.0.1` | Bind address for HTTP transports |
| `DRAFT_PORT` | `8420` | Port for HTTP transports |
| `DRAFT_DB_PATH` | `~/.draft_protocol/draft.db` | SQLite database location |
| `DRAFT_LLM_PROVIDER` | `none` | LLM provider: `none`, `ollama`, `openai`, `anthropic` |
| `DRAFT_LLM_MODEL` | *(empty)* | Model name (auto-detects provider if not set) |
| `DRAFT_EMBED_MODEL` | *(empty)* | Embedding model name |
| `DRAFT_API_KEY` | *(empty)* | API key for cloud providers |
| `DRAFT_API_BASE` | *(empty)* | Custom API endpoint URL |

### Optional: Enhanced Intelligence with Any LLM

DRAFT works out of the box with keyword matching and heuristics. For better accuracy, connect any LLM provider:

<details>
<summary><b>Ollama (local, free)</b></summary>

```json
{
  "env": {
    "DRAFT_LLM_PROVIDER": "ollama",
    "DRAFT_LLM_MODEL": "llama3.2:3b",
    "DRAFT_EMBED_MODEL": "nomic-embed-text"
  }
}
```
</details>

<details>
<summary><b>OpenAI</b></summary>

```json
{
  "env": {
    "DRAFT_LLM_PROVIDER": "openai",
    "DRAFT_LLM_MODEL": "gpt-4o-mini",
    "DRAFT_EMBED_MODEL": "text-embedding-3-small",
    "DRAFT_API_KEY": "sk-..."
  }
}
```
</details>

<details>
<summary><b>Anthropic</b></summary>

```json
{
  "env": {
    "DRAFT_LLM_PROVIDER": "anthropic",
    "DRAFT_LLM_MODEL": "claude-sonnet-4-20250514",
    "DRAFT_API_KEY": "sk-ant-..."
  }
}
```
</details>

<details>
<summary><b>Any OpenAI-compatible API</b> (Together, Groq, LM Studio, etc.)</summary>

```json
{
  "env": {
    "DRAFT_LLM_PROVIDER": "openai",
    "DRAFT_LLM_MODEL": "meta-llama/Llama-3-70b-chat-hf",
    "DRAFT_API_KEY": "...",
    "DRAFT_API_BASE": "https://api.together.xyz/v1"
  }
}
```
</details>

Add the `env` block to any MCP client config above. With an LLM, DRAFT gets semantic tier classification, embedding-based field assessment, and context-aware suggestions. Without one, you still get full governance via keyword heuristics. Auto-detection: set `DRAFT_LLM_MODEL` without a provider and DRAFT infers it (gpt-* → openai, claude-* → anthropic, anything else → ollama).

## Tools

| Tool | Purpose |
|------|---------|
| `draft_intake` | Start a session. Classifies tier automatically. |
| `draft_map` | Map all 5 dimensions against your context. |
| `draft_elicit` | Generate questions for gaps. |
| `draft_confirm` | Record your answer for a field. |
| `draft_assumptions` | Surface key assumptions as falsifiable claims. |
| `draft_verify` | Confirm or reject an assumption. |
| `draft_gate` | Check if all fields are confirmed. Blocks execution if not. |
| `draft_review` | Quality self-assessment of the elicitation. |
| `draft_status` | View current session state. |
| `draft_escalate` | Manually increase tier. |
| `draft_deescalate` | Manually decrease tier (logged). |
| `draft_unscreen` | Reverse a dimension marked N/A. |
| `draft_add_assumption` | Add a manual or Devil's Advocate assumption. |
| `draft_override` | Override a blocked gate (logged, auditable). |
| `draft_close` | Close the current session. |

## Example Flow

**You:** "Build a Python CLI that backs up my PostgreSQL database to S3"

**DRAFT classifies:** STANDARD (keyword: "build")

**DRAFT maps dimensions and finds gaps:**
- D1 ✅ SATISFIED — CLI tool for PostgreSQL backup to S3
- D3 ❓ MISSING — What fails without it? (manual backups? no backups at all?)
- R3 ❓ MISSING — What's forbidden? (drop tables? modify data?)
- T1 ❓ MISSING — How do we know it worked?
- A2 ❓ MISSING — What inputs should be rejected?

**DRAFT asks targeted questions:**
> "What currently handles backups? If nothing, what's the risk of the current approach?"
> "Are there any operations this tool must never perform?"
> "What does a successful backup look like — file in S3, notification, verification?"

**You answer. DRAFT confirms. Gate opens. AI executes with verified intent.**

## Security

DRAFT includes hardened input validation:
- Empty/whitespace message rejection at intake
- Minimum content threshold on field confirmations (prevents bypass)
- Empty dimension detection at gate check
- Prompt extraction pattern detection (OWASP LLM07) — automatically escalates suspicious messages
- Full audit trail in SQLite (every tool call logged with timestamp)

## Storage

Sessions are stored in SQLite at `~/.draft_protocol/draft.db` (configurable via `DRAFT_DB_PATH`). The database includes a full audit trail of every action.

## Part of Vector Gate

DRAFT Protocol is the intake governance layer of [Vector Gate](https://github.com/manifold-vectors), a three-gate AI governance pipeline:

- **Gate 1 — DRAFT** (this project): Intake governance. Ensures AI understands intent.
- **Gate 2 — Guardian**: Output governance. Checks responses against constitutional rules.
- **Gate 3 — GovMCP**: Execution governance. Enforces authorized execution boundaries.

DRAFT works standalone. The full pipeline provides defense in depth.

## License

Apache 2.0 — see [LICENSE](LICENSE).

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR guidelines.

- **Bug reports**: [Open an issue](https://github.com/manifold-vectors/draft-protocol/issues/new?template=bug_report.yml)
- **Feature requests**: [Open an issue](https://github.com/manifold-vectors/draft-protocol/issues/new?template=feature_request.yml)
- **Security vulnerabilities**: See [SECURITY.md](SECURITY.md)
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md)

If you find a governance gap (gate bypassed when it shouldn't be), that's a **critical bug** — please report it immediately.

---

Built by [Manifold Vector LLC](https://github.com/manifold-vectors). AI governance that works mechanically, not behaviorally.
