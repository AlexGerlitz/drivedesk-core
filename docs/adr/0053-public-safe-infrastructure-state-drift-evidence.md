# ADR-0053: Public-Safe Infrastructure State Drift Evidence

Status: accepted

## Context

DriveDesk now has public-safe OpenTofu plan evidence. The next infrastructure
question is:

```text
How is desired infrastructure state compared with observed state?
```

The public repository must not contain real state files, backend configuration,
cloud account IDs, live endpoints, addresses, credentials, raw logs, runtime
connection values, or production data.

## Decision

Add public-safe infrastructure state drift evidence:

```text
infra/opentofu/state/desired-state.sanitized.json
infra/opentofu/state/observed-state.sanitized.json
infra/opentofu/state/drift-summary.sanitized.json
```

Add an executable check:

```text
scripts/check_public_infra_state_drift.sh
```

The check validates desired state, observed state, component inventory matching,
state backend boundary, secret boundary, detected drift, in-sync components,
and plan-only no-apply behavior.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/infra-state-drift.sanitized.json
```

It records the drift shape without real state files, backend configuration,
cloud account IDs, live endpoints, addresses, credentials, raw logs, runtime
connection values, or production data.

## Consequences

- The public project now demonstrates the loop after an IaC plan: compare
  desired and observed state, detect drift, and plan remediation.
- The evidence remains synthetic and safe to publish.
- This is not a claim that public infrastructure exists or was queried.
