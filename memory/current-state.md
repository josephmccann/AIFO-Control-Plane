# Current State

Date: 2026-07-14

## Repository

- Repository: `josephmccann/AIFO-Control-Plane`
- Baseline commit: `4da93f1b674abf108e8c0e1bcb1d97c7a122baed`
- Working branch: `docs/product-context-operating-model`
- No infrastructure has been deployed from this repository.
- No `terraform apply` or `terraform destroy` has been run in this workstream.

## Product Context

- Product repository: `/Users/joemccann/code/AI.FO-Demo`
- Product baseline branch: `master`
- Observed baseline commit: `8df211e02f274d0a812771327c69b6d5b6c040d2`
- Current product is a working financial intelligence platform with deterministic financial engine, QBO ingestion, CSV ingestion, PostgreSQL, R2, AI narrative generation, and verifier support.

## Infrastructure Baseline

- Terraform remote state bootstrap root exists.
- GitHub OIDC bootstrap root exists.
- Control-plane environment exists.
- Initial network is one public subnet in one Availability Zone.
- Initial host has public IPv4, zero inbound rules, SSM-only administration, IMDSv2, encrypted root volume, and controlled HTTPS/DNS egress.
- Product runtime infrastructure is not yet provisioned.

## Current Branch Changes

- Mandatory product-context pre-work docs added.
- Operating model docs added.
- ADR framework added.
- Runbooks, memory, workstreams, and workqueue added.
- Terraform plan role narrowed from AWS managed `ReadOnlyAccess` to a custom plan read policy.
- EC2 detailed monitoring disabled by default.
- Example root volume size reduced to 100 GiB.
