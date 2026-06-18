# Runtime Rollout Evidence

DriveDesk includes a public-safe private staging rollout evidence layer. It
connects the private staging runtime to the public DevOps story without exposing
server names, network addresses, credentials, raw logs, request bodies, or
production data.

## Command

```bash
bash scripts/check_public_runtime_rollout.sh
```

## What The Check Does

The check validates the sanitized private staging rollout loop:

```text
candidate source
    |
private staging deploy
    |
runtime health gates
    |
observability gates
    |
sanitized evidence artifact
```

The check verifies:

- rollout contract is recorded;
- build, deploy, runtime health, observability, and evidence stages are present;
- private staging deploy, health, and evidence checks succeeded;
- the runtime has no public route in the public evidence;
- API health, readiness, and metrics checks passed;
- Prometheus, Loki, Alertmanager, and Grafana checks passed;
- rollback strategy is recorded;
- public evidence excludes addresses, credentials, raw logs, request bodies, and
  production data.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "check": "public_runtime_rollout_evidence",
  "data_profile": "synthetic_fake_data",
  "rollout_model": "github_actions_to_private_loopback_staging",
  "checks": {
    "staging_deploy_success": true,
    "staging_health_success": true,
    "staging_evidence_success": true,
    "loopback_boundary_recorded": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public rollout evidence uses a sanitized contract and sanitized staging
summary. It does not include live endpoints, server-specific paths, hostnames,
network addresses, credentials, raw logs, request bodies, private runtime
connection values, or production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/runtime-rollout.sanitized.json
```

The public-safe rollout contract is stored at:

```text
infra/runtime-rollout/private-staging-rollout.sanitized.json
```

## Why This Matters

Deployment work is only useful if the runtime can be checked after the change.
This layer shows the release loop after GitOps and infrastructure planning:
deploy to private staging, prove health, prove observability, record sanitized
evidence, and keep public artifacts free of private operational details.
