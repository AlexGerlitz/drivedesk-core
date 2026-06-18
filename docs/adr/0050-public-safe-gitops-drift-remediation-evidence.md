# ADR-0050: Public-Safe GitOps Drift Remediation Evidence

Status: accepted

## Context

DriveDesk has public-safe GitOps delivery, image promotion, and drift detection
evidence. The next operational question is:

```text
When drift is detected, what action is planned and how is it kept safe?
```

The public repository must not contain live cluster endpoints, runtime
connection values, raw logs, credentials, or production data.

## Decision

Add public-safe GitOps drift remediation evidence:

```text
infra/gitops/remediation/policy.yaml
infra/gitops/remediation/decision.yaml
```

Add an executable check:

```text
scripts/check_public_gitops_drift_remediation.sh
```

The check validates drift inputs, remediation policy, production approval,
plan-only behavior, rollback context, block/reconcile actions, and the
redaction boundary.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/gitops-drift-remediation.sanitized.json
```

It records the remediation shape without live cluster endpoints, addresses,
credentials, raw logs, runtime connection values, or production data.

## Consequences

- The public project now demonstrates the loop after drift detection:
  evaluate, plan, require approval, attach rollback context, and avoid unsafe
  automatic production mutation.
- The evidence remains synthetic and readable.
- This is not a claim that a public cluster exists.
