# ADR-0002: Public IPv4 SSM-Only Control Host

## Status

Accepted

## Current Product Requirement Supported

The initial operator host must install packages, clone GitHub repositories, pull containers, and call external APIs including Intuit, OpenAI-compatible providers, Anthropic, Google, Cloudflare R2, and package registries.

## Founder Principle Or Constitutional Principle Implicated

Principles 1, 14, 18, 20, and 23: trust through evidence, honest limitations, auditability without excess collection, best-in-class discipline, and avoiding unnecessary infrastructure.

## Known Facts

- AWS Systems Manager Session Manager supports node management without open inbound ports, bastion hosts, or SSH keys.
- NAT Gateways have hourly and data-processing charges.
- Internet Gateways do not have a separate hourly charge, though EC2 data transfer and public IPv4 charges apply.
- The Terraform host security group has zero ingress rules.
- The host has no SSH key pair and requires IMDSv2.

## Assumptions

- Public IPv4 plus zero inbound security-group rules is acceptable for the initial control-plane host. Confidence: medium.
- Private subnet plus NAT is not justified under the current $250 budget. Confidence: high.

## Unknowns

- Whether future compliance or customer review will require private-only host addressing.
- Whether package and API egress should later move through proxy, firewall, or endpoint controls.

## Information Sources Reviewed

- AWS Systems Manager Session Manager: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html
- AWS NAT Gateway pricing: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-pricing.html
- AWS Internet Gateway documentation: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html
- AWS VPC pricing: https://aws.amazon.com/vpc/pricing/
- AWS Startup Security Baseline WKLD.06: https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-startup-security-baseline/wkld-06.html

## Decision

Use one public subnet in one Availability Zone for the initial control-plane host. Assign a public IPv4 address, retain zero inbound security-group rules, omit SSH keys, require IMDSv2, use SSM Session Manager for administration, and allow outbound HTTPS plus DNS only.

## Why This Decision Is Appropriate Now

The host needs outbound public internet access immediately. A private subnet with NAT Gateway would meet the requirement but adds recurring cost and operational surface before the product runtime is designed.

## Alternatives Considered

- Private subnet with NAT Gateway.
- Private subnet with interface endpoints only.
- Public subnet with SSH restricted to a trusted IP.
- No EC2 host.

## Why Alternatives Were Rejected Or Deferred

- NAT Gateway is deferred because of recurring hourly and data-processing cost.
- Interface endpoints alone do not cover GitHub, registries, package mirrors, model APIs, Intuit, Google, and R2 without more architecture.
- SSH is rejected because SSM is the administrative boundary.
- No EC2 host would leave no AWS execution surface for future approved operator workflows.

## Security Effects

The design exposes a public address but no inbound security-group path. Administration is identity-based through SSM. The main residual risk is host compromise through outbound-fetched software or vulnerable local services.

## Privacy Effects

No customer data is introduced by the host itself. Future workloads must not place raw accounting data on the host without a data-handling decision.

## Reliability Effects

The host depends on internet egress and public AWS service endpoints. One Availability Zone is a known single-AZ limitation.

## Cost Effects

Avoids NAT Gateway hourly and data-processing charges. Public IPv4, EC2 compute, EBS, and data transfer still create recurring cost.

## Operational Burden

Lower than managing NAT, endpoints, and private routing at this stage. Requires periodic review of egress and patch posture.

## Solo-Founder Recoverability

Simple topology is recoverable by one operator. SSM access should be verified after first apply.

## Product Impact

Supports repository cloning, product validation tooling, package installation, and API egress for future controlled work.

## Data-Lineage Impact

No direct product lineage effect. Future product data processing on this host requires a separate decision.

## Auditability Impact

AWS CloudTrail, SSM session history, GitHub Actions, and Terraform state provide audit evidence after bootstrap.

## Reversibility

Reversible by migrating the instance to a private subnet design or recreating it in a private network.

## Rollback Or Migration Path

Add private subnets, add NAT Gateway or endpoint/proxy egress, move the host to a private subnet, remove public IPv4, and verify SSM connectivity before destroying public networking.

## Evidence That Would Cause Reconsideration

- Compliance review rejects public IPv4 on administrative hosts.
- The host begins handling customer financial data.
- Monthly spend supports NAT or network firewalling.
- Outbound egress requires centralized inspection or allowlisting.
