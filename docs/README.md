# Documentation

## Overview

DRAFT Protocol is Gate 1 of the Vector Gate pipeline — intake governance for AI tool calls.

```
User Message → [DRAFT] → [Guardian] → [GovMCP] → Execution
                Gate 1      Gate 2      Gate 3
               (intent)    (output)   (execution)
```

## Documents

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design, pipeline flow, security model |
| [REST API Reference](api.md) | HTTP endpoints, request/response formats |
| [README](../README.md) | Quick start, MCP configs, tool reference |
| [Contributing](../CONTRIBUTING.md) | Development setup, code style, PR guidelines |
| [Security](../SECURITY.md) | Vulnerability reporting |
| [Changelog](../CHANGELOG.md) | Release history |

## Quick Links

- **MCP server:** `python -m draft_protocol` (stdio default)
- **REST API:** `python -m draft_protocol --transport rest --port 8420`
- **Docker:** `docker compose -f docker-compose.example.yml up`
- **Library:** `from draft_protocol import classify_tier, create_session, map_dimensions`
- **Examples:** See [`examples/`](../examples/)
