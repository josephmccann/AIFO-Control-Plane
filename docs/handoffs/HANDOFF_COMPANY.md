# AI.FO Company Handoff

## Purpose

This document is the canonical starting context for company operations, founder discovery, fundraising, strategic priorities, and organizational memory.

## Stable Context

Founder: Joseph McCann

Background:

- More than 20 years of executive leadership experience.
- Former CFO and COO of the Center for Care Innovations.
- Senior executive experience across multiple organizations.
- Building AI.FO to provide high-quality CFO analysis and decision support to small and mid-sized companies and organizations below roughly $50 million in revenue.

## Founder Operating Philosophy

- Trust is the center. Silos are one of the primary causes of failed trust.
- Trust is earned, not assumed.
- Leaders should remain students and continue asking questions.
- Once curiosity and learning stop, failure begins.
- Nothing is static; decision frameworks must adapt to company size, growth, geography, market, and context.
- Reflection turns experience into learning.
- The most valuable guidance helps people discover the questions they did not know to ask.
- A leader should improve the shared model of reality rather than win an argument.
- When someone says "I don't know," the next question is why: missing information, context, experience, or another constraint?
- Ask more questions than you think you need to. The wrong answer is often the question that was never asked.

## Company Mission Direction

AI.FO exists to expand access to high-quality financial judgment.

The company is intended to prove that trust, transparency, humility, explainability, and intellectual honesty can outperform hype in building an AI company.

Finance is the initial proving ground because errors are measurable, trust requirements are high, and founder-led businesses are underserved by traditional CFO capacity.

## Current Strategic Priorities

1. Get AI.FO into the hands of real users.
2. Complete 25 standardized founder and finance-leader interviews.
3. Identify five to ten design partners.
4. Convert evidence into a stronger investor narrative.
5. Raise external capital as soon as credible customer and product evidence supports it.
6. Build a secure, reproducible internal control plane without allowing infrastructure to displace customer learning.

## Founder Discovery Program

Research objective:

> Understand how founder-led companies make consequential financial decisions today.

The interviews should not ask participants whether they like AI.FO or would buy an abstract product. Each interview should reconstruct one real financial decision and examine:

- trigger;
- stakes;
- data sources;
- missing information;
- assumptions;
- participants and advisors;
- tools and systems;
- uncertainty;
- timing and delay;
- decision and outcome;
- hindsight and learning.

Target mix for 25 interviews:

- approximately 10 companies with no senior finance leader;
- approximately 10 companies using fractional CFO support;
- approximately 5 companies with an in-house CFO or senior finance leader.

Target company profile:

- founder-led;
- generally below $50 million in annual revenue;
- meaningful financial and operating decisions made by the founder or CEO;
- mix of industries and stages, while preserving enough comparability for pattern analysis.

## Recruiting Channels

- NextPlay Slack community
- AI Collective Slack community
- LinkedIn public post
- LinkedIn direct outreach
- Existing professional network and referrals
- Potential design-partner introductions

Slack cannot currently be connected directly. Joe will copy and paste approved posts and responses. LinkedIn supports professional lookup but current tooling may not permit direct posting or messaging. Gmail and Calendar are connected for outreach and scheduling once contacts and approved messages are available.

## Research Operating System

An Airtable base has been created with:

- Participants
- Interviews
- Insights
- Outreach

Outreach drafts have been seeded for:

- LinkedIn post
- LinkedIn direct message
- NextPlay
- AI Collective

A Google Drive folder named `AI.FO Operating System` exists for working artifacts.

The standardized research package should include:

- research hypotheses;
- uniform interview guide;
- scoring rubric;
- interview note template;
- evidence and quote extraction;
- five-interview synthesis cadence;
- design-partner qualification;
- final research report.

## Fundraising Direction

The investor narrative should be grounded in customer evidence and product use rather than a long founder canon.

Likely narrative:

- founder-led SMBs lack continuous access to high-quality financial judgment;
- their decision data is fragmented across accounting, payments, CRM, payroll, spreadsheets, and human knowledge;
- existing finance software reports and plans but does not create an explainable, continuously learning decision process;
- AI.FO combines deterministic financial truth, connected operating context, evidence lineage, and human-governed reasoning;
- the initial wedge is continuous financial decision support;
- the longer-term opportunity is institutional reasoning for founder-led businesses.

Avoid unsupported claims such as being the first enterprise reasoning system. Related categories and competitors already exist.

## Current Infrastructure State

- AWS account created.
- Root account MFA enabled.
- IAM Identity Center enabled.
- Joe's company identity created.
- `AIFO-Platform-Admin` permission set assigned.
- Manual monthly AWS budget created at $250.
- Private GitHub repository `josephmccann/AIFO-Control-Plane` created and initialized.
- Terraform scaffold exists and has passed offline validation.
- No Terraform deployment has occurred.

## Current Workstreams

### Control Plane

Build the secure AWS execution environment through Terraform, GitHub Actions OIDC, Systems Manager, and an approval-gated deployment process.

### Product

Reduce AI.FO to a useful financial decision workflow that can be placed in design-partner hands quickly.

### Founder Discovery

Recruit and complete 25 structured interviews, synthesize every five interviews, and identify design partners.

### Fundraising

Prepare the investor narrative, target pipeline, evidence package, and outreach once customer signals and product usage are credible.

### Company Memory

Preserve durable principles, current state, decisions, and handoffs in version-controlled artifacts rather than relying on conversation history.

## Immediate Decisions and Actions

- Finish and merge the three handoff documents.
- Prepare the account-specific AWS bootstrap checklist.
- Keep infrastructure work bounded so founder recruiting can begin immediately.
- Publish the LinkedIn, NextPlay, and AI Collective recruiting messages after final review.
- Establish a scheduling link or approved calendar workflow.
- Begin outreach and populate the first participant pipeline.
- Conduct interviews using the same core guide for comparability.

## Operating Rule

Conversations are working sessions. Their outputs should become durable artifacts in GitHub, Drive, or Airtable. No critical company knowledge should exist only in a chat history.