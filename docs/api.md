# REST API Reference

> **⚠️ Security Warning:** The REST API is designed for **local development only**. It binds to `127.0.0.1` by default and should never be exposed to the public internet without authentication. If you need remote access, place the server behind a reverse proxy with TLS and authentication, or set `DRAFT_REST_AUTH` to require a bearer token. See [SECURITY.md](../SECURITY.md) and [CF-013](../CONFORMANCE.md#cf-013-rest-api-missing-authentication) for details.

Base URL: `http://127.0.0.1:8420` (configurable via `DRAFT_HOST` and `DRAFT_PORT`)

Start the server:

```bash
python -m draft_protocol --transport rest --port 8420
```

All endpoints accept and return JSON. Full CORS support for browser clients.

## Endpoints

### `GET /health`

Health check.

**Response:**

```json
{ "status": "ok", "service": "draft-protocol", "version": "0.1.0" }
```

### `GET /status`

Get the active (most recent unclosed) session.

**Response (active session):**

```json
{
  "active": true,
  "session_id": "a1b2c3d4e5f6",
  "tier": "STANDARD",
  "intent": "Build a REST API for user management",
  "gate": "[BLOCKED]: 3/8",
  "created_at": "2026-02-22T03:00:00+00:00"
}
```

**Response (no session):**

```json
{ "active": false, "message": "No active session" }
```

### `POST /classify`

Classify a message into CASUAL / STANDARD / CONSEQUENTIAL without creating a session.

**Request:**

```json
{ "message": "Build a Python CLI that backs up PostgreSQL" }
```

**Response:**

```json
{
  "tier": "STANDARD",
  "reasoning": "Keyword match: build",
  "confidence": 0.85
}
```

### `POST /session`

Create a new DRAFT session (closes any existing active session first).

**Request:**

```json
{
  "message": "Restructure the authentication system",
  "tier_override": "CONSEQUENTIAL"
}
```

- `message` (required): The user's intent description.
- `tier_override` (optional): Force a specific tier.

**Response:**

```json
{
  "session_id": "a1b2c3d4e5f6",
  "tier": "CONSEQUENTIAL",
  "reasoning": "Keyword match: restructure",
  "confidence": 0.95
}
```

### `POST /map`

Map DRAFT dimensions against user context.

**Request:**

```json
{
  "session_id": "a1b2c3d4e5f6",
  "context": "Build a REST API for user management with CRUD operations. Uses PostgreSQL. Only admin users can delete accounts. Success means all endpoints pass integration tests."
}
```

**Response:**

```json
{
  "D": {
    "D1": { "question": "What exactly is being created?", "status": "SATISFIED", "confidence": 0.6, "extracted": "Keyword match (2 hits)" },
    "D2": { "question": "What domain does it belong to?", "status": "AMBIGUOUS", "confidence": 0.4, "extracted": "Partial keyword match" }
  },
  "R": { "_screened": true, "_reason": "Rules (Operation & Limits) not applicable" },
  "T": {
    "T1": { "question": "How is success defined?", "status": "SATISFIED", "confidence": 0.6, "extracted": "Keyword match (2 hits)" }
  }
}
```

### `POST /confirm`

Confirm a DRAFT field with a human-provided answer.

**Request:**

```json
{
  "session_id": "a1b2c3d4e5f6",
  "field_key": "D1",
  "value": "A REST API for user management with CRUD endpoints"
}
```

**Response:**

```json
{ "field": "D1", "status": "CONFIRMED", "value": "A REST API for user management with CRUD endpoints" }
```

**Error (empty value):**

```json
{ "error": "Cannot confirm D1 with empty value.", "field": "D1", "status": "REJECTED" }
```

### `POST /gate`

Check if all applicable fields are confirmed.

**Request:**

```json
{ "session_id": "a1b2c3d4e5f6" }
```

**Response (blocked):**

```json
{
  "passed": false,
  "confirmed": 5,
  "total": 8,
  "blockers": ["D3: MISSING", "R4: AMBIGUOUS", "T2: MISSING"],
  "summary": "[BLOCKED]: 5/8"
}
```

**Response (passed):**

```json
{
  "passed": true,
  "confirmed": 8,
  "total": 8,
  "blockers": [],
  "summary": "[PASS]: 8/8"
}
```

### `POST /elicit`

Generate targeted questions for MISSING and AMBIGUOUS fields.

**Request:**

```json
{ "session_id": "a1b2c3d4e5f6" }
```

**Response:**

```json
{
  "questions": [
    {
      "dimension": "D — Define (Existence & ROI)",
      "field": "D3",
      "question": "What fails without it?",
      "current_status": "MISSING",
      "confidence": 0.3,
      "suggestion": "If this didn't exist, what downstream work would be blocked?"
    }
  ]
}
```

### `POST /assumptions`

Generate falsifiable assumptions from the session.

**Request:**

```json
{ "session_id": "a1b2c3d4e5f6" }
```

**Response:**

```json
{
  "assumptions": [
    {
      "claim": "For D1: Keyword match (2 hits)",
      "source": "context_extraction",
      "confidence": 0.6,
      "falsifier": "If wrong, re-elicit D1."
    }
  ]
}
```

## Error Handling

All error responses use HTTP 400 or 404 with a JSON body:

```json
{ "error": "session_id and context required" }
```

## CORS

All endpoints include CORS headers for browser access:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

`OPTIONS` requests return 204 for preflight.
