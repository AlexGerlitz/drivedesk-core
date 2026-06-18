# ADR-0061: Public-Safe Platform Maturity 70 Percent Milestone

Status: accepted

## Context

DriveDesk is being developed as a private product source and a public-safe
engineering surface. The project needs a clear milestone that can be reviewed
without exposing private infrastructure, private operations, customer data, raw
logs, or runtime secret material.

The current goal is not to prove that DriveDesk is a finished commercial SaaS
product. The goal is to prove that it has reached a serious DevOps/platform
platform maturity foundation.

## Decision

Add a public-safe 70 percent DevOps/platform milestone artifact:

- source contract:
  `infra/platform-maturity/platform-maturity-70.sanitized.json`;
- public evidence:
  `docs/public/evidence/platform-maturity-70.sanitized.json`;
- public explanation:
  `docs/public/PLATFORM_MATURITY_70.md`;
- executable checker:
  `scripts/check_public_platform_maturity_70.sh`.

The milestone is split into seven evidence groups:

- core platform foundation;
- public engineering surface;
- CI and release safety;
- IaC, packaging, and GitOps;
- observability and SRE;
- security and data boundary;
- recovery and drift operations.

Each group is worth ten points. The milestone is reached only when all seven
groups are present, complete, public-safe, and tied to executable gates.

## Consequences

- The public repository gets a clear engineering entry point for the 70 percent
  DevOps/platform milestone.
- The private repository keeps the real product and private operations.
- The milestone is checked by automation instead of being a docs-only claim.
- The artifact explicitly avoids claiming commercial SaaS completeness.
- Future work can move from platform maturity toward product maturity without
  rewriting the public proof chain.
