# Producer and adversary model

The producer implements a mission. The adversary evaluates the resulting
artifact and records normalized findings. They must be different authenticated
identities. Repository policy may also require a different model family. If a
different model family is unavailable, the gap is evidence rather than an
implicit waiver and merge authorization requires an exact founder decision.

Findings have one of four dispositions: `valid`, `invalid`, `duplicate`, or
`founder_decision`. A valid finding returns work to remediation. Invalid and
duplicate findings remain in the record because disagreement and false
positives are operational evidence. There is no required rejection rate and no
incentive to manufacture or suppress findings.

The founder remains the only merge authority in EOS v1. Adversarial review does
not grant merge, deployment, cloud, spend, secret, customer-data, or cutover
authority.
