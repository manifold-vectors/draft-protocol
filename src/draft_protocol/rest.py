"""REST API for DRAFT Protocol — Lightweight HTTP interface.

Used by the Chrome extension and other HTTP clients that don't speak MCP.
Runs alongside or instead of the MCP server.

Endpoints:
  POST /classify    — Classify a message tier (returns tier, reasoning, confidence)
  POST /session     — Create a new DRAFT session
  POST /map         — Map dimensions for a session
  POST /confirm     — Confirm a field value
  POST /gate        — Check gate status
  GET  /status      — Get active session status
  GET  /health      — Health check

Start:
  python -m draft_protocol --transport rest --port 8420
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from draft_protocol import engine, storage


class DraftHandler(BaseHTTPRequestHandler):
    """Minimal REST handler — no framework dependencies."""

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def do_OPTIONS(self):  # noqa: N802
        """CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send_json({"status": "ok", "service": "draft-protocol", "version": "0.1.0"})
        elif self.path == "/status":
            session = storage.get_active_session()
            if session:
                gate = engine.check_gate(session["id"])
                self._send_json({
                    "active": True,
                    "session_id": session["id"],
                    "tier": session["tier"],
                    "intent": session.get("intent", "")[:200],
                    "gate": gate["summary"],
                    "created_at": session.get("created_at"),
                })
            else:
                self._send_json({"active": False, "message": "No active session"})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):  # noqa: N802
        try:
            data = self._read_json()
        except (json.JSONDecodeError, ValueError):
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        path = self.path

        if path == "/classify":
            message = data.get("message", "")
            if not message or not message.strip():
                self._send_json({"error": "message required"}, 400)
                return
            tier, reasoning, confidence = engine.classify_tier(message)
            self._send_json({"tier": tier, "reasoning": reasoning, "confidence": confidence})

        elif path == "/session":
            message = data.get("message", "")
            tier_override = data.get("tier_override", "")
            if not message or not message.strip():
                self._send_json({"error": "message required"}, 400)
                return
            # Close any active session first
            active = storage.get_active_session()
            if active:
                storage.close_session(active["id"])
            tier, reasoning, confidence = engine.classify_tier(message)
            if tier_override and tier_override in ("CASUAL", "STANDARD", "CONSEQUENTIAL"):
                tier = tier_override
            sid = storage.create_session(tier, message)
            self._send_json({
                "session_id": sid, "tier": tier,
                "reasoning": reasoning, "confidence": confidence,
            })

        elif path == "/map":
            sid = data.get("session_id", "")
            context = data.get("context", "")
            if not sid or not context:
                self._send_json({"error": "session_id and context required"}, 400)
                return
            result = engine.map_dimensions(sid, context)
            self._send_json(result)

        elif path == "/confirm":
            sid = data.get("session_id", "")
            field_key = data.get("field_key", "")
            value = data.get("value", "")
            if not all([sid, field_key, value]):
                self._send_json({"error": "session_id, field_key, and value required"}, 400)
                return
            result = engine.confirm_field(sid, field_key, value)
            self._send_json(result)

        elif path == "/gate":
            sid = data.get("session_id", "")
            if not sid:
                self._send_json({"error": "session_id required"}, 400)
                return
            result = engine.check_gate(sid)
            self._send_json(result)

        elif path == "/elicit":
            sid = data.get("session_id", "")
            if not sid:
                self._send_json({"error": "session_id required"}, 400)
                return
            result = engine.generate_elicitation(sid)
            self._send_json({"questions": result})

        elif path == "/assumptions":
            sid = data.get("session_id", "")
            if not sid:
                self._send_json({"error": "session_id required"}, 400)
                return
            result = engine.generate_assumptions(sid)
            self._send_json({"assumptions": result})

        else:
            self._send_json({"error": "Not found"}, 404)

    def log_message(self, format, *args):  # noqa: A002
        """Suppress default stderr logging."""


def run_rest_server(host: str = "127.0.0.1", port: int = 8420):
    """Start the REST API server."""
    server = HTTPServer((host, port), DraftHandler)
    print(f"DRAFT Protocol REST API running on http://{host}:{port}")
    print("Endpoints: /classify, /session, /map, /confirm, /gate, /elicit, /assumptions, /status, /health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
