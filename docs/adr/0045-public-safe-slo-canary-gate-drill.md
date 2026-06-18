# ADR-0045: Public-Safe SLO Canary Gate Drill

Status: accepted

## Context

DriveDesk now has public-safe CI, API smoke checks, generated SDK checks,
integration incident runbooks, a synthetic backup/restore drill, and a
synthetic release rollback drill. The next DevOps question is:

```text
Can the platform prove that a release candidate is blocked before promotion
when it violates availability, latency, or error budget expectations?
```

The public repository must not contain private deployment targets, hostnames,
service names, credentials, raw metrics, or production incident details.

## Decision

Add a public-safe SLO canary gate drill:

```text
scripts/check_public_slo_canary_gate.sh
```

The drill:

- creates temporary synthetic stable and candidate metrics;
- evaluates the stable baseline against public SLO thresholds;
- evaluates the candidate canary against the same thresholds;
- detects availability, p95 latency, and error budget burn violations;
- blocks candidate promotion;
- records a synthetic `release.canary_gate.blocked` audit event;
- emits a machine-readable JSON summary.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/slo-canary-gate.sanitized.json
```

It records the gate model and checks without private paths, hostnames,
addresses, credentials, raw logs, or production data.

## Consequences

- Public CI can prove that release promotion is guarded by service objectives.
- Reviewers can run the same check locally without infrastructure access.
- The public project demonstrates staged promotion, error-budget thinking, and
  auditability without exposing private deployment implementation details.
- This is not a substitute for private staging or production canary gates; it
  is the public-safe evidence layer.
