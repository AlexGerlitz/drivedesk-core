# ADR-0046: Public-Safe Staged Promotion Drill

Status: accepted

## Context

DriveDesk now has public-safe CI, API smoke checks, generated SDK checks,
backup/restore evidence, release rollback evidence, and SLO canary gate
evidence. The next DevOps question is:

```text
Can the platform prove that a safe release can move through build, staging,
canary, and production promotion gates with auditable evidence?
```

The public repository must not contain private deployment targets, hostnames,
service names, credentials, raw metrics, production approvals, or production
incident details.

## Decision

Add a public-safe staged promotion drill:

```text
scripts/check_public_staged_promotion.sh
```

The drill:

- creates a temporary synthetic build manifest;
- evaluates build, staging, canary, and production gates;
- records synthetic production approval;
- attaches rollback-plan evidence;
- records promotion history;
- records a synthetic `release.staged_promotion.completed` audit event;
- emits a machine-readable JSON summary.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/staged-promotion.sanitized.json
```

It records the staged promotion shape and checks without private paths,
hostnames, addresses, credentials, raw logs, production approvals, or
production data.

## Consequences

- Public CI can prove that the release process has an auditable staged
  promotion contract.
- Reviewers can run the same check locally without infrastructure access.
- The public project demonstrates release traceability without exposing private
  deployment implementation details.
- This is not a substitute for private staging or production promotion
  workflows; it is the public-safe evidence layer.
