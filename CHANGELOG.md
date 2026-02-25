# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/manifold-vectors/draft-protocol/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/manifold-vectors/draft-protocol/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/manifold-vectors/draft-protocol/releases/tag/v0.1.0
