---
title: "draft-protocol — Product Spec"
type: spec
domain: products
subdomain: draft-protocol
status: draft
date: 2026-04-24
modified: 2026-04-27
tags: [products, spec, draft-protocol, ude/state]
ude_force: state
---
# draft-protocol — Product Spec

> **Status:** Placeholder. Fill the TODO list below using [[_templates/products/PRODUCT_SPEC_TEMPLATE]].

## TODO

### From `README.md`

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
| **Evidence basis** | Synthetic benchmarks | 140 tests + governed sessions |
| **Complementary?** | Yes | Yes — use both for defense-in-depth |

## The Problem

AI agents are getting powerful. They can write code, manage files, query databases, deploy infrastructure

### From `ROADMAP.md`

# Roadmap

What's shipped, what's next, what we won't build. Updated as priorities change based on real usage.

---

## Shipped

### v0.1.0 (February 2026)

- 5-dimension elicitation engine (Define, Rules, Artifacts, Flex, Test)
- 3-tier governance classification (Casual, Standard, Consequential)
- 7-step pipeline with cross-disciplinary methodology validation
- 15 MCP tools for native integration
- Multi-transport MCP server (stdio, SSE, streamable-http)
- REST API with Bearer token authentication
- Chrome Extension for browser-based AI chat platforms
- Optional LLM-enhanced tier classification
- Full audit trail for all sessions
- Dimension screening with skip-logic
- Conformance finding tracking (13 CFs identified and resolved)
- 80+ automated tests, CI/CD with GitHub Actions
- Docker support
- Apache 2.0 license

---

## Next: v0.2

- [ ] **API key and Bearer token hardening** — production-ready auth with rotation support
- [ ] **Python client library** — `DRAFTClient` for programmatic integration without raw REST calls
- [ ] **Framework quickstart examples** — working demos for LangChain, CrewAI, AutoGen, OpenAI, Anthropic
- [ ] **Improved tier classifier** — reduced false positive rate on governance-adjacent vocabulary
- [ ] **Unscreen operation** — reactivate screened dimensions mid-session (CF-010 fix)
- [ ] **Manual assumption tracking** — Devil's Advocate findings logged to structured session state (CF-011 fix)

## v0.3

- [ ] **Webhook support** — DRAFT events (ses

### From `docs/ARCHITECTURE.md`

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


### From brain_corpus
- _(score 0.668)_ `claude` —  blocker remaining: public-facing README.**

---

**Industry standard for open-source protocol/spec launches** — based on what OpenAPI, JSON Schema, and successful spec repos do:

The minimum viable repo for a spec launch needs these files: README.md (the big one), LICENSE (Apache 2.0 — just the sta…
- _(score 0.667)_ `claude` — this as a DRAFT spec. Let me build it out.

Here's your DRAFT spec, George. It covers:

**Guardian Gates** — the full gate architecture with instruction layers, MCP integration layers, and evaluation layers. Eight gate categories (Ethics, Safety, Transparency, Accountability, Privacy, Security, Comp…
- _(score 0.665)_ `claude` — [User]: lets go with b

[Assistant]: Building. Let me read the docx skill, then produce **Vector Agent Platform Architecture v1.0**.

**Vector Agent Platform Architecture v1.0** — 12 sections, fully cross-referenced to your existing spec stack.

What's in it: the full governing document hierarchy, y…
- _(score 0.664)_ `claude` — three-gate security architecture |
| `CONTRIBUTING.md` | VectorLab + draft-protocol | Dev setup, code standards, branch strategy |
| `CODE_OF_CONDUCT.md` | draft-protocol | Contributor Covenant v2.1 |
| `AGENTS.md` | VectorLab pattern | AI agent instructions, repo map, conventions |
| `RULES.md` | V…
- _(score 0.664)_ `claude` — **Change 3: The Symmetry Test (S1–S5) gates all future specs.** Before, a new subsystem only had to satisfy its own domain requirements and pass CLEAR. Now it also has to answer five structural questions: what are its symmetries, what does each conserve, what breaks when violated, does it cohere wit…

## Sources consulted

- products\draft-protocol\README.md
- products\draft-protocol\ROADMAP.md
- products\draft-protocol\docs\ARCHITECTURE.md
- qdrant.brain_corpus (5 hits for 'draft-protocol spec')
- _filled by `auto_fill_placeholders.py` on 2026-04-27_

## Related
- Template: [[_templates/products/PRODUCT_SPEC_TEMPLATE]]
- Parent MOC: [[products/draft-protocol/_MOC|↑ draft-protocol]]
