# DRAFT Protocol

**Intake governance for AI tool calls.** Ensures AI understands what you want before it does anything.

DRAFT is a structured elicitation protocol that sits between you and your AI agent. Before the AI executes, DRAFT maps your intent across five dimensions, surfaces assumptions, and gates execution until everything is confirmed. No more "I assumed you meant..." after the damage is done.

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

## Install

```bash
pip install draft-protocol
```

### Configure for Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

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

That's it. DRAFT is now available as 15 tools in Claude Desktop.

### Optional: Enhanced Intelligence with Ollama

DRAFT works out of the box with keyword matching and heuristics. For better accuracy, connect a local LLM via [Ollama](https://ollama.ai):

```json
{
  "mcpServers": {
    "draft-protocol": {
      "command": "python",
      "args": ["-m", "draft_protocol"],
      "env": {
        "DRAFT_LLM_MODEL": "llama3.2:3b",
        "DRAFT_EMBED_MODEL": "nomic-embed-text"
      }
    }
  }
}
```

With Ollama, DRAFT gets:
- Semantic tier classification (not just keywords)
- Embedding-based field assessment (cosine similarity)
- Context-aware suggestion generation

Without Ollama, you still get full governance — just with keyword heuristics instead of semantic understanding.

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

Sessions are stored in SQLite at `~/.draft_protocol/draft.db` (configurable via `DRAFT_DB_PATH` environment variable). The database includes full audit trail of every action.

## Part of Vector Gate

DRAFT Protocol is the intake governance layer of [Vector Gate](https://github.com/manifold-vector), a three-gate AI governance pipeline:

- **Gate 1 — DRAFT** (this project): Intake governance. Ensures AI understands intent.
- **Gate 2 — Guardian**: Output governance. Checks responses against constitutional rules.
- **Gate 3 — GovMCP**: Execution governance. Enforces authorized execution boundaries.

DRAFT works standalone. The full pipeline provides defense in depth.

## License

Apache 2.0 — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome. If you find a governance gap, that's a high-priority bug.

---

Built by [Manifold Vector LLC](https://github.com/manifold-vector). AI governance that works mechanically, not behaviorally.
