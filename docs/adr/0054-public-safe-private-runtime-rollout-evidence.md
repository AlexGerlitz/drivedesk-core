# ADR-0054: Public-Safe Private Runtime Rollout Evidence

Status: accepted

## Context

DriveDesk has public-safe evidence for backup/restore, release rollback, SLO
promotion gates, Helm packaging, GitOps delivery, image automation, OpenTofu
planning, and infrastructure state drift. The next operational question is:

```text
Can a candidate change be deployed to private staging and proven healthy?
```

The public repository must not contain server-specific paths, hostnames,
network addresses, credentials, raw logs, request bodies, runtime connection
values, or production data.

## Decision

Add public-safe private staging runtime rollout evidence:

```text
infra/runtime-rollout/private-staging-rollout.sanitized.json
docs/public/evidence/runtime-rollout.sanitized.json
docs/public/RUNTIME_ROLLOUT_EVIDENCE.md
```

Add an executable check:

```text
scripts/check_public_runtime_rollout.sh
```

The check validates the sanitized rollout contract, build/deploy/runtime health
stages, observability gates, sanitized staging evidence, rollback strategy, and
the no-public-route/no-production-data boundary.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/runtime-rollout.sanitized.json
```

It records the private staging rollout shape without exposing endpoints,
addresses, credentials, raw logs, request bodies, runtime connection values, or
production data.

## Consequences

- The public project now demonstrates the operational loop after CI, GitOps,
  and infrastructure planning.
- The evidence remains sanitized and reviewer-readable.
- This is not a claim that the public repository can deploy to private staging.
  It is a public-safe proof of the private staging rollout model and evidence
  boundary.
