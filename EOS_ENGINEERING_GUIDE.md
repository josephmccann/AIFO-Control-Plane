# EOS Engineering Guide

**Status:** current · **Audience:** engineers and AI agents working in this repository.

This guide explains how to make a change safely. If you have never seen this repository, read `EOS_VERSION_1_FINAL_REPORT.md` and `EOS_ARCHITECTURE.md` first.

> The repository is in **maintenance mode**. Change it only for operational experience, discovered defects, new governance requirements, or organizational growth — not to add sophistication.

---

## 1. The core rule

**Every change to the repository is governed by a Ready-bound mission.** You cannot commit anything to `main`'s lineage — even documentation — without a mission whose `allowed_paths` cover the files you touch, because the required `Validate Terraform` check runs `scripts/validate.sh`, whose successor-closure preflight rejects any path not in the governed allow-list.

So the daily workflow always starts with a mission.

---

## 2. Daily / change workflow

```mermaid
flowchart TD
    A[Identify the change] --> B[Draft a mission declaration]
    B --> C[Validate: schema + validate_ready + digest]
    C --> D[gh issue create]
    D --> E{Founder posts /eos ready}
    E --> F[Implement within allowed_paths]
    F --> G[Add adversarial + regression tests]
    G --> H[Local validation: unittest, validate-all, closure, git diff --check]
    H --> I[Commit + generate successor records + push]
    I --> J[Open PR with mission marker]
    J --> K[@codex review]
    K --> L{Findings?}
    L -- yes --> M[Reproduce, verify premise, fix, re-validate, re-review]
    M --> K
    L -- no / all-clear --> N[Founder merge gate]
```

### Drafting a mission
- Write a declaration (see an existing mission issue body for the exact JSON shape). Include `mission_id`, `allowed_paths`, `prohibited_paths`, `risk_tier`, `budgets`, `validation_commands`, `rollback`, `assignments`, and the `eos.constitution_sha256`.
- Validate it before filing:
  ```
  python3 -c "import json,sys; sys.path.insert(0,'.'); \
    from engineering_os.schema import validate_document; \
    from engineering_os.mission import validate_ready; \
    from engineering_os.canonical import content_sha256; \
    d=json.load(open('mission.json')); \
    print(validate_document('mission',d) or 'schema OK'); \
    print(validate_ready(d) or 'ready OK'); \
    print('digest', content_sha256(d))"
  ```
- Scope tightly. Put the analyzer/generator invariant surface and anything you are not changing in `prohibited_paths` — this makes guarantees self-enforcing.

### Implementing
- Work in an isolated worktree/branch off `origin/main`.
- Touch only `allowed_paths`. If you discover you need a file outside scope, stop — that is a scope question for a successor mission, not a silent expansion.
- After the code commit, generate the successor content-pin records (`outputs/mission-<n>-closure-records.json`) so the closure validator passes, and add the mission's paths to `SUCCESSOR_ALLOWED_PATHS` in `scripts/engineering-os/validate-activation-closure`.

---

## 3. PR workflow
- Open the PR against `main`. Include the mission marker in the body: `<!-- AIFO-EOS-MISSION-ISSUE: <n> -->` (Test Integrity requires exactly one).
- Keep the branch a clean linear descendant of `main` (no squash/rebase surprises at merge).

## 4. Review workflow
- Comment `@codex review` on the PR.
- Codex signals **all-clear** with a 👍 reaction on the PR plus a "Didn't find any major issues" comment bound to the exact head. Silence, zero visible findings, or the absence of unresolved threads alone is **not** approval.
- For each finding: reproduce it, **verify its premise**, fix it, add a regression test, re-run validation, push, and re-invoke `@codex review`. Repeat until the exact head is clean.
- If a finding's premise is empirically wrong, you may decline it with evidence rather than implement it — but verify thoroughly first.

## 5. CI workflow
- Required checks: **Validate Terraform** and **GitGuardian Security Checks**. Both must be green.
- `Test Integrity` is informational pre-activation and may deny (corpus-wide ambiguity) without blocking merge. Do not suppress, bypass, or weaken it.
- After any new commit, prior CI and review are stale — rerun everything and re-review at the new head.

## 6. Merge workflow
- A PR is engineering-ready only when: all required CI green, exact-head `@codex review` all-clear, Critical 0, Important 0, unresolved threads 0, worktree clean, branch synchronized.
- **You may not merge.** Prepare a founder merge package and stop at the founder merge gate.

---

## 7. Governance boundaries (what needs a founder)

| Action | Who |
|---|---|
| Implement in scope, add tests, open PR, address review, create a mission issue | Engineer / AI agent |
| Post `/eos ready` | **Founder** |
| Merge a PR | **Founder** |
| `/eos authorize-baseline` / `attempt-baseline` / `consume-baseline` | **Founder** |
| Activate Test Integrity, deploy, change branch protection, create a release tag | **Founder** |

---

## 8. AI Agent Guide

If you are an AI agent (Claude, Codex, or successor):

- **Authority is bounded by the Ready-bound mission scope.** Inside it, act autonomously: implement, refactor, test, validate, push, review, iterate. Outside it, stop.
- **Never fabricate a founder authentication.** Do not post `/eos ready`, and do not merge, unless the founder has explicitly and unambiguously authorized that specific action. "Complete the mission" is not authorization to author a founder-signed governance event.
- **Verify before you act on review feedback.** Reproduce findings; check their premises. Implement the valid ones; decline the incorrect ones with evidence.
- **Fail closed.** Never weaken a validation rule, suppress a finding, or convert a fail-closed path to a warning to make something pass.
- **Preserve authenticated history and protected assets.** Never rewrite EOS events, force-push, or touch the protected `engineering-operating-system` worktree or the preserved stashes.
- **Report faithfully.** State CI/test/review results as they are, with evidence. Do not claim all-clear on silence.
- **Stopping points:** the founder merge gate, a `/eos ready` gate for a new mission, and every activation/deployment gate. Return there with a complete package.
