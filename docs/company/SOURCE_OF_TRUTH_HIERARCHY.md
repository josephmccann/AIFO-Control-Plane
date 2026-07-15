# AI.FO Source-of-Truth Hierarchy

Status: RECOMMENDED — proposed 2026-07-14; becomes binding only if Joe adopts it
Principle: every kind of claim has exactly one home. Everything else links to that home. If two documents disagree, the one named below wins and the other should be corrected to a link.

## The hierarchy

| Kind of truth | Canonical source | Notes |
|---|---|---|
| **Product truth** (what the product does, what is merged) | `AI.FO-Demo` `master` — README.md + ARCHITECTURE.md | Open PRs are context, not truth, until merged. |
| **Signal methodology** (thresholds, formulas, benchmarks) | `AI.FO-Demo` `docs/SIGNAL_METHODOLOGY.md` | The repo itself declares: "No other document may claim methodology authority." |
| **Product numbers** (engine version, signal count, test counts) | Derived only: `lib/financial-engine/src/version.js`, the signal registry, and `generate-telemetry.js` output | Hardcoding these anywhere is prohibited by AI.FO-Demo's own rules; the site's remaining `SIGNALS_FALLBACK = 40` literal is a tolerated exception to retire. |
| **Infrastructure truth** (what exists in AWS) | `AIFO-Control-Plane` `main` — `memory/current-state.md` + `memory/deployment-status.md` | Terraform defines intent; these two record verified reality. Assumptions live in `docs/assumption-register.md` (memory/assumptions.md defers to it). |
| **Infrastructure decisions** | `AIFO-Control-Plane` `docs/adr/` + `memory/open-decisions.md` | ADRs for decided; open-decisions ledger for pending (OD-005…OD-012). |
| **Company state** (cross-repo digest) | `AIFO-Control-Plane` `docs/company/` (this directory) | New with this consolidation. Point-in-time; every fact must trace to a per-repo source above. |
| **Founder doctrine** | Today: split between `AI.FO-Demo` PR #180 (`docs/constitution/`, `docs/context/CURRENT_COMPANY_STATE.md`, `.aifo/*.yaml` — unmerged drafts) and `AIFO-Control-Plane` `docs/handoffs/HANDOFF_COMPANY.md` | **Needs a decision.** Recommended: merge #180 and make `AI.FO-Demo docs/constitution/` the single doctrine home; Control-Plane keeps only a link. Until then, treat both as drafts. |
| **Financial methodology heritage** | Historical: `AI-CFO` `attached_assets/` (founding PRD, Vibe Coding Inputs V1.0, standards-layer rationale) | Historical record only — extract to a durable home before archiving AI-CFO. Current methodology authority is SIGNAL_METHODOLOGY.md. |
| **Public telemetry** | `aifo-telemetry` `telemetry.json` (public) | Sole writer: AI.FO-Demo's `generate-telemetry.js`; mirror bot is the only committer. Its git history is the public record of metric movement. |
| **Marketing claims** | `GetAIFO-site` `main` | Must render numbers from live telemetry/Airtable, never hand-typed (already the repo's own rule after the June drift incident). No validation-study claims until Study A's primary run has results. |
| **Research findings** | `aifo-signal-validation-study` `master` at/after tag `prereg-v1`; results may appear only in `docs/METHODS_AND_RESULTS.md` | The default branch is a stale trap until re-pointed to `master`. Method changes after the freeze require logged amendments. |
| **Research/nightly decisions ledger** | Airtable base `appHP0GiJuiNFbdMO` (Decision Log; Test Suite Runs = "Step 0 operational ledger") | Airtable is authoritative for ruling record-IDs and nightly-run history; repos cite record IDs. |
| **Work queues** | Per-repo `workqueue/` (Control-Plane: merged on main; AI.FO-Demo: arrives with PR #195) | No company-wide queue; this digest's ACTIVE_WORKSTREAMS.md is the cross-repo index, linking down. |
| **Session handoffs** | Per-repo `docs/session-handoffs/` (dated, frozen checkpoints) | Handoffs are historical evidence — never update them; supersede with a newer dated file. Stale-looking headers ("PARKED…") in old handoffs are intentional. |

## Precedence when sources conflict

1. **Merged beats unmerged.** Master/main content outranks any open PR, worktree, or Desktop working directory.
2. **Derived beats written.** A generated number (telemetry, registry count, engine version file) outranks any prose that repeats it.
3. **Dated-current beats dated-old.** Between two frozen checkpoints, the newer date wins; neither is edited.
4. **The owning repo beats every other repo.** Control-Plane statements about the product are pointers, not truth; AI.FO-Demo statements about AWS are pointers, not truth.
5. **Repository evidence beats repository names, GitHub descriptions, and memory.** (Both mismatches found in this audit — GetAIFO-site's "Next.js" description, the study's stale default branch — were name/metadata lies that evidence corrected.)

## Anti-duplication rule

The audit found the same AWS facts repeated across seven Control-Plane documents and product claims repeated across site components. Duplication is how the June marketing-numbers drift happened. When writing any new document: state a fact once in its canonical home, link everywhere else. A document that needs a number it doesn't own should either fetch it (code) or cite the file that owns it (docs).
