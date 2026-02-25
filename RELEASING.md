# Release Gate Checklist

**Rule:** No public release (PyPI, GitHub tag, announcement) until every box is checked.
**Origin:** Builder's blindness — v0.1.0 shipped with four documentation gaps that a new user would hit in the first 10 minutes. This gate prevents that class of error.

---

## Gate 1 — Stranger Test (mandatory)

> Can someone who has never seen this repo install, configure, and complete a round-trip in under 10 minutes using only the README?

- [ ] **Install path works cold.** `pip install draft-protocol` (or equivalent) on a clean venv produces a working install with zero undocumented steps.
- [ ] **Minimal working example exists.** README contains a copy-pasteable end-to-end transcript showing input → DRAFT session → confirmed output.
- [ ] **All provider limitations documented.** If a default backend requires credentials, API keys, or has known incompatibilities (e.g., Anthropic embeddings model support), the README says so before the user hits the error.
- [ ] **Security boundaries stated.** If a component binds to a port, the docs state the intended network scope (localhost-only, LAN, public) and what happens if exposed.
- [ ] **Error messages are actionable.** The top 5 most likely first-run errors produce messages that tell the user what to do, not just what failed.

## Gate 2 — Documentation Completeness

- [ ] **README quick-start matches current API.** Every code example in the README runs against the version being released.
- [ ] **CHANGELOG updated.** New version entry with date, summary, breaking changes (if any).
- [ ] **All public docs have entry points.** Long reference docs (CONFORMANCE, THREAT_MODEL, etc.) include a quick-scan index or summary table at the top.
- [ ] **API docs match implementation.** Every public function/endpoint is documented. No undocumented parameters, no stale signatures.
- [ ] **Known limitations section exists.** Anything that doesn't work yet, works differently than expected, or requires workarounds is listed explicitly.

## Gate 3 — Code Quality

- [ ] **All tests pass.** Full suite, not just smoke tests.
- [ ] **Adversarial tests pass.** If an adversarial suite exists, it runs clean. If it doesn't exist yet, that's a blocker for any version beyond 0.x.
- [ ] **Linter/formatter clean.** `ruff check` and `ruff format --check` produce zero findings.
- [ ] **Type checking clean.** `mypy` (or equivalent) passes with no errors on public API surface.
- [ ] **No secrets in repo.** Grep for API keys, tokens, passwords, internal URLs. Automated via pre-commit hook.

## Gate 4 — Release Mechanics

- [ ] **Version bumped.** `pyproject.toml`, `__init__.py`, and any other version references match.
- [ ] **Git tag matches version.** Tag format: `v{major}.{minor}.{patch}`.
- [ ] **CI pipeline green.** GitHub Actions (or equivalent) passes on the release branch.
- [ ] **Package builds locally.** `python -m build` produces a wheel and sdist that install cleanly.
- [ ] **LICENSE file present and correct.** Apache 2.0 (or as specified). No stale headers.

## Gate 5 — Portfolio Consistency (multi-repo only)

- [ ] **Cross-repo references valid.** If this package references other Vector Systems packages (GovMCP, Guardian), version pins are correct and documented.
- [ ] **Shared terminology consistent.** Key terms (DRAFT, gate, tier, dimension) match definitions across all public repos.
- [ ] **Landing page / org README updated.** The GitHub org page reflects the new release.

---

## Post-Release

- [ ] **PyPI page renders correctly.** Check the published page — broken markdown is common.
- [ ] **Install from PyPI works.** Fresh venv, `pip install draft-protocol=={version}`, run the minimal example.
- [ ] **Tag the release on GitHub.** Release notes match CHANGELOG entry.

---

*Created after v0.1.0 shipped with undocumented Anthropic embeddings limitation, missing REST API security scope, no conformance quick-scan index, and no minimal working example. All four were builder's blindness — obvious to the author, invisible to a new user.*
