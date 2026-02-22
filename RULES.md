# RULES.md — Procedural Memory

> Lessons learned, process rules, and patterns for this repo.

## Process

- All changes go through PR with CI passing before merge
- CODEOWNERS requires founder review on governance-critical files (engine, storage, config)
- Changelog updated for every user-facing change
- Version bump in pyproject.toml matches git tag

## Security

- No secrets in source. Use environment variables (`DRAFT_API_KEY`, etc.)
- detect-secrets runs in pre-commit and CI
- Prompt extraction attacks (OWASP LLM07) are detected and auto-escalated
- Empty/whitespace inputs rejected at all entry points
- SQLite audit trail is append-only by design

## Product

- DRAFT works without any LLM (keyword heuristics). LLM is optional enhancement
- Chrome extension must support all 8 platforms (ChatGPT, Claude, Gemini, Copilot, Mistral, Poe, Perplexity, HuggingFace)
- Three tiers (Casual/Standard/Consequential) are core — never remove a tier
- Confirmation gate is the key safety mechanism — never allow bypass without audit trail
- Five dimensions (D, R, A, F, T) — D and T are mandatory, R/A/F can be screened

## Git

- Tags: `v{major}.{minor}.{patch}` — triggers PyPI release workflow
- Branch strategy: `main` only, feature branches for PRs
- Squash merge preferred for clean history
