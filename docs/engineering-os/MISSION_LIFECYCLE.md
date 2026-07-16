# Mission lifecycle

Missions move through Proposed, Ready, Claimed, In Progress, Adversarial Review,
Founder Approval, Merge Authorized, Merged, Verified, and Closed. Parked,
Cancelled, and Incident are explicit states. Every transition uses the same
authenticated event and policy kernel for humans and agents.

Merge authorization emits a decision only. It never invokes a merge API.
