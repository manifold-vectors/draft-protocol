# Vector Gate Product Portfolio Standard v1.0

**Document ID:** VG-PROD-001  
**Status:** CANONICAL  
**IP Classification:** L2 (Internal Operations)  
**DRAFT Session:** 9f55b458-352 | CONSEQUENTIAL | PASS 19/19  
**Created:** 2026-02-22  

> **INTERNAL — FOUNDER-ONLY.** This document defines what Manifold Vector LLC sells, at what price, to whom, and why. It is NOT a marketing document, sales deck, or technical specification.

---

## 1. Purpose & Scope

This standard defines the complete product portfolio for Vector Gate, the three-gate AI governance pipeline developed by Manifold Vector LLC. It establishes product names, descriptions, pricing tiers, competitive positioning, ship vehicles, release criteria, and IP classification for each product.

**Authority:** Founder-only. All pricing decisions, product additions/removals, tier restructuring, and positioning changes require explicit founder authorization per BAMS.

**Derived from:** Market research conducted February 2026 covering AI governance platforms (Credo AI, OneTrust, Holistic AI, IBM watsonx), open-source guardrails (NVIDIA NeMo, Guardrails AI, DynamoGuard), MCP ecosystem dynamics, EU AI Act compliance landscape, and enterprise pricing benchmarks.

---

## 2. Market Context

### 2.1 Market Size & Growth

The AI governance market is valued at approximately $620M–$940M (2024–2025) and projected to reach $7.38B by 2030 at a 51% CAGR. Gartner projects AI data governance spending of $492M in 2026 alone. The market is growing faster than the AI industry itself, driven by regulatory enforcement and the shift from voluntary to mandatory compliance.

### 2.2 Regulatory Drivers

The EU AI Act enters its critical enforcement phase on August 2, 2026, when high-risk AI system obligations take full effect. Fines reach up to €35M or 7% of global annual turnover. Only 18% of organizations have fully implemented AI governance frameworks despite 88% using AI operationally. The Colorado AI Act takes effect June 2026. NIST AI RMF and ISO 42001 are the de facto U.S. and international standards, respectively.

### 2.3 The Structural Gap

Every existing competitor operates at the output layer only. No product on the market governs all three attack surfaces of agentic AI:

| Surface | What Competitors Do | What Vector Gate Does |
|---------|--------------------|-----------------------|
| **Intake** (pre-LLM) | Nothing | DRAFT Protocol classifies tier, maps intent, elicits missing context before the AI acts |
| **Output** (post-LLM) | NeMo Guardrails, Guardrails AI check toxicity, PII, hallucination after generation | Guardian Core checks constitutional compliance (G1–G8 rules) with cross-gate verification |
| **Execution** (tool use) | Nothing (MCP spec says it cannot enforce security at protocol level) | GovMCP wraps any MCP server with authorization tiers, audit trails, and T0 gates |

---

## 3. Product Portfolio

The portfolio follows a funnel strategy: free products create demand and ecosystem lock-in; paid products capture value.

### 3.1 Product Map

| Product | Description | Price | Gate | Status | Ship Vehicle |
|---------|------------|-------|------|--------|-------------|
| **DRAFT Protocol** | Open-source intake governance. Tier classification, intent mapping, elicitation pipeline. Multi-LLM, multi-transport, Chrome extension. | Free (Apache 2.0) | Gate 1 | ✅ BUILT | PyPI + GitHub |
| **GovMCP** | Open-source execution governance. Wraps any MCP server with authorization tiers, T0 gates, session authorization, audit trails. | Free (Apache 2.0) | Gate 3 | 🟡 LAB-READY | PyPI + GitHub |
| **Guardian Core** | Output compliance engine. G1–G8 constitutional rules, cross-gate verification, audit-grade evidence, NIST/EU AI Act compliance reports. | **$499–$5K/mo** | Gate 2 | 🟡 LAB-READY | Docker + PyPI + SaaS |
| **Vector Gate Suite** | Unified three-gate pipeline. All gates wired with cross-gate verification, single Docker Compose deployment, enterprise policy management. | **$24K–$60K/yr** | All 3 | 🟡 LAB-READY | Docker Compose |
| **Vector Gem SDK** | User-facing trust indicator. Kintsugi degradation model (cracks on violation, gold repair lines). Gem tiers: Unrated/Rough/Polished/Brilliant. | Free | UX Layer | 🔵 SPECIFIED | SDK/API |

### 3.2 Pricing Tiers (Market-Validated)

#### DRAFT Protocol
Free forever (Apache 2.0). Adoption funnel. Chrome extension, multi-transport REST API, and core classification pipeline remain free. Future enterprise features (hosted classification endpoints, team dashboards, compliance reporting integrations) will be paid add-ons.

**Market validation:** Guardrails AI follows identical model. 5.9K GitHub stars, 10K+ monthly downloads, $7.5M seed funding on this exact strategy.

#### GovMCP
Free forever (Apache 2.0). Gateway to ecosystem. Every developer who installs GovMCP experiences authorization tiers and audit trails, creating natural demand for Guardian Core.

**Market validation:** MCP ecosystem is majority free/open-source. Free GovMCP means every MCP client config example references it.

#### Guardian Core

| Tier | Price | Features | Deployment | Target |
|------|-------|----------|------------|--------|
| Self-Hosted Open Core | Free | Limited G1–G8 rules, no dashboard, no audit export, no cross-gate | Docker | Evaluation / solo devs |
| Guardian Pro | **$499/mo** | Full G1–G8, dashboard, audit trails, cross-gate, NIST/EU AI Act reports | SaaS or self-hosted | Startups, SMBs |
| Guardian Enterprise | **$2K–$5K/mo** | VPC deployment, custom rules, dedicated support, SOC 2 artifacts, SLA | VPC / on-prem | Mid-market, regulated |

**Market validation:** CO-AIMS prices at $199–$999/mo for state-specific compliance. OneTrust starts at $50K–$100K+/yr. Guardian Pro at $499/mo fills the gap. A company spending $2M/yr on AI (governance budget $6K–$10K/yr) can afford Guardian Pro at $5,988/yr.

#### Vector Gate Suite
Enterprise contract: $24,000–$60,000/year. Competes with Credo AI and OneTrust at 10–50% of their price, with runtime enforcement vs. governance dashboards.

**Market validation:** OneTrust total year-one: $65K–$150K+. Credo AI similar. Vector Gate Suite delivers runtime enforcement at a fraction of cost.

#### Vector Gem SDK
Free. Standalone SDK + embedded in Suite. Creates market pressure: developers without a Gem look ungoverned. EU AI Act Article 50 transparency compliance, visible.

### 3.3 Internal Tools (NOT Products)

| Tool | Purpose | Why Not a Product |
|------|---------|-------------------|
| Cortex MCP | Unified retrieval across Memory, RAG, Subconscious | Commodity retrieval — no moat |
| Memory MCP | Structured fact storage with hybrid search | Commodity memory — Mem0 etc. |
| RAG MCP | Document search with BM25 + vector hybrid | Commodity RAG — dozens exist |

---

## 4. Competitive Positioning

### 4.1 Competitive Map

| Competitor | Category | Intake Gov. | Output Gov. | Exec. Gov. | Price Range |
|-----------|----------|-------------|-------------|------------|-------------|
| **Vector Gate** | Three-Gate Pipeline | ✅ DRAFT | ✅ Guardian | ✅ GovMCP | Free – $60K/yr |
| NeMo Guardrails | Output Guardrails | ❌ | ✅ | ❌ | Free – $4.5K/GPU/yr |
| Guardrails AI | Output Validation | ❌ | ✅ | ❌ | Free – Enterprise |
| Credo AI | Enterprise Platform | ❌ | Partial | ❌ | $50K–$150K+/yr |
| OneTrust | Enterprise Platform | ❌ | Partial | ❌ | $65K–$150K+/yr |
| CO-AIMS | State Compliance SaaS | ❌ | ❌ | ❌ | $2.4K–$12K/yr |

### 4.2 Key Differentiators

1. **Only three-gate pipeline.** No competitor governs intake, output, AND execution.
2. **MCP-native.** Built for the MCP ecosystem. The protocol spec says it can't enforce security — Vector Gate is the enforcement layer.
3. **Mechanical enforcement, not behavioral.** Guardian blocks non-compliant responses mechanically. Not prompt engineering.
4. **Developer-first.** pip install, MCP config, done. No sales calls to get started.
5. **Cross-gate verification.** Guardian reads DRAFT's state. GovMCP enforces DRAFT boundaries. No competitor has this.

---

## 5. Release Criteria

| Product | Criteria | LLC Required | Blocker |
|---------|----------|:---:|---------|
| DRAFT Protocol | 46/46 tests, CI green, README, PyPI package, Chrome extension on 8 platforms | Yes | **LLC approval pending** |
| GovMCP | Extraction complete, zero lab deps, 40+ tests, T0 docs, audit trail, PyPI | Yes | Extraction not started |
| Guardian Core | Extraction complete, 34+ adversarial tests, G1–G8, cross-gate, dashboard, Docker | Yes | Extraction not started |
| Vector Gate Suite | All 3 gates extracted + passing, Docker Compose, cross-gate E2E, docs | Yes | Depends on Gate 2+3 |
| Vector Gem SDK | Gem tiers, kintsugi model, trust API, 3+ frontend integrations | Yes | Not yet built |

---

## 6. Go-to-Market Strategy

### 6.1 Funnel Logic

**Stage 1 — Awareness:** Developer discovers DRAFT Protocol (free, pip install). Classifies first AI interaction. Sees tier labels. Realizes their agent has no intake governance.

**Stage 2 — Ecosystem:** Installs GovMCP (free). Adds Gem SDK (free). Their AI system has visible governance. Competitors' don't.

**Stage 3 — Conversion:** Needs output compliance. EU AI Act deadline. Buys Guardian Core ($499/mo). For full pipeline, upgrades to Vector Gate Suite ($24K–$60K/yr).

### 6.2 Timing

EU AI Act high-risk rules effective August 2, 2026 (~5 months). 40% of enterprises embedding agents by end 2026. Only 6% have advanced AI security strategies. Window of opportunity before enterprise platforms adapt to MCP.

### 6.3 First Actions (Post-LLC)

1. Transfer draft-protocol to Manifold Vector LLC org. Publish to PyPI.
2. Extract GovMCP. Standalone repo. Publish to PyPI.
3. Extract Guardian Core. Docker image. Stripe billing.
4. Vector Gate Suite Docker Compose. Cross-gate wiring.
5. Vector Gem SDK. React, Vue, vanilla JS integration examples.

---

## 7. IP Classification

| Product | IP Tier | License | Public | Protected |
|---------|---------|---------|--------|-----------|
| DRAFT Protocol | L0 (Public) | Apache 2.0 | All source, docs, tests | Nothing |
| GovMCP | L0 (Public) | Apache 2.0 | All source, docs, tests | Nothing |
| Guardian Core | L1 (Commercial) | BSL / Proprietary | Open core, API docs | Full rules, cross-gate, dashboard, audit |
| Vector Gate Suite | L1 (Commercial) | Proprietary | Architecture overview, API docs | Cross-gate wiring, configs, enterprise features |
| Vector Gem SDK | L0 (Public) | Apache 2.0 / MIT | SDK source, examples | Visual design assets (trademark) |
| Internal Tools | L3 (Internal) | N/A | Nothing | All source and configs |

---

## 8. Review & Amendment

**Review triggers:** (1) New competitor in AI governance MCP space, (2) EU AI Act changes, (3) first customer feedback, (4) product extraction complete, (5) quarterly pricing review.

**Forbidden changes:** (1) Removing free tier from DRAFT Protocol, (2) making Guardian Core free, (3) merging products without founder approval, (4) publishing competitor trade secrets, (5) changing IP classification without review.

**Amendment authority:** Founder only. Tracked in VERSION REGISTRY.

---

*Manifold Vector LLC — INTERNAL — VG-PROD-001 v1.0*
