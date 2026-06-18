# Private Infrastructure Validation

DriveDesk includes a public-safe private infrastructure validation layer. It
records how the private staging/control-plane state is checked before any
apply, deploy, or remediation decision, while keeping public artifacts free of
private addresses, hostnames, paths, credentials, raw logs, request bodies, and
production data.

## Command

```bash
bash scripts/check_public_private_infra_validation.sh
```

## What The Check Does

The check validates the read-only private infrastructure validation loop:

```text
private staging summary
    |
OpenTofu and GitOps contracts
    |
runtime rollout evidence
    |
read-only validation boundary
    |
sanitized public evidence
```

The check verifies:

- the validation contract is present;
- the collector is read-only;
- no runtime mutation, infrastructure apply, or service restart is recorded;
- private staging evidence is referenced;
- runtime components are validated;
- observability state is validated;
- OpenTofu, infrastructure drift, runtime rollout, and GitOps contracts are
  referenced;
- loopback-only and no-public-route boundaries are recorded;
- operator review is required before remediation;
- public evidence excludes addresses, credentials, raw logs, request bodies,
  private paths, and production data.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_private_infra_validation",
  "data_profile": "sanitized_private_staging_summary",
  "validation_model": "private_control_plane_state_validation",
  "checks": {
    "read_only_collector_recorded": true,
    "no_runtime_mutation_recorded": true,
    "runtime_components_validated": true,
    "observability_state_validated": true,
    "operator_review_required": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public validation evidence uses sanitized private staging summaries and
public-safe infrastructure contracts. It does not include live endpoints,
server-specific paths, hostnames, network addresses, credentials, raw logs,
request bodies, private runtime connection values, or production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/private-infra-validation.sanitized.json
```

The public-safe validation contract is stored at:

```text
infra/state-validation/private-infra-validation.sanitized.json
```

## Why This Matters

Infrastructure automation is risky if it jumps directly from desired state to
apply. This layer shows the safer middle step: read the private environment,
compare it with the Git/OpenTofu/GitOps contracts, record sanitized evidence,
and require operator review before any mutation.
