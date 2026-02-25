# Conformance Findings

DRAFT Protocol publishes every conformance finding from production use. This practice is borrowed from aviation safety culture, where incident reporting prevents future failures and transparency builds trust.

Every finding gets a CF-ID, root cause analysis, fix, and extracted rule. Findings are never deleted — they're part of the protocol's permanent record.

## Response Commitment

- **Root cause identified:** within 48 hours of discovery
- **Extracted rule published:** within 1 week
- **Fix shipped:** within 2 weeks (or documented as accepted risk)

## Filing a Conformance Finding

Found a gap? File an issue with the `conformance` label using this template:

```
**CF-ID:** (assigned on triage)
**Discovered:** [date]
**Context:** [what you were doing]
**Expected:** [what DRAFT should have done]
**Actual:** [what happened instead]
**Severity:** CRITICAL / HIGH / MEDIUM / LOW
```

## Active Findings

### CF-010: One-Way Dimension Screening

| Field | Value |
|---|---|
| **Discovered** | 2026-02-18 |
| **Context** | Production governed session — one-time task |
| **Severity** | MEDIUM |
| **Root Cause** | Dimension screening (v1.1 addition) correctly marked Flex as N/A, but provided no mechanism for the human to override and re-include a screened dimension. Screening was one-way. |
| **Fix** | Added `draft_unscreen` operation. Human can override any N/A classification with justification. |
| **Extracted Rule** | Every automated classification must be human-overridable. One-way gates create blind spots. |
| **Status** | FIXED in v0.1.0 |

### CF-011: Manual Assumptions Not Tracked

| Field | Value |
|---|---|
| **Discovered** | 2026-02-19 |
| **Context** | Consequential session — architecture decision |
| **Severity** | HIGH |
| **Root Cause** | Assumptions Check (Step 5) surfaced assumptions from the AI's interpretation, but the human could not manually add assumptions they were aware of but the AI missed. The check was AI-generated only. |
| **Fix** | Added `draft_add_assumption` operation. Humans can inject their own assumptions into the check. |
| **Extracted Rule** | Assumption surfacing must be bidirectional. The human often knows risks the AI cannot infer. |
| **Status** | FIXED in v0.1.0 |

### CF-012: Perfunctory Confirmation Not Flagged at Standard Tier

| Field | Value |
|---|---|
| **Discovered** | 2026-02-20 |
| **Context** | Standard session — human confirmed 4 inferred fields with "yes" in rapid succession |
| **Severity** | MEDIUM |
| **Root Cause** | Elicitation Review (Step 7) is only mandatory at Consequential tier. At Standard tier, rapid "yes" to multiple inferred fields went unchallenged. The protocol assumed Standard-tier users would engage meaningfully. |
| **Fix** | Added heuristic: if >3 Inferred fields are confirmed in sequence without elaboration, flag for re-engagement regardless of tier. |
| **Extracted Rule** | Confirmation quality checks should trigger on behavior patterns, not just tier classification. |
| **Status** | FIXED in v0.1.0 |

### CF-013: REST API Missing Authentication

| Field | Value |
|---|---|
| **Discovered** | 2026-02-22 |
| **Context** | Security review of HTTP transport |
| **Severity** | HIGH |
| **Root Cause** | REST transport launched with `DRAFT_REST_CORS=*` default and no authentication mechanism. Any client on the network could interact with active sessions. |
| **Fix** | Added `DRAFT_REST_AUTH` environment variable for bearer token authentication. CORS default narrowed. Documented in security notes. |
| **Extracted Rule** | Every network-exposed endpoint ships with authentication. Open defaults are not acceptable for governance tools. |
| **Status** | FIXED in v0.1.0 |

## Resolved Findings Summary

| CF-ID | Severity | Category | Status |
|---|---|---|---|
| CF-010 | MEDIUM | Screening | FIXED v0.1.0 |
| CF-011 | HIGH | Assumptions | FIXED v0.1.0 |
| CF-012 | MEDIUM | Confirmation Quality | FIXED v0.1.0 |
| CF-013 | HIGH | Security | FIXED v0.1.0 |

## Why We Publish Failures

Most projects hide their bugs. We publish ours because:

1. **Trust requires transparency.** If we claim DRAFT prevents mistakes, you should see the mistakes we've already found and fixed in the protocol itself.
2. **Patterns prevent recurrence.** Every extracted rule becomes a design constraint for future features.
3. **Contributors need context.** Understanding what broke and why helps contributors make better design decisions.
4. **Governance tools must self-govern.** A protocol that claims to surface assumptions should surface its own.

---

*DRAFT Protocol is Gate 1 (intake) in the [Vector Gate](https://github.com/manifold-vectors) pipeline. Conformance findings are tracked indefinitely and never removed from this document.*
