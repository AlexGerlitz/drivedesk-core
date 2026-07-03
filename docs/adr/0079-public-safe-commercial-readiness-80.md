# ADR-0079: Public-Safe Commercial Readiness 80 Percent Milestone

Status: accepted

## Context

DriveDesk already has a public-safe 70 percent DevOps/platform milestone. The
next goal is to move toward a commercial Business OS product without claiming
that the SaaS is finished or exposing private provider credentials, customer
data, runtime state, or production evidence.

The project needs a milestone that explains the shift from platform foundation
to commercial readiness in a way that remains verifiable through public-safe
artifacts.

## Decision

Add a public-safe 80 percent commercial readiness milestone artifact:

- source contract:
  `infra/platform-maturity/commercial-readiness-80.sanitized.json`;
- public evidence:
  `docs/public/evidence/commercial-readiness-80.sanitized.json`;
- public explanation:
  `docs/public/COMMERCIAL_READINESS_80.md`;
- executable checker:
  `scripts/check_public_commercial_readiness_80.sh`.

The milestone is split into eight evidence groups:

- platform maturity foundation;
- product workbench previews;
- provider sandbox path;
- action approval safety;
- API and SDK contract;
- operations and release evidence;
- public/private boundary;
- commercial gap control.

Each group is worth ten points. The milestone is reached only when all eight
groups are present, complete, public-safe, and tied to executable gates.

## Consequences

- The public repository gets a clear next milestone after the 70 percent
  DevOps/platform proof.
- The milestone remains honest: it explicitly does not claim finished
  commercial SaaS readiness.
- The next private step is clear: one approved real-provider sandbox run with
  sanitized evidence and no public secret exposure.
- The private repository remains the source for commercial product work,
  production state, provider credentials, and runtime operations.
