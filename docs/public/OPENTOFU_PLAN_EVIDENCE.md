# OpenTofu Plan Evidence

DriveDesk includes a public-safe OpenTofu plan evidence layer. It shows the
infrastructure-as-code shape without provisioning a real cloud account.

## Command

```bash
bash scripts/check_public_opentofu_plan.sh
```

## What The Check Does

The check validates the synthetic IaC flow:

```text
OpenTofu contract
    |
environment and component model
    |
state and secret boundary
    |
sanitized plan summary
    |
plan-only validation
```

The check verifies:

- OpenTofu files are present;
- build, staging, canary, and production environments are recorded;
- network, runtime, GitOps, observability, backup, and secrets-boundary
  components are recorded;
- encrypted state and locking expectations are documented;
- public backend configuration is not included;
- secret values are excluded;
- the public plan is plan-only;
- destroy count is zero;
- production data is not touched.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_opentofu_plan",
  "data_profile": "synthetic_demo_data",
  "iac_model": "opentofu_plan_only_infrastructure_contract",
  "checks": {
    "opentofu_files_present": true,
    "state_boundary_recorded": true,
    "plan_only_no_apply": true,
    "destroy_count_zero": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public plan uses synthetic data and public-safe component names. It does not
include cloud credentials, real backend configuration, state files, hostnames,
addresses, raw logs, runtime connection values, or production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/opentofu-plan.sanitized.json
```

## Why This Matters

GitOps shows how application desired state is delivered. OpenTofu evidence
shows the next infrastructure layer: environments, runtime components, state
handling, and secret boundaries can be described and checked before any real
cloud account is touched.
