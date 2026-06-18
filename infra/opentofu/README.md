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
