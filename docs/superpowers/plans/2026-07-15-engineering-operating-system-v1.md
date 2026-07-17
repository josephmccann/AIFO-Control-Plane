# AI.FO Engineering Operating System v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and review the complete GitHub-native, enforcement-first AI.FO Engineering Operating System v1 and integrate AI.FO-Demo through thin pinned callers without merging, deploying, or mutating production systems.

**Architecture:** A dependency-free Python 3.9+ kernel makes deterministic policy decisions from JSON inputs. Shell wrappers and least-privilege reusable GitHub Actions adapt the pure kernel to authenticated GitHub Issues, PRs, comments, and artifacts. GitHub remains authoritative; repository policy supplies target-specific risk, ownership, and activation flags; Airtable remains dry-run and one-way.

**Tech Stack:** Python 3.9+ standard library, `unittest`, Bash, JSON Schema draft 2020-12 documents, GitHub Issue Forms, GitHub Actions YAML, GitHub CLI, pnpm/Vitest only for AI.FO-Demo integration validation.

## Global Constraints

- Work only in `AIFO-Control-Plane` and `AI.FO-Demo`; never inspect or modify the active EDGAR study repository.
- Do not merge a PR, deploy, mutate AWS/Replit/production, change live branch protection, activate auto-merge or Airtable writes, enable connectors, configure Stripe, run QBO sync, use customer data, create paid services, or create broad credentials.
- Founder approval remains required for every merge. Auto-merge, production deployment, cloud mutation, and Airtable live writes remain disabled by policy.
- GitHub Issues and authenticated GitHub history are authoritative for missions. Airtable is reporting-only and must never drive state or authority.
- The Engineering Constitution references `docs/governance/FOUNDER_OPERATING_MANUAL.md` in one direction and does not duplicate founder doctrine.
- EOS version is `1.0.0`; the EOS content hash is SHA-256 over the exact bytes of `docs/engineering-os/ENGINEERING_CONSTITUTION.md`.
- Runtime kernel code has no third-party Python dependencies and supports the local baseline Python `3.9.6`.
- Every policy decision is deny-by-default; computed risk may raise but never lower declared risk.
- New production behavior follows red-green-refactor. Each new function has a test that was observed failing for the intended reason before implementation.
- Do not commit secrets, credentials, state, local plans, generated evidence, caches, virtual environments, or build output.
- Preserve existing Terraform behavior and the absent apply workflow. `scripts/validate.sh` remains the canonical full validation entrypoint.
- Use conventional commits and one coherent commit per package so package branches can point to evidence-preserving commits.

---

### Task 1: Constitution, schemas, state model, and repository policy

**Files:**
- Create: `docs/engineering-os/ENGINEERING_CONSTITUTION.md`
- Create: `docs/engineering-os/ARCHITECTURE.md`
- Create: `docs/engineering-os/RISK_TIERS.md`
- Create: `docs/adr/0011-github-native-engineering-operating-system.md`
- Modify: `docs/adr/README.md`
- Create: `schemas/engineering-os/{mission,evidence,approval,audit-event,repository-policy,frozen-path,incident,mission-state,finding,authority,metrics,airtable-record}.schema.json`
- Create: `.aifo/engineering-os-policy.json`
- Create: `engineering_os/{__init__,errors,canonical,schema,mission,state}.py`
- Create: `tests/engineering_os/{__init__,helpers,test_schema,test_mission,test_state}.py`
- Create: `tests/engineering_os/fixtures/{mission-valid,mission-not-ready,policy-control-plane}.json`

**Interfaces:**
- Produces `engineering_os.canonical.canonical_json(value) -> str` and `content_sha256(value) -> str`.
- Produces `engineering_os.schema.validate_document(kind, value) -> list[Violation]`.
- Produces `engineering_os.mission.parse_issue_body(body) -> dict` and `validate_ready(mission) -> list[Violation]`.
- Produces `engineering_os.state.project_state(events) -> MissionProjection` and `authorize_transition(projection, event, policy) -> Decision`.

- [ ] **Step 1: Write failing schema, mission, and transition tests**

  Cover complete valid mission parsing, every required field, EOS version/hash pinning, Definition of Ready failure, allowed lifecycle, every invalid state transition, role authority, remediation return, Parked recovery, Incident, Cancelled, and unknown-event denial. Assert stable violation codes such as `MISSION_FIELD_REQUIRED`, `MISSION_NOT_READY`, and `STATE_TRANSITION_DENIED`.

- [ ] **Step 2: Verify the new tests fail because modules and schemas are absent**

  Run: `python3 -m unittest tests.engineering_os.test_schema tests.engineering_os.test_mission tests.engineering_os.test_state -v`

  Expected: non-zero with import/file-not-found failures naming the new interfaces.

- [ ] **Step 3: Implement the minimum canonicalization, validation, mission parser, and deny-by-default state machine**

  Use structured result objects with `allowed`, `code`, and `details`; canonical JSON uses sorted keys and compact separators; audit hashes exclude the `event_hash` field itself. Schemas use `additionalProperties: false` where records are closed and explicit enums for all state, role, tier, rollback, disposition, and authority values.

- [ ] **Step 4: Add the constitution, architecture, risk documentation, policy, and ADR**

  The policy declares Control Plane semantic domains, Tier 2 governance/infrastructure/security paths, founder identities, status checks, default limits, `auto_merge_enabled: false`, `airtable_live_enabled: false`, `deployment_enabled: false`, and `edgar_integration_enabled: false`.

- [ ] **Step 5: Run focused and documentation validation**

  Run: `python3 -m unittest tests.engineering_os.test_schema tests.engineering_os.test_mission tests.engineering_os.test_state -v && python3 -m json.tool .aifo/engineering-os-policy.json >/dev/null && git diff --check`

  Expected: all tests pass and both format checks exit zero.

- [ ] **Step 6: Commit package 1**

  Commit: `feat: establish engineering operating system contracts`

### Task 2: Mission lifecycle, claims, leases, heartbeats, limits, and recovery

**Files:**
- Create: `engineering_os/{lease,limits,commands}.py`
- Create: `tests/engineering_os/{test_lease,test_limits,test_commands}.py`
- Create: `tests/engineering_os/fixtures/events/{valid-lifecycle,expired-lease,concurrent-claim,heartbeat-timeout}.json`
- Create: `scripts/engineering-os/{transition-mission,validate-lease,recover-orphaned-mission}`
- Create: `.github/workflows/{reusable-mission-validation,reusable-orphan-recovery,mission-command}.yml`

**Interfaces:**
- Consumes Task 1 mission/state/canonical interfaces.
- Produces `claim_mission`, `heartbeat_lease`, `release_mission`, `find_orphans`, and `evaluate_limits` pure functions.
- Commands emit an event proposal only; GitHub workflow adapters serialize and append authenticated events.

- [ ] **Step 1: Write failing claim, lease, heartbeat, orphan, and limit tests**

  Cover atomic first claim, duplicate/concurrent claim rejection, one producer lease, lease expiry, valid/invalid heartbeat, stale-agent recovery, safe release, reclaim, path conflict persistence, budget cap, runtime cap, remediation cap, CI rerun cap, concurrent-agent cap, preserved state, and Parked recommendation.

- [ ] **Step 2: Observe expected failures**

  Run: `python3 -m unittest tests.engineering_os.test_lease tests.engineering_os.test_limits tests.engineering_os.test_commands -v`

  Expected: non-zero because lifecycle control interfaces are absent.

- [ ] **Step 3: Implement pure lifecycle controls and stable CLI wrappers**

  Use UTC RFC3339 timestamps, workflow concurrency key `eos-mission-<repo>-<issue>`, nonces, exact lease owner checks, explicit expiry, and no implicit state mutation. Limit decisions include measured value, cap, state-preservation flag, and recommended next action.

- [ ] **Step 4: Implement least-privilege workflow adapters**

  `mission-command.yml` responds only to exact `/eos` commands from authorized actors, serializes by mission issue, normalizes GitHub author/time/URL metadata, validates the full chain, and appends only a validated event. Orphan recovery is scheduled and dry-run by default; mutation requires a repository policy flag that is false initially.

- [ ] **Step 5: Run focused tests and workflow syntax validation**

  Run: `python3 -m unittest tests.engineering_os.test_lease tests.engineering_os.test_limits tests.engineering_os.test_commands -v && ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p) }' .github/workflows/*.yml && bash -n scripts/engineering-os/*`

  Expected: all tests and parsers pass.

- [ ] **Step 6: Commit package 2**

  Commit: `feat: enforce mission leases and lifecycle limits`

### Task 3: Tier, path, semantic ownership, authority, and frozen artifacts

**Files:**
- Create: `engineering_os/{risk,scope,authority,frozen}.py`
- Create: `tests/engineering_os/{test_risk,test_scope,test_authority,test_frozen}.py`
- Create: `tests/engineering_os/fixtures/{changed-files,active-missions,frozen-declarations,authority-records}/**/*.json`
- Create: `scripts/engineering-os/{validate-tier,validate-paths,validate-frozen-artifacts}`
- Create: `.github/workflows/{reusable-tier-path-guard,reusable-frozen-path-guard}.yml`
- Create: `docs/engineering-os/{AUTHORITY_MODEL,FROZEN_ARTIFACTS,CREDENTIAL_MODEL}.md`

**Interfaces:**
- Produces `compute_tier`, `validate_scope`, `detect_mission_conflicts`, `validate_authority`, and `validate_frozen_changes`.
- Inputs are mission, base-policy, changed-file list, active mission projections, authority records, frozen declarations, and current time/head SHA.

- [ ] **Step 1: Write failing risk, path, authority, and frozen tests**

  Cover Tier 0/Tier 1 classification both directions, every Tier 2 trigger, automatic raise/no automatic lower, under-declaration failure, allowed/prohibited/path-scope failures, semantic conflicts, coordinated overlap, Tier 1 touching Tier 2 paths, read-only default, expired/wrong-repo/wrong-path authority, frozen write, valid exception, stale/wrong-SHA exception, pins, sealed manifests, release conditions, and one-shot markers.

- [ ] **Step 2: Observe expected failures**

  Run: `python3 -m unittest tests.engineering_os.test_risk tests.engineering_os.test_scope tests.engineering_os.test_authority tests.engineering_os.test_frozen -v`

  Expected: non-zero because enforcement modules are absent.

- [ ] **Step 3: Implement deterministic deny-by-default enforcement**

  Normalize POSIX paths, reject traversal and absolute paths, apply `fnmatch` globs consistently, compute the maximum tier across path and capability triggers, and require exact mission/PR/head/path/action matching for exceptions and authorities.

- [ ] **Step 4: Implement reusable guards and documentation**

  Workflows evaluate the base-branch policy so a PR cannot weaken its own guard. A change to policy or governance computes Tier 2. Document the GitHub credential path-scope gap and GitHub App migration path without claiming unsupported enforcement.

- [ ] **Step 5: Run focused tests and syntax checks**

  Run: `python3 -m unittest tests.engineering_os.test_risk tests.engineering_os.test_scope tests.engineering_os.test_authority tests.engineering_os.test_frozen -v && ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p) }' .github/workflows/*.yml && git diff --check`

  Expected: all checks pass.

- [ ] **Step 6: Commit package 3**

  Commit: `feat: enforce risk ownership and frozen artifacts`

### Task 4: Test-integrity and validation controls

**Files:**
- Create: `engineering_os/test_integrity.py`
- Create: `tests/engineering_os/test_test_integrity.py`
- Create: `tests/engineering_os/fixtures/test-integrity/{base,head,overrides}/**/*`
- Create: `scripts/engineering-os/validate-test-integrity`
- Create: `.github/workflows/reusable-test-integrity.yml`
- Modify: `scripts/validate.sh`
- Modify: `.github/workflows/terraform-validate.yml`

**Interfaces:**
- Produces `analyze_test_integrity(base_root, head_root, policy) -> IntegrityReport` and `validate_test_override(report, override, review, approval) -> Decision`.

- [ ] **Step 1: Write failing deterministic fixture tests**

  Cover deleted and effectively renamed tests, new skip/disable markers, assertion decline, sourcing/property assertion removal, validation workflow deletion, weakened test configuration, material coverage decline, fixture substitution reducing cases, no absolute test-count rule, approved behavior-removal override, wrong mission/head override, missing reviewer approval, and Tier 2 founder approval.

- [ ] **Step 2: Observe expected failures**

  Run: `python3 -m unittest tests.engineering_os.test_test_integrity -v`

  Expected: non-zero because the analyzer is absent.

- [ ] **Step 3: Implement delta-based adapters and override validation**

  Count configured assertion and skip patterns, compare file content hashes and normalized test signatures, treat ambiguous reductions as findings, accept optional coverage JSON, and emit raw deltas even when an override is valid.

- [ ] **Step 4: Add reusable workflow and canonical validation integration**

  The workflow checks out base and head into separate paths, uses base policy, and uploads a JSON report. `scripts/validate.sh` runs the complete EOS unittest suite and shell syntax checks in addition to existing Terraform validation; existing infrastructure checks remain intact.

- [ ] **Step 5: Run focused and full non-Terraform validation**

  Run: `python3 -m unittest tests.engineering_os.test_test_integrity -v && python3 -m unittest discover -s tests/engineering_os -p 'test_*.py' -v && bash -n scripts/*.sh scripts/engineering-os/* && git diff --check`

  Expected: all EOS tests and syntax checks pass.

- [ ] **Step 6: Commit package 4**

  Commit: `feat: guard test integrity with evidence deltas`

### Task 5: Evidence, audit, findings, metrics, and founder approval

**Files:**
- Create: `engineering_os/{audit,findings,approval,evidence,metrics}.py`
- Create: `tests/engineering_os/{test_audit,test_findings,test_approval,test_evidence,test_metrics}.py`
- Create: `tests/engineering_os/fixtures/{audit,approvals,evidence,metrics}/**/*.json`
- Create: `scripts/engineering-os/{validate-approval,validate-audit,generate-evidence,generate-metrics}`
- Create: `.github/workflows/reusable-evidence-manifest.yml`
- Create: `docs/engineering-os/{PRODUCER_ADVERSARY_MODEL,EVIDENCE_AND_AUDIT,METRICS}.md`

**Interfaces:**
- Produces hash-chain validation, normalized finding classification, exact approval validation, evidence generation, and aggregate metric projection.
- Evidence generation consumes only machine-derived adapter outputs and authenticated GitHub records.

- [ ] **Step 1: Write failing audit, finding, approval, evidence, and metric tests**

  Cover event ordering/hash breaks, actor/time normalization, all finding classes, producer/adversary identity separation, different-model-family policy, valid-findings/rejection/disagreement/remediation metrics, stale/wrong SHA/wrong PR/wrong environment/wrong method approval, post-approval commit, every required evidence field, schema validation, artifact hashes, founder minutes, lifecycle durations, costs, defects, parked/orphan/false-positive/override/rollback/incident/throughput metrics, and no rejection quota.

- [ ] **Step 2: Observe expected failures**

  Run: `python3 -m unittest tests.engineering_os.test_audit tests.engineering_os.test_findings tests.engineering_os.test_approval tests.engineering_os.test_evidence tests.engineering_os.test_metrics -v`

  Expected: non-zero because the modules are absent.

- [ ] **Step 3: Implement canonical audit, approval, evidence, and metric logic**

  Approval binds action, mission, PR, reviewed head, environment, merge method, expiry, deployment, and cutover independently. Evidence rejects producer-supplied derived values, records cleanup/deployment state, and includes canonical artifact hashes and timestamp.

- [ ] **Step 4: Implement split-privilege evidence workflow**

  An unprivileged job checks out and executes PR code with read-only contents. A separate fresh-runner job receives only validated artifacts and may link the run to the PR/mission. No job that executes PR code receives issue-write, PR-write, secrets, OIDC, deployment, or cloud authority.

- [ ] **Step 5: Run focused and aggregate tests**

  Run: `python3 -m unittest tests.engineering_os.test_audit tests.engineering_os.test_findings tests.engineering_os.test_approval tests.engineering_os.test_evidence tests.engineering_os.test_metrics -v && git diff --check`

  Expected: all tests pass.

- [ ] **Step 6: Commit package 5**

  Commit: `feat: generate auditable engineering evidence`

### Task 6: Merge authorization, incidents, rollback, issue forms, and queue views

**Files:**
- Create: `engineering_os/{merge,incident}.py`
- Create: `tests/engineering_os/{test_merge,test_incident,test_human_agent_equivalence}.py`
- Create: `scripts/engineering-os/validate-merge-authorization`
- Create: `.github/workflows/reusable-merge-authorization.yml`
- Create: `.github/ISSUE_TEMPLATE/{engineering-mission,engineering-incident,config}.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `docs/engineering-os/{MISSION_LIFECYCLE,DEFINITION_OF_READY,DEFINITION_OF_DONE,INCIDENT_AND_ROLLBACK}.md`

**Interfaces:**
- Produces `authorize_merge` and `validate_incident`.
- Human and agent submissions use the same mission parser, events, checks, and approval gates.

- [ ] **Step 1: Write failing merge and incident tests**

  Cover merge in wrong state, missing required checks, incomplete adversarial review, unresolved threads, stale/wrong approval, commits after approval, wrong method, tier failure, missing evidence, manual authorization, disabled auto-merge, policy-enabled future auto-merge, incident transition, every rollback classification, originating mission/PR linkage, kill switch, evidence preservation, recovery verification, and human/agent equivalence.

- [ ] **Step 2: Observe expected failures**

  Run: `python3 -m unittest tests.engineering_os.test_merge tests.engineering_os.test_incident tests.engineering_os.test_human_agent_equivalence -v`

  Expected: non-zero because merge/incident interfaces are absent.

- [ ] **Step 3: Implement exact merge and incident decisions**

  Merge authorization emits a decision only and never invokes a merge API. Deployment and cutover flags are independent and false unless separately approved. Incident validation never treats merge approval as rollback execution authority.

- [ ] **Step 4: Add issue forms, PR template, queue conventions, and lifecycle docs**

  Forms collect complete machine-readable declarations and incident records. Labels/conventions cover Ready, Claimed, In Progress, Review, Founder Approval, Parked, Incident, and Closed plus repository, tier, producer, lease expiry, age, program link, and blocked reason. Native Projects fields remain optional because current token scope cannot manage Projects.

- [ ] **Step 5: Run focused tests and YAML validation**

  Run: `python3 -m unittest tests.engineering_os.test_merge tests.engineering_os.test_incident tests.engineering_os.test_human_agent_equivalence -v && ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p) }' .github/ISSUE_TEMPLATE/*.yml .github/workflows/*.yml && git diff --check`

  Expected: all tests and parsers pass.

- [ ] **Step 6: Commit package 6**

  Commit: `feat: gate merges and incident recovery`

### Task 7: Airtable one-way reporting mirror

**Files:**
- Create: `engineering_os/airtable.py`
- Create: `tests/engineering_os/test_airtable.py`
- Create: `tests/engineering_os/fixtures/airtable/{missions,expected-records,approval}.json`
- Create: `scripts/engineering-os/sync-airtable`
- Create: `.github/workflows/reusable-airtable-mirror.yml`
- Create: `docs/engineering-os/AIRTABLE_MIRROR.md`

**Interfaces:**
- Produces `project_airtable_record` and `sync_airtable(direction, mode, ...)`.
- Dry-run emits redacted deterministic records; live mode requires policy, exact approval, identifiers, and ephemeral environment credential.

- [ ] **Step 1: Write failing mirror tests**

  Cover schema projection, GitHub-to-Airtable dry run, attempted Airtable-to-GitHub rejection, missing live gates, redaction, idempotent upsert key, API error fail-closed behavior, and confirmation that Airtable state cannot transition or authorize a mission.

- [ ] **Step 2: Observe expected failures**

  Run: `python3 -m unittest tests.engineering_os.test_airtable -v`

  Expected: non-zero because the connector is absent.

- [ ] **Step 3: Implement dry-run-first one-way adapter**

  Use `urllib.request` only in explicitly gated live mode, never print tokens, set timeouts, retry only safe requests with bounded attempts, and return non-zero on partial failure. Initial Control Plane policy keeps live mode false.

- [ ] **Step 4: Add reusable workflow and schema contract documentation**

  The workflow has no Airtable secret requirement in dry-run. A future live job must use an approved environment and exact approval record; no live environment is created or activated in this program.

- [ ] **Step 5: Run focused tests and syntax checks**

  Run: `python3 -m unittest tests.engineering_os.test_airtable -v && ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p) }' .github/workflows/*.yml && git diff --check`

  Expected: all tests pass.

- [ ] **Step 6: Commit package 7**

  Commit: `feat: add dry-run Airtable reporting mirror`

### Task 8: AI.FO-Demo thin integration

**Files in `/Users/joemccann/code/AI.FO-Demo`:**
- Create: `.aifo/engineering-os-policy.json`
- Create: `.github/workflows/{eos-pull-request,eos-orphan-recovery,eos-airtable-mirror}.yml`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Create: `CONTRIBUTING.md`
- Create: `artifacts/aifo/tests/eosPolicyIntegration.test.js`

**Interfaces:**
- Consumes Control Plane reusable workflows pinned to the reviewed package SHA and EOS version/hash.
- Demo policy defines semantic ownership for `lib/financial-engine`, `lib/db`, API, frontend, generated clients, workflows, product claims, secrets/connectors, and frozen declarations while leaving EDGAR integration disabled.

- [ ] **Step 1: Read Demo `AGENTS.md`, `CLAUDE.md`, current package files, and existing workflows completely, then write the failing thin-integration test**

  Test immutable reusable workflow pins, EOS version/hash, founder-required merge, disabled auto-merge/deploy/cloud/Airtable-live/EDGAR flags, base-policy enforcement, semantic ownership, Tier 2 methodology/schema/security/claims/connectors, no duplicated constitution, equivalent human/agent path, and absence of deploy/QBO/live-verifier commands.

- [ ] **Step 2: Observe the integration test fail**

  Run from Demo: `pnpm --filter @workspace/aifo test -- eosPolicyIntegration.test.js`

  Expected: non-zero because policy and callers are absent.

- [ ] **Step 3: Implement policy, pinned thin callers, AGENTS pointer, and concise CONTRIBUTING**

  The PR caller invokes one composed reusable mission-validation workflow, which internally runs tier/path, frozen, integrity, evidence, and merge-authorization jobs. Scheduled callers remain dry-run. `CLAUDE.md` either stays synchronized or explicitly defers to `AGENTS.md`. Because private cross-repository Actions access is currently `none`, document that callers cannot activate until the founder approves the exact repository Actions access change; do not change the setting.

- [ ] **Step 4: Run deterministic Demo validation without external services or secrets**

  Run from Demo: `pnpm lock:preflight && pnpm run typecheck && pnpm --filter @workspace/aifo test && CI=1 pnpm --filter @workspace/api-server test && pnpm --filter @workspace/scripts test && pnpm build && git diff --check`

  Expected: integration and existing offline suites pass. Do not run Playwright, deployment smoke, live verifier, QBO sync, or connector workflows.

- [ ] **Step 5: Commit Demo integration on a dedicated branch**

  Commit: `feat: integrate engineering operating system`

### Task 9: Operational documentation, gap register, program state, and final validation

**Files:**
- Create: `docs/engineering-os/{README,KNOWN_ENFORCEMENT_GAPS,HUMAN_ONBOARDING}.md`
- Modify: `CONTRIBUTING.md`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `memory/{current-state,known-risks,open-decisions}.md`
- Modify: `workqueue/README.md`
- Create: `tests/engineering_os/test_documentation.py`
- Create: `scripts/engineering-os/validate-all`

**Interfaces:**
- `validate-all` runs all EOS unit/fixture/schema/document/workflow checks without external credentials.
- The gap register maps every non-mechanical Layer 0/Layer 2 rule to status, risk, mitigation, owner, and closure path.

- [ ] **Step 1: Write failing documentation/coverage tests**

  Test required document/schema/workflow/script presence, constitution version/hash references, one-way Founder Manual link, every constitutional/convention rule mapped to an enforcement control or named gap, disabled capability flags, no EDGAR activation, wrapper executability, and no generated artifacts tracked.

- [ ] **Step 2: Observe expected failures**

  Run: `python3 -m unittest tests.engineering_os.test_documentation -v`

  Expected: non-zero until the complete documentation and gap mapping exist.

- [ ] **Step 3: Complete onboarding, repository entrypoints, state ledgers, and gap register**

  Document same-path human/agent onboarding, compliant mission/PR examples, program epic conventions, status views, activation prerequisites, exact known GitHub limitations, branch-protection/Actions-access founder gates, and migration to scoped GitHub App credentials. Do not duplicate founder doctrine or product methodology.

- [ ] **Step 4: Run complete local verification**

  Run: `python3 -m unittest discover -s tests/engineering_os -p 'test_*.py' -v`

  Run: `PATH="$PWD/build/bin:$PATH" ./scripts/validate.sh`

  Run: `PATH="$PWD/build/bin:$PATH" bash tests/install-dev-tools-test.sh`

  Run: `ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p) }' .github/ISSUE_TEMPLATE/*.yml .github/workflows/*.yml`

  Run: `bash -n scripts/*.sh scripts/engineering-os/* && git diff --check`

  Expected: zero failures. If Terraform or pinned linters are absent, install only the repository-pinned tools into ignored `build/bin`; do not weaken or skip the check.

- [ ] **Step 5: Secret/output/prohibited-scope review**

  Run tracked-file scans for credentials, `.tfstate`, plans, evidence output, caches, EDGAR references that imply activation, deploy/apply/destroy commands in new workflows, and any live Airtable or auto-merge flag. Expected: no prohibited artifact or enabled high-risk capability.

- [ ] **Step 6: Commit package 9**

  Commit: `docs: complete engineering operating system operations`

### Task 10: Independent adversarial review, remediation, and draft PR program

**Files:**
- Create only review artifacts that belong in `docs/engineering-os/reviews/` and issue/PR bodies; do not commit generated diff packages or evidence output.

**Interfaces:**
- Review inputs are clean-context acceptance criteria, exact base/head SHAs, and diff packages.
- Findings use the shared classification schema and count against the configured remediation cap.

- [ ] **Step 1: Create a normal GitHub program epic and nine mission issues**

  Use AIFO-Control-Plane issues as authoritative records, assign the founder, link package missions to the program issue, and record EOS version/hash, exact repositories/paths, limits, roles, acceptance criteria, validation, rollback, and founder gates. Do not create a GitHub Project because the current token lacks Projects scope.

- [ ] **Step 2: Run clean-context adversarial review for every material package**

  Prefer a different model family where available. Require break attempts against authority, state, paths, tiering, evidence, approval, frozen artifacts, lease recovery, incidents, and test integrity. Reviewers receive no hidden producer reasoning.

- [ ] **Step 3: Classify findings and remediate valid Critical/Important findings test-first**

  Record valid, invalid, duplicate, and founder-decision dispositions. Re-run focused and complete validation after each remediation cycle. Park rather than exceed the configured remediation cap.

- [ ] **Step 4: Create evidence-preserving package branches and draft PRs**

  Point Control Plane package branches at their sequential package SHAs and open stacked draft PRs with exact base/head, mission, evidence, risk, rollback, disabled capabilities, and approval state. Open the Demo draft PR against `master` only after its caller pins the reviewed Control Plane workflow SHA. Do not merge.

- [ ] **Step 5: Verify remote PR heads and unresolved review state**

  Use read-only GitHub queries to confirm every draft PR URL, base/head SHA, check state, review threads, and that no PR merged. Record the private reusable-workflow access setting as a founder activation gate rather than changing it.

- [ ] **Step 6: Produce the founder decision packet**

  Include the requested 28-part deliverable, ranked recommendation, alternatives and consequences, exact approvals requested, exact artifacts/SHAs, validation evidence, known gaps, disabled capabilities, and explicit prohibited-action confirmations.
