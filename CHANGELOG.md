# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-03-08

### Added
- **5-Tier Classification** — TRIVIAL, LOOKUP, TASK, MULTI, CONSEQUENTIAL replace the 3-tier CASUAL/STANDARD/CONSEQUENTIAL system. Finer-grained governance matching actual task complexity.
- **Open Elicitation Phase** — `open_elicitation()` adds unstructured intent gathering (Cognitive Interview) before dimension mapping for TASK+ tiers. Prevents anchoring bias.
- **Assumption Quality Scoring** — `score_assumptions()` rates each assumption on falsifiability, impact, and novelty (0-1 each). Low-quality assumptions flagged for replacement.
- **Ceremony Depth** — `get_ceremony_depth()` returns tier-appropriate governance visibility: invisible (TRIVIAL), tag (LOOKUP), semi_visible (TASK), visible (MULTI), full (CONSEQUENTIAL).
- **Legacy Tier Compatibility** — CASUAL/STANDARD/CONSEQUENTIAL still accepted, auto-mapped to new tiers. `resolve_tier_override()` and `get_legacy_tier()` for bidirectional mapping.
- **MCP Tool: `draft_open_elicit`** — open elicitation as a dedicated tool for TASK+ sessions.
- 57 new tests covering 5-tier classification, open elicitation, ceremony depth, legacy compat, assumption scoring. Total suite: 197 tests.

### Changed
- Tier classification engine now uses 5-tier keyword sets with priority ordering (T4 > T3 > T2 > T1 > T0)
- Extraction attack patterns moved from STANDARD_TRIGGERS to CONSEQUENTIAL_TRIGGERS (security fix)
- `create_session()` auto-maps legacy tier names to 5-tier equivalents
- Assumption count scales across 5 tiers: 0 (TRIVIAL), 1 (LOOKUP), 2 (TASK), 3 (MULTI), 5 (CONSEQUENTIAL)

## [1.1.0] - 2026-03-07

### Added
- **Batch Operations** — `confirm_batch`, `quick_confirm_satisfied`, `verify_batch` reduce tool call overhead by 50-60% per session
- **LLM-Powered Adversarial Assumptions** — when LLM is available, generates genuinely falsifiable claims instead of restating confirmed fields (fixes CF-011 rubber-stamp problem)
- **Devil's Advocate at All Tiers** — scaled intensity: CASUAL 1-2, STANDARD 2-3, CONSEQUENTIAL 3-5 assumptions
- **Hard Extraction Enforcement** — strips fabricated extracted text from AMBIGUOUS/MISSING fields in LLM assessments
- **Escalation/De-escalation** — `escalate_tier` and `deescalate_tier` with audit trail and reason logging
- **Collaborative Framing** — PEACE + Motivational Interviewing framing hints on all elicitation questions
- **Perfunctory Confirmation Detection** — warns on repeated identical values, known rubber-stamp patterns (DFT-08)
- **Session Analytics** — `elicitation_review` includes metrics: field counts, confidence distribution, assumption rejection rate
- **M1.3 Closed Session Guards** — all engine functions reject operations on closed sessions
- **M1.4 Tier Enum Validation** — strict tier validation at intake
- **M1.5 Context Enrichment on Gate PASS** — gate results include full dimensional context
- 35 new v1.1 feature tests + 25 hardening tests, total suite: 140 tests
- 18 MCP tools (3 new: `draft_confirm_batch`, `draft_quick_confirm`, `draft_verify_batch`; 2 new: `draft_escalate`, `draft_deescalate`)

### Changed
- Assumption generation scales by tier instead of fixed count
- Gate results include perfunctory warnings alongside blockers
- Elicitation review returns analytics block with session-level metrics
- Test suite expanded from 80 to 140 tests, zero regressions

## [1.0.0] - 2026-02-27

### Added
- First stable release — all core features production-hardened
- Python Semantic Release (PSR) automated CI/CD pipeline
- Automated version bumps, changelogs, tagging, and PyPI publishing

### Changed
- Promoted from 0.x to 1.0 — API considered stable

## [0.1.1] - 2026-02-25

### Added
- `RELEASING.md` — release gate checklist to prevent builder's blindness
- Minimal working example (end-to-end transcript) in README
- Conformance quick-scan index table at top of `CONFORMANCE.md`
- `docs/architecture.md` — system design, pipeline flow, security model, file layout
- `docs/api.md` — REST API reference with all endpoints, request/response examples
- `examples/basic_usage.py` — library usage example (no server needed)
- `tests/test_security.py` — prompt injection, bypass, input validation tests
- `tests/test_rest.py` — REST API endpoint tests with mock handler
- `Dockerfile` — production container (Python 3.13-slim, non-root, SSE default)
- `docker-compose.example.yml` — example stack with DRAFT + Ollama
- `.dockerignore` — keep Docker image clean
- `.github/ISSUE_TEMPLATE/bug_report.yml` — structured bug report template
- `.github/ISSUE_TEMPLATE/feature_request.yml` — structured feature request template
- `.github/PULL_REQUEST_TEMPLATE.md` — PR checklist

### Fixed
- `rest.py` `/status` endpoint called nonexistent `storage.get_session_state()` — replaced with inline session + gate query
- Documented Anthropic embeddings limitation (voyage model not supported, use `text-embedding-3-small` or Ollama)
- Added localhost-only security warning to REST API docs

### Changed
- `docs/README.md` updated to documentation index linking all docs
- `STRUCTURE.md` updated to reflect all new files

## [0.1.0] - 2025-02-21

### Added
- 15 MCP tools for structured intent elicitation via FastMCP
- Three-tier automatic classification: Casual, Standard, Consequential
- Five-dimension mapping: Define, Rules, Artifacts, Flex, Test
- Confirmation gate blocks execution until all fields verified
- Assumptions surfacing with Devil's Advocate support
- Dimension screening for non-mandatory dimensions (R, A, F)
- Gate override with audit trail for founder use
- Elicitation review with quality self-assessment
- Multi-provider LLM support: Ollama, OpenAI, Anthropic, any OpenAI-compatible API
- Auto-detection of provider from model name
- Graceful degradation to keyword heuristics without LLM
- Prompt extraction attack detection (OWASP LLM07)
- Empty/whitespace input rejection at all entry points
- Full SQLite audit trail
- REST API with CORS for Chrome extension and HTTP clients
- Chrome extension for any AI chat (ChatGPT, Claude, Gemini, etc.)
- 46 tests covering security, lifecycle, governance, and provider configuration
- AGENTS.md, RULES.md, STRUCTURE.md for AI agent compatibility
- Professional repo infrastructure: CONTRIBUTING, SECURITY, CODE_OF_CONDUCT

[Unreleased]: https://github.com/manifold-vectors/draft-protocol/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/manifold-vectors/draft-protocol/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/manifold-vectors/draft-protocol/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/manifold-vectors/draft-protocol/compare/v0.1.1...v1.0.0
[0.1.1]: https://github.com/manifold-vectors/draft-protocol/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/manifold-vectors/draft-protocol/releases/tag/v0.1.0
