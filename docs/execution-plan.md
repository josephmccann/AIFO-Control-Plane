# Execution Plan

## Mission Scope

Build and maintain the AI.FO AWS control plane with enough discipline that a staff engineer, security engineer, investor technical diligence team, or future CTO can review it and see evidence of careful engineering practice.

## Prioritized Tasks

| Priority | Task | Dependencies | Decision Gate | Validation |
| --- | --- | --- | --- | --- |
| P0 | Complete product context docs | Product repo access | None | Markdown review |
| P0 | Establish repository operating model | Product context docs | None | File existence and status review |
| P0 | Add ADR framework and initial ADRs | Operating model | None | Markdown review |
| P0 | Create bootstrap runbook | Existing Terraform bootstrap roots | AWS execution approval | Terraform validate |
| P0 | Document EC2 instance recommendation | Official AWS pricing/spec sources | Human approval before apply | Source review |
| P1 | Refine least-privilege IAM policies | Bootstrap design | IAM deployment approval | Terraform validate |
| P1 | Add cost model | EC2 recommendation | Human review | Manual calculation |
| P1 | Add disaster recovery and emergency access runbooks | Remote state/bootstrap design | None | Runbook review |
| P1 | Prepare deployment-readiness review | All P0/P1 docs | Apply approval | Checklist review |
| P2 | Design product runtime architecture | Product migration decision | Spending and deployment approval | ADR review |
| P2 | Design secrets architecture | Product runtime scope | Spending approval if AWS service used | ADR review |
| P2 | Design monitoring architecture | Product runtime scope | Spending approval if paid services used | ADR review |

## Dependencies

- Local product repository context from `AI.FO-Demo`.
- Authenticated GitHub access for PR and branch state.
- Official AWS documentation and Price List data for instance and cost decisions.
- Human approval before AWS bootstrap, IAM changes, deployment, spending, or apply.

## Decision Gates

| Gate | Required Approval |
| --- | --- |
| Remote-state bucket creation | Human approval |
| GitHub OIDC provider and IAM role creation | Human approval |
| Any `terraform apply` | Human approval |
| Any paid or recurring AWS service activation | Human approval |
| Apply workflow creation or use | Human approval |
| Product runtime deployment | Human approval |
| Repository merge | Human approval |

## Validation Plan

Run before any commit:

```bash
./scripts/validate.sh
git diff --check
ruby -ryaml -e 'ARGV.each { |path| YAML.load_file(path) }' .github/workflows/*.yml
```

Run when tooling is available:

```bash
shellcheck scripts/*.sh
actionlint
```

## Documentation Outputs

- Product runtime inventory.
- Control-plane fit assessment.
- Principle traceability matrix.
- Assumption register.
- ADRs.
- Runbooks.
- Memory/current-state docs.
- Dependency-aware workqueue.
- Changelog entries.

## Rollback Strategy

Documentation and Terraform changes roll back through normal Git revert until AWS bootstrap occurs.

For future AWS bootstrap:

1. Produce an execution-specific plan.
2. Record expected resources.
3. Record destroy/import rollback steps.
4. Require human approval.
5. Preserve command output in a private operational log without secrets.
