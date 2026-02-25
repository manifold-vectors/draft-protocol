# Contributing to DRAFT Protocol

Thank you for considering contributing to DRAFT Protocol! This document explains how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/manifold-vectors/draft-protocol.git
cd draft-protocol

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=draft_protocol

# Run linter
ruff check src/ tests/
```

## Code Style

- We use [ruff](https://github.com/astral-sh/ruff) for linting and import sorting
- Line length: 120 characters
- Target: Python 3.10+
- All public functions need docstrings
- Type hints on all function signatures

## Making Changes

1. **Fork** the repo and create a branch from `main`
2. **Write tests** for any new functionality
3. **Run the full test suite** and ensure all tests pass
4. **Run the linter** and fix any issues
5. **Commit** with a clear message following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation only
   - `test:` adding or updating tests
   - `refactor:` code change that neither fixes a bug nor adds a feature
6. **Open a Pull Request** with a clear description of the change

## Architecture

```
src/draft_protocol/
├── __init__.py      # Public API exports
├── __main__.py      # Entry point: python -m draft_protocol
├── config.py        # Environment-driven configuration
├── engine.py        # Core governance logic (classification, mapping, gate)
├── providers.py     # LLM provider abstraction (ollama/openai/anthropic)
├── server.py        # FastMCP server with 15 tool definitions
└── storage.py       # SQLite session and audit storage
```

Key design principles:
- **Zero required dependencies beyond FastMCP** — keyword heuristics work without any LLM
- **Provider-agnostic** — any LLM works, configured via env vars
- **Fail-closed** — gate blocks execution on unverified fields, never silently passes
- **Audit everything** — every tool call logged with timestamp to SQLite

## Reporting Bugs

Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your Python version and OS

**Governance gaps are high-priority bugs.** If DRAFT allows unverified execution, that's a critical issue.

## Security

See [SECURITY.md](SECURITY.md) for reporting security vulnerabilities.

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
