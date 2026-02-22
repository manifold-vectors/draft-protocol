"""Tests for DRAFT Protocol REST API."""
import json
import os
import tempfile
from http.server import HTTPServer
from io import BytesIO
from threading import Thread
from unittest.mock import patch

_test_db = tempfile.mktemp(suffix=".db")
os.environ["DRAFT_DB_PATH"] = _test_db

from draft_protocol.rest import DraftHandler  # noqa: E402


class MockRequest:
    """Minimal mock for HTTP request."""

    def __init__(self, method: str, path: str, body: dict | None = None):
        self.method = method
        self.path = path
        self.body = json.dumps(body).encode() if body else b""


class FakeSocket:
    """Fake socket for handler construction."""

    def __init__(self):
        self.data = b""

    def makefile(self, mode, buffering=-1):
        return BytesIO(self.data)

    def sendall(self, data):
        self.data += data


def make_handler(method: str, path: str, body: dict | None = None) -> tuple:
    """Create a DraftHandler and capture its response."""
    body_bytes = json.dumps(body).encode() if body else b""
    request_line = f"{method} {path} HTTP/1.1\r\n"
    headers = f"Content-Type: application/json\r\nContent-Length: {len(body_bytes)}\r\n\r\n"
    raw = request_line.encode() + headers.encode() + body_bytes

    rfile = BytesIO(raw)
    wfile = BytesIO()

    # Construct handler with mock connection
    handler = DraftHandler.__new__(DraftHandler)
    handler.rfile = BytesIO(body_bytes)
    handler.wfile = wfile
    handler.path = path
    handler.headers = {"Content-Type": "application/json", "Content-Length": str(len(body_bytes))}
    handler.requestline = f"{method} {path} HTTP/1.1"
    handler.request_version = "HTTP/1.1"
    handler.command = method
    handler.client_address = ("127.0.0.1", 0)
    handler.server = type("FakeServer", (), {"server_name": "localhost", "server_port": 8420})()
    handler.close_connection = True
    handler.raw_requestline = request_line.encode()

    # Suppress logging
    handler.log_message = lambda *a: None

    return handler, wfile


def parse_response(wfile: BytesIO) -> tuple[int, dict]:
    """Extract status code and JSON body from handler output."""
    wfile.seek(0)
    raw = wfile.read().decode("utf-8", errors="replace")
    # Find JSON body (after double newline)
    parts = raw.split("\r\n\r\n", 1)
    if len(parts) < 2:
        return 0, {}
    status_line = parts[0].split("\r\n")[0]
    status_code = int(status_line.split(" ")[1]) if " " in status_line else 0
    try:
        body = json.loads(parts[1])
    except (json.JSONDecodeError, IndexError):
        body = {}
    return status_code, body


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        handler, wfile = make_handler("GET", "/health")
        handler.do_GET()
        status, body = parse_response(wfile)
        assert status == 200
        assert body["status"] == "ok"
        assert body["service"] == "draft-protocol"


class TestStatusEndpoint:
    def test_status_no_active_session(self):
        handler, wfile = make_handler("GET", "/status")
        handler.do_GET()
        status, body = parse_response(wfile)
        assert status == 200
        assert body["active"] is False


class TestClassifyEndpoint:
    def test_classify_standard(self):
        handler, wfile = make_handler("POST", "/classify", {"message": "build a Python tool"})
        handler.do_POST()
        status, body = parse_response(wfile)
        assert status == 200
        assert body["tier"] == "STANDARD"

    def test_classify_casual(self):
        handler, wfile = make_handler("POST", "/classify", {"message": "hello"})
        handler.do_POST()
        status, body = parse_response(wfile)
        assert status == 200
        assert body["tier"] == "CASUAL"

    def test_classify_empty_rejects(self):
        handler, wfile = make_handler("POST", "/classify", {"message": ""})
        handler.do_POST()
        status, body = parse_response(wfile)
        assert status == 400
        assert "error" in body


class TestSessionEndpoint:
    def test_create_session(self):
        handler, wfile = make_handler("POST", "/session", {"message": "build a REST API"})
        handler.do_POST()
        status, body = parse_response(wfile)
        assert status == 200
        assert "session_id" in body
        assert body["tier"] in ("CASUAL", "STANDARD", "CONSEQUENTIAL")

    def test_create_session_empty_rejects(self):
        handler, wfile = make_handler("POST", "/session", {"message": ""})
        handler.do_POST()
        status, body = parse_response(wfile)
        assert status == 400


class TestNotFoundEndpoint:
    def test_get_unknown_path(self):
        handler, wfile = make_handler("GET", "/nonexistent")
        handler.do_GET()
        status, body = parse_response(wfile)
        assert status == 404

    def test_post_unknown_path(self):
        handler, wfile = make_handler("POST", "/nonexistent", {"data": "test"})
        handler.do_POST()
        status, body = parse_response(wfile)
        assert status == 404
