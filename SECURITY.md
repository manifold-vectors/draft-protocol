# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Email security concerns to the maintainers with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Security Model

DRAFT Protocol is an **intake governance layer**. Its security properties:

- **Gate is fail-closed**: Unconfirmed fields block execution. The gate never silently passes.
- **Input validation**: Empty, whitespace, and minimum-length checks at all entry points.
- **Prompt extraction detection**: Suspicious patterns (OWASP LLM07) auto-escalate to STANDARD+ tier.
- **Audit trail**: Every tool call is logged to SQLite with timestamp and session ID.
- **No credential storage**: DRAFT never persists API keys. They're read from env vars at startup only.

### What DRAFT Does NOT Protect Against

- **Output content**: DRAFT governs intake (understanding intent), not output (what the AI generates). Use Guardian or similar tools for output governance.
- **Execution safety**: DRAFT verifies intent before execution but does not sandbox execution itself.
- **Provider security**: API keys for cloud LLM providers are passed through; DRAFT does not encrypt or validate them beyond basic presence checks.

## Threat Model

DRAFT assumes the human operator is trusted. The primary threats it addresses:
1. AI misunderstanding human intent (scope drift, assumption errors)
2. Prompt injection attempting to bypass governance tiers
3. Accidental execution on unverified or ambiguous requirements
