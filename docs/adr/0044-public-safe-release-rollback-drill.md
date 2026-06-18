# ADR-0044: Public-Safe Release Rollback Drill

Status: accepted

## Context

DriveDesk now has public-safe CI, API smoke checks, generated SDK checks,
integration incident runbooks, and a synthetic backup/restore drill. The next
DevOps question is:

```text
Can the platform prove that a bad release can be detected and rolled back?
```

The public repository must not contain private deployment targets, hostnames,
service names, credentials, or production incident details.

## Decision

Add a public-safe release rollback drill:

```text
scripts/check_public_release_rollback.sh
```

The drill:

- creates a temporary release directory;
- creates a healthy synthetic stable release manifest;
- creates an unhealthy synthetic candidate release manifest;
- points `current` at the stable release;
- promotes the candidate release;
- detects the synthetic readiness failure;
- rolls `current` back to the stable release;
- verifies the stable release is active and healthy after rollback;
- records a synthetic `release.rollback.executed` audit event;
- emits a machine-readable JSON summary.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/release-rollback-drill.sanitized.json
```

It records the rollback shape and checks without private paths, hostnames,
addresses, credentials, raw logs, or production data.

## Consequences

- Public CI can prove that rollback logic exists as an executable contract.
- Reviewers can run the same check locally without infrastructure access.
- The drill demonstrates release safety without exposing private deployment
  implementation details.
- This is not a substitute for private staging or production rollback drills;
  it is the public-safe evidence layer.
