# DriveDesk OpenTofu Foundation

This folder contains public-safe infrastructure-as-code evidence for DriveDesk
Core.

It does not provision a real cloud account. The public layer describes the
target infrastructure contract and validates a sanitized plan summary without
provider credentials, runtime secrets, live endpoints, or production data.

## Layout

```text
infra/opentofu/
  public/
    main.tf
    variables.tf
    outputs.tf
    plan-summary.sanitized.json
  state/
    desired-state.sanitized.json
    observed-state.sanitized.json
    drift-summary.sanitized.json
```

## Plan Shape

```text
OpenTofu contract
  -> environment and component model
  -> state and secret boundary
  -> sanitized plan summary
  -> public validation script
```

The public plan is evidence only. It is intentionally plan-only and does not run
`apply`, mutate infrastructure, create cloud resources, or include live backend
configuration.

## Drift Shape

The `state/` files are sanitized desired/observed snapshots. They are not real
OpenTofu state files and do not contain backend configuration, provider
credentials, cloud account identifiers, live endpoints, or production data.

The drift evidence compares public-safe desired infrastructure with a synthetic
observed snapshot, records drift for observability and backup storage, and keeps
the response plan-only.
