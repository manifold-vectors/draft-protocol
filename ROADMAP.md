---
title: draft-protocol — ROADMAP
type: roadmap
domain: company
subdomain: products/draft-protocol
status: active
date: 2026-04-24
modified: 2026-04-24
tags: [company, roadmap, products, draft-protocol, ude/state]
ude_force: state
---
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

- [ ] **Webhook support** — DRAFT events (session created, gate passed, gate blocked) as webhooks for external systems
- [ ] **Multi-user session support** — multiple humans contributing to the same DRAFT session
- [ ] **Streaming elicitation** — real-time dimensional mapping as the human types (experimental)
- [ ] **Metrics dashboard** — session statistics, tier distribution, common ambiguity patterns
- [ ] **Benchmark CLI** — `draft-protocol benchmark --sessions ./my_sessions/` for reproducible measurement

## v1.0

- [ ] **Stable API** — no breaking changes after v1.0
- [ ] **DRAFT Certification spec** — formal criteria for certifying that an AI system implements DRAFT correctly
- [ ] **Language support** — DRAFT elicitation in non-English languages
- [ ] **Enterprise features** — SSO, team management, audit export

---

## What We Won't Build

This section exists because scope discipline matters more than feature count. These are deliberate architectural decisions, not missing features.

**We won't replace output guardrails.** DRAFT governs intake — making sure AI understands intent before acting. Validating what the AI produces is a different problem with excellent existing solutions (Guardrails AI, NeMo Guardrails). We're complementary, not competitive. Use both.

**We won't become a full agent framework.** DRAFT sits between the human and the agent framework. It doesn't orchestrate tasks, manage memory, or route between agents. LangChain, CrewAI, and AutoGen do that well. DRAFT makes them do it on the right task.

**We won't add behavioral rules that drift.** The entire premise of DRAFT is structural enforcement. If a governance feature requires relying on instructions that degrade under pressure, it doesn't belong in this protocol. Every rule must be mechanically enforceable.

**We won't chase features nobody uses.** The roadmap moves based on real usage pain reported through issues, not theoretical completeness. If a feature has zero demand, it gets cut regardless of how clever it is.

**We won't sacrifice simplicity for power.** `pip install draft-protocol` should stay the entire onboarding experience. If a feature makes getting started harder, it needs a very compelling reason to exist.

---

## Community Requested

Features requested by users. Upvote with 👍 on the linked issue to signal priority.

| Feature | Issue | Votes |
|---|---|---|
| *No community requests yet — be the first!* | [Open an issue](https://github.com/manifold-vectors/draft-protocol/issues/new?labels=roadmap) | — |

We prioritize based on real usage pain, not theoretical completeness.

---

## Contributing to the Roadmap

Open an issue with the `roadmap` label. Describe what problem you're trying to solve, not just what feature you want. The best roadmap items come from people using DRAFT in production and hitting real friction.

---

*DRAFT Protocol is Gate 1 (intake) in the [Vector Gate](https://github.com/manifold-vectors) pipeline. This roadmap covers the open-source DRAFT component only.*
