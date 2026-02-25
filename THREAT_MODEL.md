# Threat Model: Intake Governance Attack Surface

Most AI governance tools don't publish a threat model. We do, because if you're trusting DRAFT to sit between humans and AI execution, you should know exactly what it defends against, what it doesn't, and where the boundaries are.

---

## What DRAFT Defends Against

### 1. Intent Hijacking

**Attack:** The AI misinterprets ambiguous human input and executes a destructive action that was never intended.

**Example:** User says "clean up the database." AI interprets this as DROP TABLE instead of deleting expired rows.

**Defense:** DRAFT's 5-dimension mapping (Define, Rules, Artifacts, Flex, Test) forces explicit confirmation of goal (D1), scope (D3), constraints (A2), and success/failure criteria (T1/T2) before any execution. Ambiguity is surfaced, not assumed away.

**Severity if bypassed:** High — leads to irreversible actions based on wrong assumptions.

### 2. Assumption Poisoning

**Attack:** The AI builds a chain of reasonable-sounding but unchecked assumptions. Each assumption is individually plausible; the chain is collectively wrong.

**Example:** "Deploy the update" → AI assumes: latest branch, production environment, immediate rollout, no rollback plan. Each assumption is defensible individually. Together they create an unrecoverable deployment.

**Defense:** Step 5 (Assumptions Check) requires 3-5 falsifiable assumptions to be explicitly surfaced. At Consequential tier, Devil's Advocate actively challenges the strongest assumptions. Assumptions must be confirmed individually — batch confirmation is blocked.

**Severity if bypassed:** High — cascading failures from compounded wrong assumptions.

### 3. Ceremony Bypass

**Attack:** Users or AI systems skip governance steps to "save time," reducing the protocol to a rubber stamp.

**Example:** AI presents all fields as pre-filled defaults and asks "shall I proceed?" — the human clicks yes without engaging.

**Defense:** The no-exemption rule means every input passes through DRAFT. Casual tier reduces visibility but not enforcement. Confirmation quality monitoring (CF-012) detects cases where humans confirm without engaging. The Elicitation Review step (Step 7) audits whether real engagement occurred.

**Severity if bypassed:** Medium — governance exists on paper but provides no actual protection.

### 4. Scope Creep Injection

**Attack:** The task grows beyond its original confirmed scope during execution, accumulating unauthorized actions without re-triggering governance.

**Example:** "Update the homepage headline" slowly becomes "redesign the homepage, add new sections, change the navigation, and deploy to production."

**Defense:** DRAFT captures explicit scope boundaries (A2: constraints) and failure criteria (T2: what should NOT happen). Scope drift detection (G6 in the Guardian gate) flags when execution diverges from confirmed intent. Any material scope change requires a new DRAFT session.

**Severity if bypassed:** Medium — unauthorized work performed under cover of original authorization.

### 5. Tier Manipulation

**Attack:** A high-stakes action is classified at a lower governance tier to avoid scrutiny.

**Example:** A database migration is classified as CASUAL instead of CONSEQUENTIAL, skipping Devil's Advocate review and full assumption checking.

**Defense:** Auto-escalation rules trigger on specific patterns: canonical document changes → Consequential, destructive operations → Consequential, governance modifications → Consequential. Tier cannot be lowered without explicit founder/admin de-escalation, which is logged and auditable.

**Severity if bypassed:** High — consequential actions executed with minimal governance.

### 6. Confirmation Fatigue

**Attack:** The protocol asks so many questions that humans stop reading and confirm everything reflexively.

**Example:** 15 sequential confirmation prompts leads to a human clicking "yes" 15 times without reading any of them.

**Defense:** Dimension screening (SCID-5 derived) skips inapplicable sections. The two-option maximum rule (at Consequential tier) prevents decision overload. Targeted elicitation (Step 4) only asks about missing or ambiguous fields, not fields already clear from context. The goal is minimum necessary questions, not maximum coverage.

**Severity if bypassed:** Medium — governance theater replaces actual governance.

---

## What DRAFT Does NOT Defend Against

Honesty about limitations builds more trust than pretending they don't exist.

### Prompt Injection at the LLM Level

DRAFT governs intake — the space between human intent and AI action. It does not validate what the LLM generates internally. If a prompt injection bypasses the LLM's own safety mechanisms, DRAFT has already done its job (confirmed the legitimate intent) and the failure is downstream.

**Mitigation:** Use output guardrails (Guardrails AI, NeMo Guardrails) after DRAFT. This is defense in depth: DRAFT prevents bad calls, output guardrails catch bad responses.

### Malicious Human Operators

If the human intentionally provides false confirmations to DRAFT — confirming destructive intent as their genuine goal — DRAFT will gate it through. DRAFT verifies that AI understands human intent. It does not override human intent.

**Mitigation:** Authorization controls and approval chains (not DRAFT's responsibility) should gate who can confirm consequential actions. The audit trail provides forensic evidence.

### Social Engineering of the AI

If an attacker convinces the AI (outside of DRAFT) to misrepresent its capabilities or bypass governance, the failure is in the AI's behavioral compliance, not in the intake protocol.

**Mitigation:** The three-gate pipeline (DRAFT → Guardian → GovMCP) means no single gate can be socially engineered independently. Guardian (Gate 2) validates that DRAFT was actually run. GovMCP (Gate 3) enforces execution boundaries regardless of what Gates 1 and 2 produced.

### Data Exfiltration via Session Content

DRAFT sessions contain confirmed intent, assumptions, and scope. If an attacker gains access to session storage, they can see what tasks were authorized. DRAFT does not encrypt session data at rest by default.

**Mitigation:** v0.2 will add API key authentication. For sensitive environments, run DRAFT behind your existing auth infrastructure and encrypt the session database.

---

## Defense-in-Depth: The Three-Gate Pipeline

DRAFT is Gate 1 in a three-gate architecture. Each gate addresses a different failure mode:

```
Human Intent
    │
    ▼
┌─────────┐   Gate 1: Did the AI understand what you want?
│  DRAFT  │   Prevents: intent hijacking, assumption poisoning,
│ (intake)│   ceremony bypass, scope creep, tier manipulation
└────┬────┘
     │
     ▼
┌──────────┐  Gate 2: Does the AI's response comply with rules?
│ Guardian │  Prevents: authority claims, unlabeled speculation,
│ (output) │  governance bypass, scope drift, consciousness claims
└────┬─────┘
     │
     ▼
┌─────────┐   Gate 3: Is the execution authorized and bounded?
│ GovMCP  │   Prevents: unauthorized file ops, unaudited commands,
│  (exec) │   privilege escalation, resource exhaustion
└────┬────┘
     │
     ▼
  Execution
```

No single gate is sufficient. DRAFT without Guardian means unvalidated output. Guardian without DRAFT means validated output for the wrong task. Both without GovMCP means governed intent with ungoverned execution.

---

## Reporting Security Issues

If you discover a vulnerability in DRAFT Protocol, please report it via our [security policy](SECURITY.md). We take security reports seriously and will respond within 48 hours.

Do not file security vulnerabilities as public GitHub issues.

---

*DRAFT Protocol is Gate 1 (intake) in the [Vector Gate](https://github.com/manifold-vectors) pipeline. This threat model covers the intake governance layer. For the full three-gate security architecture, see Vector Gate.*
