# Repository Structure

```
draft-protocol/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # CI: lint, test (4 Python versions), type-check, coverage
│   │   └── release.yml         # PyPI publish + GitHub Release on v* tags
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml      # Bug report template
│   │   └── feature_request.yml # Feature request template
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS              # Founder review on governance-critical files
│   └── dependabot.yml          # Automated dependency updates
├── docs/
│   └── PRODUCT_STANDARD.md     # Product portfolio standard (internal reference)
├── extension/
│   ├── background.js           # Service worker for Chrome extension
│   ├── content.js              # Content script — injects governance badge
│   ├── content.css             # Badge and panel styling
│   ├── popup.html/js           # Extension popup UI
│   ├── sidepanel.html/js       # Full DRAFT workflow side panel
│   ├── manifest.json           # Chrome extension manifest v3
│   └── icons/                  # Extension icons (16, 48, 128px)
├── src/draft_protocol/
│   ├── __init__.py             # Package init + version
│   ├── __main__.py             # CLI entry point (python -m draft_protocol)
│   ├── engine.py               # Core: classification, mapping, elicitation, gate logic
│   ├── server.py               # MCP server via FastMCP (stdio, SSE, streamable-http)
│   ├── rest.py                 # REST API via FastAPI (for Chrome extension + non-MCP)
│   ├── storage.py              # SQLite persistence + audit trail
│   ├── config.py               # Environment config + transport selection
│   ├── providers.py            # LLM provider abstraction (Ollama, OpenAI, Anthropic)
│   └── py.typed                # PEP 561 typed marker
├── tests/
│   └── test_draft_protocol.py  # 46+ tests: security, lifecycle, governance, providers
├── AGENTS.md                   # AI agent instructions
├── CHANGELOG.md                # Keep a Changelog format
├── CODE_OF_CONDUCT.md          # Contributor Covenant v2.1
├── CONTRIBUTING.md             # Dev setup, code style, PR guidelines
├── LICENSE                     # Apache 2.0
├── Makefile                    # Dev commands: test, lint, format, type-check, clean
├── README.md                   # Full documentation + Quick Start
├── RULES.md                    # Procedural memory + lessons learned
├── SECURITY.md                 # Vulnerability reporting policy
├── STRUCTURE.md                # This file
├── .editorconfig               # Editor formatting consistency
├── .gitignore                  # Python, IDE, OS, build artifacts
├── .pre-commit-config.yaml     # Pre-commit hooks (ruff, whitespace, secrets)
└── pyproject.toml              # Package config, dependencies, tool settings
```
