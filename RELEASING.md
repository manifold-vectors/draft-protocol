# Release Process — Vector Systems Standard

**Rule:** No public release ships without passing all gates.
**Automation:** Python Semantic Release (PSR) handles version bumping, changelog generation, tagging, and publishing. You commit; PSR releases.
**Origin:** v0.1.0 shipped with four builder's blindness gaps. v0.1.1 required manual version bumping across 3 files, manual changelog editing, manual tagging, and fighting branch protection. Never again.

---

## How It Works

PSR reads your commit messages and decides what to do:

| Commit prefix | Effect | Example |
|---------------|--------|---------|
| `fix:` | Patch bump (0.1.1 → 0.1.2) | `fix: handle empty input in classifier` |
| `feat:` | Minor bump (0.1.2 → 0.2.0) | `feat: add batch confirmation endpoint` |
| `feat!:` or `BREAKING CHANGE:` | Major bump (0.2.0 → 1.0.0) | `feat!: remove v1 API endpoints` |
| `docs:`, `chore:`, `ci:`, `test:` | No release | `docs: update README example` |

**The full cycle:** Push to main → CI runs tests/lint/types → PSR detects releasable commits → bumps version in pyproject.toml + __init__.py → updates CHANGELOG.md → commits + tags + pushes → builds package → publishes to PyPI → creates GitHub Release.

**If no `fix:` or `feat:` commits exist since last release, nothing happens.** No empty releases.

---

## One-Time Setup

### 1. GitHub Personal Access Token (PAT)

PSR needs to push version commits and tags back through branch protection.

1. Go to https://github.com/settings/tokens → **Fine-grained tokens** → Generate
2. Scope: `manifold-vectors/draft-protocol` only
3. Permissions: **Contents** (read+write), **Metadata** (read)
4. Copy the token

### 2. Add Secrets to Repo

1. Go to repo → Settings → Secrets and variables → Actions
2. Add secret: `GH_TOKEN` = your PAT from step 1
3. Verify the `pypi` environment exists (Settings → Environments) with trusted publisher configured

### 3. Branch Protection Update

Your `main` branch rules must allow the GH_TOKEN to push:
- Settings → Rules → main branch rule
- Under "Bypass list", add yourself or the token's associated account

---

## Pre-Merge Checklist (human responsibility)

These are the things PSR cannot check. Run before merging to main:

### Gate 1 — Stranger Test

> Can someone who has never seen this repo install, configure, and complete a round-trip in under 10 minutes using only the README?

- [ ] Install path works cold on a clean environment
- [ ] Minimal working example: copy-pasteable end-to-end transcript in README
- [ ] All provider/backend limitations documented before the user hits them
- [ ] Security boundaries stated for any network-facing component
- [ ] Top 5 first-run errors produce actionable messages

### Gate 2 — Documentation Completeness

- [ ] README quick-start matches current API
- [ ] Long reference docs have quick-scan index or summary table
- [ ] API docs match implementation (no stale signatures)
- [ ] Known limitations section exists

### Gate 3 — Code Quality (automated by CI, verify locally first)

- [ ] `pytest tests/ -v` — all pass
- [ ] `ruff check src/ tests/` — clean
- [ ] `mypy src/draft_protocol/` — clean
- [ ] No secrets in repo (`pre-commit run --all-files`)

### Gate 4 — Portfolio Consistency

- [ ] Cross-repo version pins correct
- [ ] Shared terminology consistent across public repos
- [ ] Org README / landing page updated

---

## What PSR Handles Automatically

You never manually do any of these again:

- ~~Edit version in pyproject.toml~~
- ~~Edit version in __init__.py~~
- ~~Write CHANGELOG entries~~
- ~~Create git tags~~
- ~~Push tags~~
- ~~Build packages~~
- ~~Publish to PyPI~~
- ~~Create GitHub Releases~~

---

## Post-Release Verification

After PSR publishes, verify:

- [ ] PyPI page renders correctly: https://pypi.org/project/draft-protocol/
- [ ] `pip install draft-protocol=={version}` works in fresh venv
- [ ] GitHub Release notes look right

---

## Emergency: Manual Release

If PSR fails and you need to release manually:

```bash
# 1. Bump version in pyproject.toml and __init__.py
# 2. Update CHANGELOG.md
# 3. Commit, tag, push
git add -A
git commit -m "release: v{version}"
git tag v{version}
git push origin main
git push origin v{version}
# 4. Build and upload
python -m build
twine upload dist/*
```

---

*Automated 2026-02-25 using Python Semantic Release. Manual process retired after v0.1.1 required editing 3 files, fighting branch protection, and running 6 commands to publish documentation fixes.*
