# Benchmarks

These numbers come from real production use of DRAFT Protocol in daily AI-assisted development work. They are not synthetic. They are not cherry-picked. They include honest caveats about what we have and haven't measured yet.

## Usage Context

- **Environment:** Solo founder using DRAFT to govern all AI tool calls in a multi-MCP development lab (18 Docker containers, 9 MCP backends, PostgreSQL, Qdrant, Ollama)
- **Period:** November 2025 – February 2026
- **Sessions:** 50+ governed sessions across Casual, Standard, and Consequential tiers
- **Tooling:** Claude Desktop, VS Code, custom MCP servers, REST API

## Key Metrics

| Metric | Value | Context |
|---|---|---|
| **Assumptions caught per Consequential session** | ~3 avg | Wrong assumptions surfaced by Step 5 (Assumptions Check) before execution. These would have produced incorrect output without DRAFT. |
| **Dimensions screened per session** | ~30% | Inapplicable dimensions identified and skipped via Dimension Screening (v1.1). Reduces ceremony without reducing coverage. |
| **Adversarial gate tests passing** | 76/77 | Automated test harness for bypass attempts, injection detection, empty input handling, and tier manipulation. |
| **Pipeline overhead (Standard tier)** | ~45–90 seconds | Time added for elicitation before task execution begins. Varies by task complexity. |
| **Re-work prevented (estimated)** | ~60% reduction | Tasks that would have required full re-execution due to misinterpreted intent. Estimate based on sessions where Assumptions Check changed the execution plan. |

## What Assumptions Check Actually Catches

Real examples from production sessions (anonymized):

| Session Type | Assumption Surfaced | What Would Have Happened |
|---|---|---|
| Architecture decision | AI assumed new component should be a separate service | Would have built microservice when a library was needed |
| Documentation task | AI assumed audience was developers | Spec was for compliance reviewers — wrong tone, wrong depth |
| Code refactor | AI assumed backward compatibility required | Task was greenfield rewrite — compatibility constraint would have blocked the simplest solution |
| Config change | AI assumed all environments affected | Change was production-only — would have broken staging |

## What Dimension Screening Saves

In 50+ sessions, approximately 30% of DRAFT dimension mappings were screened as N/A with justification:

- **Flex (F)** most commonly screened: one-time tasks, throwaway scripts, exploratory work
- **Rules (R)** occasionally screened: tasks with no constraints beyond "make it work"
- **Test (T)** rarely screened: almost everything has evaluation criteria

Screening saves 15–30 seconds per session and eliminates irrelevant questions that cause ceremony fatigue — the #1 reason users abandon governance tools.

## Adversarial Testing

The automated test suite covers:

| Category | Tests | Pass Rate |
|---|---|---|
| Empty/whitespace input rejection | 8 | 8/8 |
| Minimum content threshold enforcement | 6 | 6/6 |
| OWASP LLM07 prompt extraction detection | 4 | 4/4 |
| Tier manipulation resistance | 12 | 12/12 |
| Gate bypass attempts | 15 | 14/15 |
| Session state integrity | 10 | 10/10 |
| Override audit completeness | 8 | 8/8 |
| Input validation edge cases | 14 | 14/14 |
| **Total** | **77** | **76/77 (98.7%)** |

The 1 failing test (gate bypass via rapid session cycling) is tracked as a known issue with a fix planned for v0.2.

## Honest Caveats

We believe in publishing what we know and what we don't:

- **No external deployments yet.** All data is from one user (the founder) in one environment. We expect different patterns from different users and workflows.
- **No control-group comparison.** We haven't run identical tasks with and without DRAFT to measure time-saved vs. time-added rigorously. The "60% re-work reduction" is an estimate, not a controlled measurement.
- **No multi-user data.** Sessions are single-user. Team dynamics (shared sessions, handoffs, conflicting assumptions) are untested.
- **LLM-enhanced vs. heuristic-only not benchmarked.** We use LLM-enhanced classification internally but haven't published comparison data for heuristic-only mode.

## Reproduce It Yourself

Run the benchmark suite against your own sessions:

```bash
# Run the full adversarial test suite
make test

# Or directly:
python -m pytest tests/ -v --tb=short

# Generate a coverage report
make coverage
```

If you're using DRAFT in production and want to contribute anonymized benchmark data, file an issue with the `benchmarks` label. We'll add community metrics as data becomes available.

## Comparison: Prevention vs. Detection

| | Output Guardrails (e.g., Guardrails AI, NeMo) | DRAFT Protocol |
|---|---|---|
| **When it acts** | After the LLM responds | Before the LLM acts |
| **What it checks** | Toxicity, format, policy, hallucination | Intent, scope, assumptions, completeness |
| **Failure mode** | Catches bad output after tokens are spent | Prevents bad calls entirely |
| **Overhead** | Per-response latency | Per-session setup (amortized across all calls) |
| **Evidence basis** | Synthetic validator benchmarks | Real governed sessions |
| **Complementary?** | Yes — DRAFT + output guardrails = defense-in-depth | Yes — output guardrails catch what intake misses |

DRAFT is not a replacement for output guardrails. It's the layer that makes them fire less often.

---

*DRAFT Protocol is Gate 1 (intake) in the [Vector Gate](https://github.com/manifold-vectors) pipeline. Benchmark data is updated as more sessions accumulate. Community contributions welcome.*
