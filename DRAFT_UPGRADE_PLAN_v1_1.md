---
title: "DRAFT UPGRADE PLAN v1 1"
date: 2026-04-24
modified: 2026-04-24
status: active
tags:
  - lab
  - doc
  - 05-knowledge
  - ip
  - draft
  - ude/state
aliases: []
related: []
ude_force: state
---
# DRAFT Protocol v1.1.0 Upgrade Plan
# Source: Lab DRAFT MCP (18 tools) + brain_library science + FLOW-1.0 evolution
# Target: Public draft-protocol repo (D:\VECTOR\draft-protocol)

## LAB → PUBLIC BACKPORT (features proven in production)

### 1. Batch Operations (3 new functions + 3 new MCP tools)
- confirm_batch(session_id, {field_key: value, ...}) → confirm multiple fields in one call
- quick_confirm_satisfied(session_id) → promote all SATISFIED→CONFIRMED in one call
- verify_batch(session_id, {index: bool, ...}) → verify multiple assumptions in one call
Source: Lab engine.py (tested, production since Session 22)
Impact: 50-60% reduction in tool call overhead per session

### 2. Devil's Advocate at ALL Tiers (scaled)
Current public: DA only at CONSEQUENTIAL
Lab evolution (FLOW-1.0 R2):
  CASUAL: 1-2 lightweight internal assumptions
  STANDARD: 2-3 assumptions with light DA
  CONSEQUENTIAL: 3-5 assumptions with full DA
Source: CIA Structured Analytic Techniques (Key Assumptions Check)
Brain corpus: "auto-generated assumptions are just restating confirmed fields, not testing anything"
Fix: LLM-powered assumption generation that creates genuinely falsifiable claims

### 3. LLM-Powered Assumptions (fix CF-011)
Current: assumptions just echo SATISFIED field extractions (rubber-stamp)
Fix: When LLM available, generate adversarial assumptions:
  - "What if [extracted D1] is the wrong scope?"
  - "What if [R3 forbidden] isn't actually forbidden?"
  - "What if [T1 success] can't be measured?"
Science: Cognitive debiasing through structured adversarial questioning (CIA SATs)

### 4. Hard Extraction Enforcement
Current public: LLM can fabricate extracted text for AMBIGUOUS/MISSING fields
Lab fix: Strip extracted content from non-SATISFIED fields
Code: if result["status"] in ("AMBIGUOUS", "MISSING"): result["extracted"] = ""

### 5. Escalation + De-escalation Tools
Current public: no escalate/deescalate in engine.py
Lab: escalate(session_id) and deescalate(session_id, reason) with audit trail
These are already in server.py MCP tools but missing from engine.py public

## SCIENCE-BACKED IMPROVEMENTS (from brain_library + biomimicry)

### 6. Collaborative Framing (PEACE + Motivational Interviewing)
Current: elicitation questions feel interrogatory
Fix: Add framing context to all elicitation outputs:
  - Signal purpose: "These questions help get this right"
  - Acknowledge expertise: "You know your domain — these questions seek your knowledge"
  - Scaffold: Provide example answers, not just questions
Source: DRAFT Protocol v1.1 spec §3.5 (written but not implemented in code)
Brain: GAP-03 "Interrogation Dynamics" documented in subconscious

### 7. Open Elicitation Phase (Cognitive Interview)
Current: AI interprets immediately after intake
Fix: For STANDARD+, add optional open_elicitation step between intake and map
  - Single open question: "Describe what you're trying to accomplish"
  - Human response becomes context for map_dimensions
  - Prevents anchoring bias (GAP-02 from brain corpus)
Source: Cognitive Interview, PEACE model, Motivational Interviewing
Brain: "7 of 8 comparison methodologies begin with unstructured info gathering"

### 8. Assumption Quality Scoring
Current: all assumptions equal weight
Fix: Score assumptions by:
  - Falsifiability: How testable is this claim? (0-1)
  - Impact: If wrong, how much rework? (0-1) 
  - Novelty: Is this a genuine risk or restating the obvious? (0-1)
  - Combined quality_score = (falsifiability + impact + novelty) / 3
  - Low-quality assumptions flagged for replacement
Source: CIA Key Assumptions Check quality criteria

### 9. Perfunctory Confirmation Detection (DFT-08)
Current: any string ≥3 chars accepted as confirmation
Fix: Detect perfunctory patterns:
  - Same value for multiple fields ("yes", "agreed", "as stated")
  - Value matches the AI's extracted suggestion exactly (rubber-stamp)
  - Very short value relative to question complexity
  - Flag but don't block — add warning to gate results
Source: DRAFT Protocol v1.1 spec DFT-08 conformance test
Brain: CF-011 "weak assumptions" pattern documented

### 10. Session Analytics (from FLOW-1.0)
Current: no session-level metrics
Fix: Add to elicitation_review output:
  - fields_per_minute: How fast were fields confirmed?
  - assumption_rejection_rate: What % of assumptions were rejected?
  - escalation_count: How many tier changes in this session?
  - confidence_distribution: Histogram of field confidence scores
Source: FLOW-1.0 review-at-pause pattern

## IMPLEMENTATION ORDER (by impact × effort)

1. confirm_batch + verify_batch + quick_confirm → 30min, 50% overhead reduction
2. LLM-powered assumptions with DA at all tiers → 1hr, fixes rubber-stamp problem
3. Hard extraction enforcement → 5min, security fix
4. Escalation/de-escalation in engine → 15min, feature parity
5. Collaborative framing on elicitation output → 20min, UX improvement
6. Perfunctory confirmation detection → 30min, quality gate
7. Assumption quality scoring → 30min, assumption quality
8. Open elicitation phase → 30min, anchoring prevention
9. Session analytics → 20min, observability
10. Version bump + CHANGELOG + tests → 30min

Total: ~4 hours for complete upgrade
