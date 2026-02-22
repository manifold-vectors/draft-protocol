# AGENTS.md — AI Agent Instructions

> For AI coding assistants (Copilot, Cursor, Claude, etc.) working in this repo.

## Project Overview

**DRAFT Protocol** is an open-source intake governance layer for AI tool calls. It ensures AI understands human intent before execution begins, using a structured 5-dimension elicitation protocol with three tiers of rigor.

**License:** Apache 2.0  
**Language:** Python 3.10+  
**Transport:** MCP (stdio, SSE, streamable-http) + REST API  

## Key Directories

```
src/draft_protocol/     # Core library
  engine.py             # Classification + mapping logic
  server.py             # MCP server (FastMCP)
  rest.py               # REST API (FastAPI)
  storage.py            # SQLite persistence + audit trail
  config.py             # Environment config + LLM provider setup
  providers.py          # LLM provider abstraction (Ollama, OpenAI, Anthropic)
extension/              # Chrome extension (works on 8 AI chat platforms)
tests/                  # pytest suite (46+ tests)
docs/                   # Product documentation
```

## Conventions

- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`)
- **Style:** ruff for linting + formatting, mypy for type checking
- **Line length:** 120 characters
- **Tests:** pytest. Run `make test` before committing
- **Pre-commit:** Installed via `make dev`. Runs ruff + trailing whitespace + detect-secrets

## What NOT to Do

- Do not commit secrets, API keys, or `.env` files
- Do not add dependencies without updating `pyproject.toml`
- Do not modify `engine.py` or `storage.py` without running the full test suite
- Do not bypass the DRAFT elicitation protocol in code — it's the product
- Do not add files larger than 5MB

## Related Repos

| Repo | Purpose | Platform |
|------|---------|----------|
| vector-gate | Three-gate pipeline (product repo) | GitLab (private) |
| draft-protocol | This repo — Gate 1 intake governance | GitHub (Apache 2.0) |
