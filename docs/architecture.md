# Architecture

## Overview

DRAFT Protocol is **Gate 1** of the Vector Gate pipeline — a three-gate AI governance system that ensures AI agents operate with verified intent, constitutional compliance, and authorized execution.

```
┌─────────────────────────────────────────────────────────────┐
│                    USER MESSAGE                             │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────┐
│  GATE 1 — DRAFT Protocol    │  ◄── Intake Governance
│  "Do I understand intent?"  │      (this project)
│                             │
│  • Classify tier            │
│  • Map 5 dimensions         │
│  • Surface assumptions      │
│  • Confirmation gate        │
└─────────────┬───────────────┘
              │ Intent verified
              ▼
┌─────────────────────────────┐
│  GATE 2 — Guardian          │  ◄── Output Governance
│  "Is the response safe?"    │
│                             │
│  • G1-G8 rule checks        │
│  • Constitutional compliance│
│  • Authority-claiming check │
└─────────────┬───────────────┘
              │ Response approved
              ▼
┌─────────────────────────────┐
│  GATE 3 — GovMCP            │  ◄── Execution Governance
│  "Am I authorized to act?"  │
│                             │
│  • T0-T3 trust levels       │
│  • Session authorization    │
│  • Audit trail              │
└─────────────┬───────────────┘
              │ Execution authorized
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TOOL EXECUTION                           │
└─────────────────────────────────────────────────────────────┘
```

DRAFT works standalone. The full pipeline provides defense in depth.

## Core Design Principles

### 1. Governance Before Cognition

DRAFT runs *before* the AI generates a response. This is the key architectural insight — most AI safety solutions filter the output (after the damage is conceptualized). DRAFT governs the intake (before cognition begins).

### 2. Graceful Degradation

DRAFT operates at three intelligence levels:

| Level | Requirements | Capabilities |
|-------|-------------|--------------|
| **Keyword** | None (zero dependencies) | Fast-path triggers, heuristic field matching |
| **Embedding** | Embedding model | Cosine similarity field assessment |
| **Full LLM** | Chat + embedding model | Semantic classification, smart suggestions |

Each level falls back cleanly. No LLM? Keywords work. No embeddings? Keywords work. Everything available? Best accuracy.

### 3. Mechanical Enforcement

The confirmation gate is binary — pass or block. No "soft" suggestions. The gate checks every applicable field and reports blockers. Override requires explicit authorization with audit trail.

### 4. Five Dimensions (DRAFT)

```
D — Define (Existence & ROI)     [MANDATORY]
    D1: What is being created?
    D2: What domain?
    D3: What fails without it?
    D4: Replacement test?
    D5: Non-goals?

R — Rules (Operation & Limits)   [SCREENABLE]
    R1: Human authority source?
    R2: Allowed decisions?
    R3: Forbidden decisions?
    R4: Stop conditions (≥3)?
    R5: Interfaces?

A — Artifacts (Inputs & Outputs) [SCREENABLE]
    A1: Allowed inputs?
    A2: Forbidden inputs?
    A3: Allowed outputs?
    A4: Forbidden outputs?
    A5: Correct example?
    A6: Incorrect example?

F — Flex (Change Without Drift)  [SCREENABLE]
    F1: Change authority?
    F2: Permitted changes?
    F3: Forbidden changes?
    F4: Review triggers?

T — Test (Evaluation)            [MANDATORY]
    T1: Success definition?
    T2: Failure definition?
    T3: Review questions (≥3)?
    T4: Evidence requirements?
```

D and T are always mapped. R, A, F undergo screening — if the task genuinely doesn't involve rules, artifacts, or lifecycle, those dimensions are marked N/A. Screening can be reversed with `draft_unscreen`.

## Seven-Step Pipeline

```
Step 1 — Open Elicitation     User describes intent freely
Step 2 — Provisional Interp   AI summarizes understanding
Step 3 — DRAFT Mapping        Map all 5 dimensions, screen R/A/F
Step 4 — Targeted Elicitation Ask about MISSING/AMBIGUOUS fields
Step 5 — Assumptions Check    Surface falsifiable claims
Step 6 — Confirmation Gate    All fields CONFIRMED? → proceed
Step 7 — Elicitation Review   Quality self-assessment
```

At CASUAL tier, steps 1, 5, and 7 are skipped. At CONSEQUENTIAL, all steps are mandatory with Devil's Advocate in step 5.

## Transport Architecture

```
                    ┌──────────────────────┐
                    │   draft_protocol     │
                    │   engine + storage   │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐  ┌─────▼──────┐  ┌──────▼─────┐
    │  MCP Server    │  │  REST API  │  │  Library   │
    │  (server.py)   │  │  (rest.py) │  │  (import)  │
    │                │  │            │  │            │
    │  stdio / sse / │  │  HTTP POST │  │  Python    │
    │  streamable    │  │  + CORS    │  │  API       │
    └────────────────┘  └────────────┘  └────────────┘
         │                    │
    MCP clients          Chrome ext
    (Claude, Cursor,     (any AI chat)
     Windsurf, etc.)
```

All three interfaces use the same engine and storage. No divergence.

## Storage

SQLite with WAL mode. Two tables:

- **sessions** — DRAFT session state (tier, dimensions, assumptions, gate status)
- **audit_log** — Append-only trace of every tool call with timestamps

Default location: `~/.draft_protocol/draft.db`. Override with `DRAFT_DB_PATH`.

## Security Model

| Threat | Mitigation |
|--------|-----------|
| Prompt extraction (OWASP LLM07) | Extraction patterns trigger escalation to STANDARD/CONSEQUENTIAL |
| Empty confirmation bypass | Minimum content threshold (3+ chars) on all field confirmations |
| Gate bypass | Gate checks for empty CONFIRMED fields, flags as possible bypass |
| Audit tampering | Append-only audit log, no delete operations exposed |
| Dimension skip | D and T are mandatory, cannot be screened. Override is logged. |

## File Layout

```
src/draft_protocol/
├── __init__.py      # Public API re-exports
├── __main__.py      # Entry point (transport selection)
├── config.py        # Environment config, triggers, field definitions
├── engine.py        # Core logic (classify, map, elicit, gate)
├── providers.py     # LLM abstraction (Ollama/OpenAI/Anthropic)
├── rest.py          # REST API server
├── server.py        # MCP server (FastMCP)
└── storage.py       # SQLite session + audit storage
```
