# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- 46 tests covering security, lifecycle, governance, and provider configuration

[Unreleased]: https://github.com/georgegoytia/draft-protocol/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/georgegoytia/draft-protocol/releases/tag/v0.1.0
