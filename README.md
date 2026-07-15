# AI.FO Control Plane

AWS infrastructure control-plane repository for AI.FO.

Session state: ACTIVE — OPERATIONAL REFINEMENT

The approved current-scope AWS control-plane baseline is operationally complete. It does not host the AI.FO product runtime and it does not include an apply workflow.

Start with [docs/session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md](docs/session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md) before changing infrastructure design or resuming work.

## Baseline

- AWS account: `350480401760`
- AWS region: `us-west-2`
- Terraform state bucket: `aifo-terraform-state-350480401760-us-west-2`
- Terraform state key: `control-plane/terraform.tfstate`
- Human admin access: IAM Identity Center permission set `AIFO-Platform-Admin`
- CI/CD access: GitHub Actions OIDC, no static AWS keys
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`
- Apply role status: state-access-only; no infrastructure mutation policy
- EC2 instance: `i-0254a9e2fcbcdebd7`
- EC2 state: `stopped`
- Instance type: `m7i-flex.2xlarge`
- Root volume: 100 GiB encrypted gp3
- Administrative access: AWS Systems Manager Session Manager only
- Public SSH: not allowed
- Inbound security-group rules: zero
- Operating schedule: start 08:00 and stop 16:00 Monday-Friday
- Timezone: `America/Los_Angeles`
- Current monthly posture: scheduled operation under the $250 budget target; always-on operation is not approved
- Product runtime infrastructure: not deployed

## Current Verification

- Local Terraform control-plane plan: `0 to add, 0 to change, 0 to destroy`
- Latest successful GitHub Terraform Plan: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29378532712
- GitHub plan classification: exit code `0`, `0` add / `0` change / `0` destroy, result `clean`
- GitHub plan-role policy default version: `v4`
- OIDC trust: unchanged and restricted to exact repository/environment subjects
- Scheduler: unchanged and targets only `i-0254a9e2fcbcdebd7`

## Repository Layout

```text
.
├── .github/workflows/
│   ├── terraform-plan.yml
│   └── terraform-validate.yml
├── docs/
│   ├── adr/
│   ├── handoffs/
│   ├── runbooks/
│   ├── session-handoffs/
│   ├── architecture.md
│   ├── deployment-readiness-review.md
│   ├── product-runtime-inventory.md
│   └── security-model.md
├── memory/
├── scripts/
├── terraform/
│   ├── bootstrap/
│   ├── environments/control-plane/
│   └── modules/
├── workqueue/
└── workstreams/
```

## What Terraform Defines

The deployed `control-plane` environment includes:

- VPC with DNS support
- One public subnet in one Availability Zone
- Internet Gateway and outbound default route
- S3 gateway endpoint
- Ubuntu EC2 control-plane host with public IPv4 for outbound egress
- No SSH key
- Security group with no ingress rules
- Security group egress for HTTPS and DNS only
- EC2 IAM role with `AmazonSSMManagedInstanceCore`
- IMDSv2 required
- Termination protection enabled
- Multi-Region CloudTrail management-events baseline
- Dedicated encrypted CloudTrail S3 log bucket with lifecycle expiration
- Session Manager logging to encrypted CloudWatch Logs with 30-day retention
- EventBridge Scheduler start/stop automation for weekday operating hours
- Scheduler dead-letter queue
- Optional AWS Budget management, disabled by default

The host uses public IPv4 because the initial workload needs outbound internet access for package installation, GitHub clones, container pulls, and external API calls. Public addressing plus zero inbound security-group rules avoids NAT Gateway cost for the solo-founder stage. A private subnet migration remains deferred.

## GitHub Actions

Workflows:

- `terraform-validate.yml`: formatting and Terraform validation without AWS credentials.
- `terraform-plan.yml`: Terraform plan using GitHub Actions OIDC.

There is no apply workflow.

Repository variables configured for planning:

- `AWS_TERRAFORM_PLAN_ROLE_ARN=arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- `TF_BACKEND_BUCKET=aifo-terraform-state-350480401760-us-west-2`
- `TF_BACKEND_KEY=control-plane/terraform.tfstate`

Plan gate behavior:

- Pull request exit code `2`: allowed as proposed change.
- Main/manual exit code `2`: failed as unexpected drift.
- Exit code `0`: clean.
- Exit code `1`: failed plan.

GitHub required environment reviewers are unavailable on the current repository plan. The `terraform-apply` environment exists but must remain unused. Do not create an apply workflow until an enforceable approval boundary exists.

## Local Validation

Install the pinned, checksum-verified lint tools into ignored `build/bin`:

```bash
./scripts/install-dev-tools.sh
```

Run the standard validation entrypoint with the repository tools on `PATH`:

```bash
PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 ./scripts/validate.sh
```

Read-only control-plane plan:

```bash
PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 \
terraform -chdir=terraform/environments/control-plane plan \
  -no-color -input=false -lock=false -detailed-exitcode
```

## Operating Model

- Current state: [memory/current-state.md](memory/current-state.md)
- Open decisions: [memory/open-decisions.md](memory/open-decisions.md)
- Work queue: [workqueue/README.md](workqueue/README.md)
- Deployment readiness: [docs/deployment-readiness-review.md](docs/deployment-readiness-review.md)
- Control-plane handoff: [docs/handoffs/HANDOFF_CONTROL_PLANE.md](docs/handoffs/HANDOFF_CONTROL_PLANE.md)
- Session handoff: [docs/session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md](docs/session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md)
- Host patching: [docs/runbooks/host-patching.md](docs/runbooks/host-patching.md)

## Product Runtime Boundary

The control plane does not run the AI.FO product. Product runtime infrastructure remains out of scope until a separate architecture, security, data, cost, and deployment decision is approved.
