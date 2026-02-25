# Methodology: Cross-Disciplinary Validation of DRAFT Protocol

DRAFT Protocol was not designed in isolation. After shipping v1.0, we stress-tested the entire framework against **eight established human-elicitation methodologies** — each with decades of empirical validation in environments where extracting accurate information from humans is critical and mistakes have real consequences.

This document records what we tested, what broke, what we fixed, and how each source methodology contributed to the current 7-step pipeline.

## Why Cross-Disciplinary?

AI governance tools are almost exclusively built by engineers for engineers. The result: technically sound systems that fail at the human interface. Humans don't behave like API contracts. They omit context, assume shared knowledge, confirm things they haven't read, and resent being interrogated.

The fields that have solved these problems — forensic psychology, intelligence analysis, clinical psychiatry, emergency medicine, investigative interviewing — have spent decades refining how to extract accurate intent from humans under pressure, ambiguity, or resistance. We borrowed from them.

## Source Methodologies

| Methodology | Field | Origin | What We Borrowed |
|---|---|---|---|
| **Cognitive Interview** | Forensic Psychology | Fisher & Geiselman, 1985 | Freeform recall before imposing structure |
| **PEACE Model** | Investigative Interviewing | UK Home Office, 1992 | Engage phase (collaborative framing), Evaluation phase (self-review) |
| **Motivational Interviewing / OARS** | Clinical Psychology | Miller & Rollnick, 1983 | Elicit-Provide-Elicit pattern, reflective listening, autonomy respect |
| **Structured Analytic Techniques** | Intelligence Analysis | Heuer & Pherson (CIA), 2010 | Key Assumptions Check, Devil's Advocate for high-stakes decisions |
| **SCID-5 / Biopsychosocial Model** | Psychiatry | APA / Engel, 1977 | Modular screening with skip-logic for inapplicable sections |
| **OPQRST / SAMPLE** | Emergency Medicine | Paramedic training standards | Severity-based scaling (triage → depth) |
| **Requirements Elicitation** | Software Engineering | IEEE 830 / SEI-CMU | Failure mode catalog, completeness criteria |
| **Elicitation Interview** | HCI / Phenomenology | Petitmengin, 2006 | Question framing rules (prefer what/how over why) |

## Stress-Test Process

We took DRAFT v1.0's 4-step pipeline and ran each step against each methodology's core principles. The question: **"Would a trained practitioner in this field accept our elicitation approach, or would they flag gaps?"**

Five gaps emerged. All five were real.

## Gaps Found in v1.0

| # | Gap | Source That Exposed It | Severity | What Went Wrong |
|---|---|---|---|---|
| 1 | **Premature structuring** | Cognitive Interview, PEACE | High | v1.0 jumped straight to dimensional mapping. No space for the human to describe what they actually wanted in their own words first. Trained interviewers never start with structured questions — they start with open recall. |
| 2 | **No assumption surfacing** | CIA Structured Analytic Techniques | High | v1.0 mapped dimensions and confirmed them, but never explicitly asked "what am I assuming here that might be wrong?" Intelligence analysts treat this as mandatory for any consequential assessment. |
| 3 | **No self-evaluation** | PEACE Evaluation, CIA SATs review | Medium | v1.0 had no mechanism for the AI to audit its own elicitation quality. Did the human actually engage, or just click "yes" to everything? PEACE-trained interviewers always review their own performance. |
| 4 | **Ceremony fatigue on inapplicable dimensions** | SCID-5 modular assessment | Medium | v1.0 mapped all five dimensions at full depth regardless of relevance. A one-time script doesn't need a Flex (change management) dimension. Psychiatrists screen sections before diving deep. |
| 5 | **Interrogation dynamics** | PEACE Engage phase, MI Spirit | Medium | v1.0's question format could feel like a bureaucratic checklist. When humans perceive questions as obstruction, they short-circuit the protocol. This is a framing failure, not a protocol failure. |

## Fixes Applied (v1.0 → v1.1)

Every fix was **additive** — no existing architecture was removed. The five DRAFT dimensions, stop conditions, tier scaling, no-exemption rule, and confirmation gate all survived unchanged.

| Gap | Fix | New Pipeline Step | Source |
|---|---|---|---|
| Premature structuring | Added freeform recall phase before any dimensional mapping | **Step 1: Open Elicitation** | Cognitive Interview, PEACE, MI |
| No assumption surfacing | Added explicit bias mitigation with Devil's Advocate at Consequential tier | **Step 5: Assumptions Check** | CIA Structured Analytic Techniques |
| No self-evaluation | Added quality audit of elicitation process itself | **Step 7: Elicitation Review** | PEACE Evaluation, CIA SATs review |
| Ceremony fatigue | Added skip-logic for inapplicable dimensions with justification | **Section 2.6: Dimension Screening** | SCID-5 modular assessment |
| Interrogation dynamics | Added collaborative framing guidance throughout | **Section 3.5: Collaborative Framing** | PEACE Engage, MI Spirit |

Additionally, **Targeted Elicitation** (Step 4) was enhanced with question framing rules (prefer what/how over why) and the Elicit-Provide-Elicit pattern from Motivational Interviewing, where the AI asks what the human already knows before offering suggestions.

## Pipeline Evolution

**v1.0 (4 steps):**
1. Interpretation → 2. Mapping → 3. Elicitation → 4. Confirmation Gate

**v1.1 (7 steps):**
1. Open Elicitation → 2. Provisional Interpretation → 3. Mapping + Screening → 4. Targeted Elicitation → 5. Assumptions Check → 6. Confirmation Gate → 7. Elicitation Review

| Step | Name | Source | Casual | Standard | Consequential |
|---|---|---|---|---|---|
| 1 | Open Elicitation | CI, PEACE, MI | Skip | Required | Required |
| 2 | Provisional Interpretation | v1.0 | Internal | Visible | Visible |
| 3 | Mapping + Screening | v1.0 + SCID-5 | Internal | Visible | Visible |
| 4 | Targeted Elicitation | v1.0 + EI, MI | Skip | Required | Required |
| 5 | Assumptions Check | CIA SATs | Skip | Required | Required + Devil's Advocate |
| 6 | Confirmation Gate | v1.0 | Internal | Required | Required |
| 7 | Elicitation Review | PEACE, SATs | Skip | Recommended | Required |

## What This Means for Users

You don't need to know any of these methodologies to use DRAFT. The protocol embeds their principles mechanically:

- **Open Elicitation** prevents the AI from jumping to conclusions about what you meant.
- **Assumptions Check** forces the AI to say "here's what I'm assuming — am I wrong?" before acting.
- **Dimension Screening** skips irrelevant questions so you're not answering things that don't apply.
- **Collaborative Framing** makes the process feel like refinement, not interrogation.
- **Elicitation Review** catches cases where you said "sure" without actually engaging.

## What This Means for Researchers

Every feature borrowed from an established methodology is traceable to its source. If you're evaluating DRAFT for academic work, compliance review, or comparison with other governance approaches, the provenance chain is explicit.

We welcome challenges to this analysis. If a methodology we cited would flag additional gaps in the current v1.1 pipeline, we want to know. File an issue with the `methodology` label.

## How to Cite

If referencing this methodology validation in academic or professional work:

> Goytia, G. (2026). DRAFT Protocol: Cross-disciplinary validation of structured intent elicitation for AI tool governance. Manifold Vector LLC. https://github.com/manifold-vectors/draft-protocol/blob/main/METHODOLOGY.md

---

*DRAFT Protocol is Gate 1 (intake) in the [Vector Gate](https://github.com/manifold-vectors) pipeline. This document covers the methodology behind the elicitation layer. Output validation (Gate 2) and execution governance (Gate 3) are separate components under active development.*
