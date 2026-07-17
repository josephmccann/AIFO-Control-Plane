# Engineering Operating System Risk Tiers

Risk is the maximum supported by the mission declaration, changed paths,
requested capabilities, and repository policy. The kernel may raise but never
lower a declared tier. Under-declaration is a denial; over-declaration is
allowed and keeps the higher-tier gates.

## Tier 0

Non-behavioral maintenance that is explicitly matched by repository policy.
Examples may include spelling or formatting changes with no effect on claims,
controls, generated artifacts, workflows, or behavior. A change is not Tier 0
merely because it is small.

## Tier 1

Bounded behavioral work within one declared semantic domain, with complete
tests and no Tier 2 trigger. Its paths, owner, dependencies, validation,
rollback, and authority remain explicit.

## Tier 2

Tier 2 is mandatory for schemas, deployment or cloud behavior, customer data,
financial methodology, secrets, destructive action, spend, security or
privacy controls, public claims, cross-module or cross-repository work,
residual risk, irreversible behavior, governance and policy, or any path and
capability configured by repository policy as Tier 2.

Tier 2 requires the complete evidence and adversarial-review path plus exact,
current founder approval for the requested action and revision. Merge approval
does not authorize deployment, cutover, cloud mutation, secrets, customer
data, spend, or rollback execution.

## Classification failure behavior

Unknown or conflicting evidence fails closed. Frozen paths and prohibited
paths are separate constraints: a high tier does not override them. A risk
classification is not authority, and authority is not approval.
