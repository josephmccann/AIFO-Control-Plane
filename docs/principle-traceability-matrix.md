# Principle Traceability Matrix

This matrix maps the founder principles to control-plane responsibilities. It is intentionally operational: every principle should influence infrastructure, documentation, or process.

| # | Principle | Affected Area | Current Compliance | Gap | Planned Remediation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Trust is earned, not assumed | Validation, CI, docs | Improved | First branch still needs validation and review | Maintain workqueue and validation evidence | `scripts/validate.sh`, `workqueue/README.md` |
| 2 | Curiosity before certainty | Planning | Improved | Assumptions need review cadence | Maintain assumption register | `docs/assumption-register.md` |
| 3 | Better context produces better decisions | Product fit | Improved | Product inventory must stay current as PRs merge | Maintain product inventory | `docs/product-runtime-inventory.md` |
| 4 | Distinguish how the system knows | Data architecture | Partial | Future runtime docs need observed/reported/derived/inferred taxonomy | Add data-lineage requirements to product runtime ADRs | Product UX criteria |
| 5 | Missing information is an active workflow | Workqueue | Improved | Blocked approval gates remain | Maintain blocked/open-decision docs | `memory/open-decisions.md` |
| 6 | Preserve state of knowledge | ADRs, memory | Improved | No deployed-state history yet | Maintain ADR framework and current-state memory | `docs/adr/`, `memory/current-state.md` |
| 7 | Decision process is an asset | ADRs | Improved | Future decisions must keep using the standard | Use full ADR standard | `docs/adr/0000-adr-template.md` |
| 8 | Human authority remains central | Approval gates | Improved | Bootstrap and apply approvals remain blocked | Use deployment/bootstrap runbooks | `docs/runbooks/` |
| 9 | Human value is not a ranking function | Product data governance | Deferred | No personnel decision systems planned | Explicitly keep out of infra scope | `workqueue/README.md` |
| 10 | Explain differences, do not flatten them | Product runtime | Partial | Infra does not yet encode tenant-specific context | Defer tenant architecture until product hosting design | Product docs |
| 11 | Improve the model, do not win the argument | Review process | Improved | No PR template yet | Use contributing and ADR requirements | `CONTRIBUTING.md` |
| 12 | Great leadership seeks to understand the most | Operations | Improved | Runbooks untested until deployment | Maintain onboarding and recovery runbooks | `docs/runbooks/` |
| 13 | Continuous learning includes success and failure | Incidents | Improved | No real incident history yet | Maintain runbooks and risk memory | `memory/known-risks.md` |
| 14 | Transparency, humility, and trust outperform hype | Docs | Improved | Deployment status must remain current | Maintain deployment-status memory | `memory/deployment-status.md` |
| 15 | Deterministic truth before generative interpretation | Product boundary | Strong in product | Control plane must preserve boundary in future hosting | Add traceability to product inventory | Product README |
| 16 | Source systems remain authoritative | Integrations | Partial | Future connectors not yet infra-scoped | Do not build hypothetical connector infra | Product PR #186 |
| 17 | Recommendations require lineage | Observability | Partial | No infra lineage/retention plan | Add monitoring ADR | `workstreams/monitoring.md` |
| 18 | Auditability must not become surveillance | Logging/security | Partial | No data-minimization policy for infra logs | Add logging retention ADR before deployment | Product ops runbook |
| 19 | Help people discover what they lack | Product support | Deferred | Infra cannot substitute product discovery | Support validation and safe experimentation | Workqueue |
| 20 | Best-in-class work is operating requirement | Repo quality | Improved | First branch still needs PR review | Maintain operating model docs | This branch |
| 21 | Preserve individuality while learning from patterns | Data governance | Deferred | Cross-company learning is not current infra scope | Explicit future ADR required | Charter |
| 22 | No silent adaptation of material policy | ADR/change control | Improved | Policy changes must be enforced in review | Use ADR standard and CODEOWNERS | `.github/CODEOWNERS` |
| 23 | Build for decisions, not engagement | Scope control | Partial | Avoid overbuilding infra | Workqueue prioritizes product needs | `docs/control-plane-fit-assessment.md` |
| 24 | Full context is never complete | Assumptions | Partial | Need review cadence | Add expiration dates to assumptions | `docs/assumption-register.md` |
