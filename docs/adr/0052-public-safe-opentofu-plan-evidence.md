# ADR-0052: Public-Safe OpenTofu Plan Evidence

Status: accepted

## Context

DriveDesk already has public-safe Docker, Helm, GitOps delivery, image
automation, drift, and remediation evidence. The next infrastructure question
is:

```text
How is the target infrastructure shape described before any real apply?
```

The public repository must not contain cloud credentials, state files, backend
secrets, private endpoints, addresses, raw logs, runtime connection values, or
production data.

## Decision

Add a public-safe OpenTofu plan evidence layer:

```text
infra/opentofu/public/main.tf
infra/opentofu/public/variables.tf
infra/opentofu/public/outputs.tf
infra/opentofu/public/plan-summary.sanitized.json
```

Add an executable check:

```text
scripts/check_public_opentofu_plan.sh
```

The check validates the public IaC contract, environment model, component
model, state boundary, secret boundary, sanitized plan summary, and plan-only
no-apply behavior.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/opentofu-plan.sanitized.json
```

It records infrastructure shape without cloud credentials, state files, backend
configuration, private endpoints, addresses, raw logs, runtime connection
values, or production data.

## Consequences

- The public project now demonstrates the infrastructure-as-code layer after
  Docker, Helm, and GitOps.
- The evidence remains plan-only and safe to publish.
- This is not a claim that public infrastructure was provisioned.
