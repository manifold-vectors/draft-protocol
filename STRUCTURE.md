# Repository Structure

```
draft-protocol/
├── .dockerignore                    # Docker build exclusions
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml           # Bug report template
│   │   └── feature_request.yml      # Feature request template
│   ├── PULL_REQUEST_TEMPLATE.md     # PR checklist
│   └── workflows/
│       ├── ci.yml                   # CI: lint + test matrix (3.10-3.13)
│       └── release.yml              # Release: test → build → PyPI → GitHub Release
├── AGENTS.md                        # AI agent instructions for this repo
├── CHANGELOG.md                     # Release history (Keep a Changelog format)
├── CODE_OF_CONDUCT.md               # Contributor covenant
├── CONTRIBUTING.md                  # Dev setup, code style, PR guidelines
├── Dockerfile                       # Production container (SSE default)
├── LICENSE                          # Apache 2.0
├── Makefile                         # Dev commands: make lint, test, format, etc.
├── README.md                        # Quick start, MCP configs, tool reference
├── RULES.md                         # Procedural memory for AI agents
├── SECURITY.md                      # Vulnerability reporting policy
├── STRUCTURE.md                     # This file
├── docker-compose.example.yml       # Example: DRAFT + Ollama stack
├── docs/
│   ├── README.md                    # Documentation index
│   ├── api.md                       # REST API reference
│   └── architecture.md              # System design, pipeline flow, security model
├── examples/
│   ├── README.md                    # Examples index
│   └── basic_usage.py               # Library usage without server
├── extension/                       # Chrome extension (any AI chat)
│   ├── background.js                # Service worker
│   ├── content.css                  # Injected styles
│   ├── content.js                   # Chat detection + badge injection
│   ├── icons/                       # Extension icons (16/48/128)
│   ├── manifest.json                # Manifest V3
│   ├── popup.html                   # Toolbar popup
│   ├── popup.js                     # Popup logic
│   ├── sidepanel.html               # Side panel UI
│   └── sidepanel.js                 # Side panel logic
├── pyproject.toml                   # Build config, deps, tool settings
├── src/
│   └── draft_protocol/
│       ├── __init__.py              # Public API re-exports + version
│       ├── __main__.py              # Entry point (transport selection)
│       ├── config.py                # Env config, triggers, field definitions
│       ├── engine.py                # Core: classify, map, elicit, gate
│       ├── providers.py             # LLM abstraction (Ollama/OpenAI/Anthropic)
│       ├── py.typed                 # PEP 561 typed marker
│       ├── rest.py                  # REST API server
│       ├── server.py                # MCP server (FastMCP, 15 tools)
│       └── storage.py               # SQLite session + audit storage
└── tests/
    ├── conftest.py                  # pytest marker registration
    ├── test_draft_protocol.py       # Core engine + lifecycle tests (46 tests)
    ├── test_rest.py                 # REST API endpoint tests
    └── test_security.py             # Injection, bypass, validation tests
```

## Key Conventions

- **Source layout**: `src/draft_protocol/` (PEP 517 src layout)
- **Entry point**: `python -m draft_protocol` or `draft-protocol` CLI
- **Tests**: pytest, no framework — each test file sets temp DB via env var
- **Lint**: ruff (E, F, W, I, UP, B, SIM, TCH) — CI runs `ruff check`
- **Types**: mypy with `py.typed` marker
- **Docs**: Markdown in `docs/`, no build step
- **Docker**: Single-stage slim image, non-root user
