# Test Integrity baseline and initial-activation diagnostic

Status: diagnostic only. No remediation is approved by this document.

## Preserved observation

The failed bootstrap was evaluated at commit `066529950a94a6bb3a5f213af51beceb4fe9790f`, tree `ec0cecce021253defa2f3370d525638bff948b32`, against base `77af0e93780134349abb15bd8d8b665c6de939a3`. The GitHub run was `29613972932`. The machine report emitted 31 findings. The preserved report, run log, run metadata, and identity record are retained outside the repository with the hashes recorded in Mission #25 issue evidence.

The bootstrap preflight itself failed before evidence upload because `EXPECTED_HEAD_SHA` was referenced after the hard-coded head check had been replaced. The reusable Test Integrity job nevertheless ran and produced the preserved machine report. This is a bootstrap defect, not a reason to discount the report.

The report completed the normal full-corpus analysis envelope: 210 test cases, 314 assertions, 22 sourcing assertions, 3 property assertions, 0 focus declarations, 0 skips, and no resource-exhaustion finding. The report was `allowed: false`; no finding is suppressed here.

## Root-cause groups and security disposition

| Group | Findings | Provisional severity | Security disposition | Remediation layer | Adversarial proof |
| --- | ---: | --- | --- | --- | --- |
| A. Integrity-test parser/import capability | 21–22 | Important | Valid fail-closed denials until the parser and first-party import closure can account for the existing test corpus. | Analyzer, import graph, tests | Parser-shape matrix, recursive import/cycle/shadow/dynamic/stale tests, shared-budget tests. |
| B. Analyzer/test co-change ambiguity | 1–20 | Important | Valid conservative denials. The changed contract tests alter executable behavior while the analyzer cannot prove preserved coverage. | Analyzer, baseline protocol, tests | Analyzer weakening with assertion removal, smoke-test replacement, simultaneous analyzer/test changes, exact corpus inventory. |
| C. Validation-workflow co-change ambiguity | 23–31 | Important | Valid conservative denials. The current analyzer cannot prove that the nine changed reusable/caller workflows preserve validation semantics during initial activation. | Workflow analyzer, manifest, staged activation | Omitted stage, stale pin, manifest exclusion, immutable-kernel substitution, partial completion, wrong-SHA evidence. |

All 31 are classified provisionally as Important because they block a security-critical integrity decision but do not, by themselves, demonstrate that an accepted change has bypassed the guard. Final severity remains subject to independent review. No “known finding” or grandfathering disposition is permitted.

## Finding-by-finding disposition plan

Each row is an individual emitted finding. Rows with the same rule remain distinct because they identify distinct governed files or executable test identities.

| ID | Original rule and affected path | Validity | Proposed remediation | Required regression | Rollback |
| ---: | --- | --- | --- | --- | --- |
| 1 | `TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS` — `test_test_integrity_caller.py` | Valid conservative denial of analyzer/test co-change. | Add bounded semantic comparison and staged baseline evidence; retain denial when equivalence is unprovable. | Weakened assertion and smoke-only replacement remain denied. | Revert analyzer/baseline changes. |
| 2–20 | `TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS` — 19 distinct executable cases in `test_workflow_boundaries.py` | Valid conservative denials; each case remains separately governed. | Parse the legitimate existing constructs, fingerprint imported support, and distinguish proof-bearing test evolution from weakened behavior. | One adversarial mutation per semantic family plus simultaneous analyzer/test weakening. | Revert analyzer/test protocol changes. |
| 21 | `TEST_FILE_UNPARSABLE` — `test_test_integrity.py` | Valid until every executed first-party support construct is resolved or denied with a stable reason. | Extend only closed parser/import semantics; do not skip the file. | All implicated syntax, imports, computed setup, and mutation cases. | Revert parser/import changes. |
| 22 | `TEST_FILE_UNPARSABLE` — `test_test_integrity_adversarial.py` | Valid for the same reason; adversarial code cannot be exempt from accounting. | Same closed parser/import expansion with resource bounds. | Full existing adversarial corpus plus malformed/dynamic/resource cases. | Revert parser/import changes. |
| 23 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `reusable-airtable-mirror.yml` | Valid initial-activation ambiguity; no workflow is trusted merely because it is current. | Add complete workflow identity/ownership inventory and staged validation evidence. | Caller/pin/provenance mutation and omitted-stage tests. | Revert baseline protocol. |
| 24 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `reusable-evidence-manifest.yml` | Valid because evidence generation is itself governed. | Bind manifest and evidence schema identities to exact commit/tree. | Missing, stale, contradictory, and wrong-SHA evidence tests. | Revert manifest/baseline changes. |
| 25 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `reusable-frozen-path-guard.yml` | Valid; frozen-path enforcement cannot be self-approved during activation. | Include immutable-kernel input/output identities in the baseline and staged review. | Kernel substitution and verification-logic co-change tests. | Revert activation changes. |
| 26 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `reusable-merge-authorization.yml` | Valid; merge authorization is downstream of integrity evidence. | Require complete candidate evidence before authorization. | Partial-corpus and incomplete-result tests. | Revert activation changes. |
| 27 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `reusable-mission-validation.yml` | Valid; composed validation must prove every child gate executed. | Add explicit stage completion and exact pin inventory. | Missing child, stale pin, and false-success tests. | Revert workflow protocol changes. |
| 28 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `reusable-orphan-recovery.yml` | Valid; unrelated-looking workflow changes remain governed during initial activation. | Inventory all governed reusable workflows and classify ownership deterministically. | Omission, unauthorized caller, and baseline deletion tests. | Revert workflow protocol changes. |
| 29 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `reusable-test-integrity.yml` | Valid and highest-risk co-change finding; the analyzer and its caller cannot self-authorize. | Use staged candidate/prior analyzer validation and immutable evidence; retain fail-closed ambiguity. | Analyzer weakening, workflow omission, stale kernel, and wrong-SHA evidence tests. | Revert to prior trusted path. |
| 30 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `reusable-tier-path-guard.yml` | Valid; path/tier enforcement participates in the governed evidence surface. | Add exact workflow and manifest inventory. | Omitted guard and contradictory pin tests. | Revert workflow protocol changes. |
| 31 | `VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS` — `test-integrity.yml` | Valid; caller activation and event-boundary changes are security-sensitive. | Establish one-time activation with exact event, caller, workflow, kernel, manifest, and analyzed-SHA binding. | Fork rejection, wrong SHA, stale caller, replay, and post-activation reuse tests. | Revert caller/activation changes. |

## Proposed architecture to validate before implementation

1. The candidate analyzer first validates the prior trusted corpus and its own immutable source inventory.
2. The prior trusted analyzer validates bounded candidate changes where possible; any unsupported or contradictory result remains denied.
3. A one-time baseline artifact records exact commit, tree, every governed file, file hash, manifest identity, workflow/caller identity, immutable-kernel input/output identity, and validation-script identity.
4. Independent review validates the inventory and candidate result. The activation record is single-use, exact-SHA-bound, and unavailable after successful activation.
5. The final production analyzer validates the complete post-activation corpus. Ordinary PRs cannot invoke the initial-baseline path.

The mechanism must not use path exemptions, current-state trust, blanket grandfathering, skip-unchanged behavior, partial accounting, external check creation, or a write-capable workflow.

## Resource accounting

The original report did not emit a resource-exhaustion finding and reported a complete measured test corpus, but that is not proof that the activation protocol is safe. Candidate remediation must preserve one shared aggregate budget across file enumeration, manifest reads, import traversal, parsing, workflow inspection, and evidence generation. Boundary, exhaustion, and cross-phase accounting tests are required.

## Required reconciliation

After implementation, rerun the original bootstrap scenario and produce a table mapping all 31 emitted findings to: original result, root cause, changed code/architecture, new result, regression test, and independent-review conclusion. No row may be marked “accepted baseline” without a separately evidenced security rationale.
