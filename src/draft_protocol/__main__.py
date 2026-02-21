"""Entry point: python -m draft_protocol

Supports multiple MCP transports:
  stdio            — Default. For Claude Desktop, Cursor, Windsurf, Continue.
  sse              — Server-Sent Events. For web-based MCP clients.
  streamable-http  — New MCP standard. For HTTP-native MCP clients.

Usage:
  python -m draft_protocol                          # stdio (default)
  python -m draft_protocol --transport sse          # SSE on port 8420
  python -m draft_protocol --transport streamable-http --port 8420
  python -m draft_protocol --transport rest         # REST API on port 8420

Environment variables (override CLI defaults):
  DRAFT_TRANSPORT  — stdio | sse | streamable-http
  DRAFT_HOST       — Bind address (default: 127.0.0.1)
  DRAFT_PORT       — Port for SSE/HTTP (default: 8420)
"""
import argparse
import os

from draft_protocol.server import mcp


def main():
    parser = argparse.ArgumentParser(
        prog="draft-protocol",
        description="DRAFT Protocol — Intake governance for AI tool calls.",
    )
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "sse", "streamable-http", "rest"],
        default=os.environ.get("DRAFT_TRANSPORT", "stdio"),
        help="MCP transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("DRAFT_HOST", "127.0.0.1"),
        help="Bind address for SSE/HTTP (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.environ.get("DRAFT_PORT", "8420")),
        help="Port for SSE/HTTP (default: 8420)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "rest":
        from draft_protocol.rest import run_rest_server
        run_rest_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
