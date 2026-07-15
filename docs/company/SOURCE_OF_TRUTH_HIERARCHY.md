# AI.FO Source-of-Truth Hierarchy

> **Digest metadata**
> - Audit snapshot: 2026-07-14 · pinned commits: see [README.md](README.md) evidence table
> - Statement classes: **[FACT]** verified current fact · **[PR]** open-PR proposal · **[RUN]** active runtime state · **[REC]** recommendation · **[JOE]** founder decision
> - This entire document is a **[REC]** — proposed 2026-07-14; it becomes binding only if Joe adopts it [JOE]. Rows citing repository self-declarations are marked [FACT].
> - PR and active-run state is volatile — refresh from the [canonical dynamic sources](README.md#canonical-dynamic-sources-always-fresher-than-this-digest) before acting.

Principle: every kind of claim has exactly one home. Everything else links to that home. If two documents disagree, the one named below wins and the other should be corrected to a link.

## The hierarchy

| Kind of truth | Canonical source | Notes |
|---|---|---|
| **Product truth** (what the product does, what is merged) | `AI.FO-Demo` `master` — README.md + ARCHITECTURE.md | Open PRs are context, not truth, until merged. [FACT] Canonical baseline at this revision: `3329c99` (PR #186 merge); the deployed demo may lag the baseline — deployment state is a separate fact from merged truth. |
| **Signal methodology** (thresholds, formulas, benchmarks) | `AI.FO-Demo` `docs/SIGNAL_METHODOLOGY.md` | [FACT] The repo itself declares: "No other document may claim methodology authority." |
| **Product numbers** (engine version, signal count, test counts) | Derived only: `lib/financial-engine/src/version.js`, the signal registry, and `generate-telemetry.js` output | [FACT] Hardcoding these anywhere is prohibited by AI.FO-Demo's own rules; the site's remaining `SIGNALS_FALLBACK = 40` literal is a tolerated exception to retire. |
| **Infrastructure truth** (what exists in AWS) | `AIFO-Control-Plane` `main` — `memory/current-state.md` + `memory/deployment-status.md` | Terraform defines intent; these two record verified reality. Assumptions live in `docs/assumption-register.md` (memory/assumptions.md defers to it). |
| **Infrastructure decisions** | `AIFO-Control-Plane` `docs/adr/` + `memory/open-decisions.md` | ADRs for decided; open-decisions ledger for pending (OD-005…OD-012). [PR] PR #13's proposed ADR-0011…ADR-0022 and reference architecture are **proposals, not canonical, until reviewed and merged** [JOE]. |
| **Company state** (cross-repo digest) | `AIFO-Control-Plane` `docs/company/` (this directory) | New with this consolidation. Point-in-time index; never outranks the per-repo sources above (see README.md update protocol). |
| **Founder doctrine** | **No canonical home exists yet.** Source material: [PR] `AI.FO-Demo` PR #180 (`docs/constitution/`, `docs/context/CURRENT_COMPANY_STATE.md`, `.aifo/*.yaml` — valuable working drafts) and [FACT] `AIFO-Control-Plane` `docs/handoffs/HANDOFF_COMPANY.md` | [REC] Reconcile both into **one canonical Founder Operating Manual** before or as part of PR #180's final disposition; the manual's home and format are [JOE]. Until then, treat all doctrine text as draft source material, not authority. |
| **Financial methodology heritage** | Historical: `AI-CFO` `attached_assets/` (founding PRD, Vibe Coding Inputs V1.0, standards-layer rationale) | Historical record only — extract to a durable home before archiving AI-CFO [JOE]. Current methodology authority is SIGNAL_METHODOLOGY.md. |
| **Public telemetry** | `aifo-telemetry` `telemetry.json` (public) | [FACT] Sole writer: AI.FO-Demo's `generate-telemetry.js`; mirror bot is the only committer. Its git history is the public record of metric movement. |
| **Marketing claims** | `GetAIFO-site` `main` | [FACT] Must render numbers from live telemetry/Airtable, never hand-typed (the repo's own rule after the June drift incident). [REC] No validation-study claims until Study A's scoring and measurement complete under the preregistered gates. |
| **Research findings** | `aifo-signal-validation-study` `master` at/after tag `prereg-v1`; results may appear only in `docs/METHODS_AND_RESULTS.md` | [FACT] The default branch is a stale trap until re-pointed to `master` [JOE]. Method changes after the freeze require logged amendments. [RUN] Collection progress is runtime state on the operator machine, not repo state. |
| **Research/nightly decisions ledger** | Airtable base `appHP0GiJuiNFbdMO` (Decision Log; Test Suite Runs = "Step 0 operational ledger") | [FACT] Airtable is authoritative for ruling record-IDs and nightly-run history; repos cite record IDs. |
| **Work queues** | Per-repo `workqueue/` (Control-Plane: merged on main; AI.FO-Demo: proposed in PR #195, whose checkpoint may need refresh) | No company-wide queue; this digest's ACTIVE_WORKSTREAMS.md is the cross-repo index, linking down. |
| **Session handoffs** | Per-repo `docs/session-handoffs/` (dated, frozen checkpoints) | Handoffs are historical evidence — never update them; supersede with a newer dated file. Stale-looking headers ("PARKED…") in old handoffs are intentional. |

## Precedence when sources conflict — [REC]

1. **Merged beats unmerged.** Master/main content outranks any open PR, worktree, or Desktop working directory.
2. **Derived beats written.** A generated number (telemetry, registry count, engine version file) outranks any prose that repeats it.
3. **Dated-current beats dated-old.** Between two frozen checkpoints, the newer date wins; neither is edited.
4. **The owning repo beats every other repo.** Control-Plane statements about the product are pointers, not truth; AI.FO-Demo statements about AWS are pointers, not truth.
5. **Repository evidence beats repository names, GitHub descriptions, and memory.** (Both mismatches found in this audit — GetAIFO-site's "Next.js" description, the study's stale default branch — were name/metadata lies that evidence corrected.)
6. **Runtime state beats all documents for "what is happening right now" — and no document should pretend otherwise.** Active-run progress (e.g., the EDGAR collection) must be re-verified at the source; digests record it only as a dated checkpoint.

## Anti-duplication rule — [REC]

The audit found the same AWS facts repeated across seven Control-Plane documents and product claims repeated across site components. Duplication is how the June marketing-numbers drift happened. When writing any new document: state a fact once in its canonical home, link everywhere else. A document that needs a number it doesn't own should either fetch it (code) or cite the file that owns it (docs).
