# Human and Agent Onboarding

Humans and agents use the same Engineering Operating System path. Neither role
receives a bypass, alternate schema, implicit approval, or weaker evidence
standard. The active contract is EOS version `1.0.0` with Engineering
Constitution SHA-256
`a255c0976949d8acae91f7d46e85cc083a15e242ccbd62e587c4e3163b29265e`.

## Mission path

1. Open an Engineering mission issue using the repository issue form.
2. Include exactly one complete JSON declaration between the mission markers.
3. Obtain the Ready transition before claiming work.
4. Claim the mission and maintain its bounded lease and heartbeat.
5. Work only inside the declared paths, capabilities, budgets, and authority.
6. Run every declared validation command and retain machine-derived evidence.
7. Send the exact head to a distinct independent adversary.
8. Remediate every valid Critical and Important finding and repeat review.
9. Request founder approval bound to the exact repository, pull request, head,
   environment, action, merge method, and expiry.
10. Merge only after authorization. Deployment, cutover, cloud mutation, spend,
    secrets, customer data, and rollback execution remain separate actions.

## Minimal mission example

Replace example identities, paths, commands, limits, and issue-specific values.
The declaration must remain valid JSON.

```text
<!-- EOS:MISSION:BEGIN -->
{
  "schema_version": "1.0.0",
  "mission_id": "aifo-control-plane-123",
  "repository": "josephmccann/AIFO-Control-Plane",
  "title": "Document one bounded control",
  "objective": "Add one reviewed operating control without external mutation.",
  "acceptance_criteria": ["The focused test passes", "The full EOS gate passes"],
  "allowed_paths": ["docs/engineering-os/**", "tests/engineering_os/**"],
  "prohibited_paths": ["terraform/**"],
  "dependencies": [],
  "founder_decisions": ["Written founder authorization for the mission"],
  "risk_tier": "Tier 2",
  "capabilities": ["read", "write"],
  "budgets": {
    "model_cost_usd": 25.0,
    "model_tokens": 250000,
    "wall_clock_minutes": 240,
    "remediation_cycles": 2,
    "concurrent_agents": 4,
    "ci_reruns": 3
  },
  "validation_commands": [
    "python3 -m unittest tests.engineering_os.test_documentation -v",
    "git diff --check"
  ],
  "rollback": {
    "class": "clean_revert",
    "plan": "Revert the package commit; no external system was mutated."
  },
  "assignments": {
    "producer": {"identity": "producer-name", "model_family": "family-a"},
    "adversary": {"identity": "reviewer-name", "model_family": "family-b"}
  },
  "eos": {
    "version": "1.0.0",
    "constitution_sha256": "a255c0976949d8acae91f7d46e85cc083a15e242ccbd62e587c4e3163b29265e"
  }
}
<!-- EOS:MISSION:END -->
```

## Pull request example

The mission marker is machine-readable and must contain the authoritative issue
number.

```markdown
<!-- AIFO-EOS-MISSION-ISSUE: 123 -->

## Problem

State the bounded problem and why it belongs to this mission.

## Solution

Describe only the implemented scope and the exact reviewed head.

## Verification

List commands and machine results. Link independent review and evidence.

## Rollback

State the declared rollback class and executable recovery plan.
```

Founder approval is required for merge. Opening a pull request, passing tests,
or receiving reviewer approval does not authorize merge or any external action.

## Queue and recovery

Use lifecycle labels and issue history as the authoritative queue. A missing or
expired lease, malformed history, conflict, crossed budget, expanded scope, or
unresolved finding stops or parks the mission. Scheduled orphan recovery is
dry-run only. Human operators and agents submit the same authenticated commands
and receive decisions from the same kernel.

## Activation prerequisites

Before activating a new repository caller, verify its base policy, immutable
workflow pin, private Actions access, actual required-check contexts, branch
protection, founder identity, dry-run defaults, and disabled capabilities.
See [Known Enforcement Gaps](KNOWN_ENFORCEMENT_GAPS.md).
