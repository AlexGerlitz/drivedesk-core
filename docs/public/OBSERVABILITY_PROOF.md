# Observability Proof

DriveDesk Core exposes a public-safe observability proof for the exported
engineering surface. It connects metrics, structured logs, alert rules,
runbooks, and dashboard panels without exposing private runtime telemetry.

## Evidence

Machine-readable evidence:

```text
docs/public/evidence/observability-proof.sanitized.json
infra/observability/observability-proof.sanitized.json
```

Verifier:

```bash
bash scripts/check_public_observability_proof.sh
```

## Signals

| Signal type | Public-safe examples | Purpose |
| --- | --- | --- |
| Metrics | `drivedesk_http_requests_total`, `drivedesk_http_request_duration_seconds_bucket`, `drivedesk_outbox_events`, `drivedesk_integration_jobs`, `drivedesk_auth_attempts_total` | Show request health, latency, queue depth, integration status, and auth health with aggregate labels. |
| Logs | `api.request.completed`, `adapter.completed`, `outbox_event.retry_requested` | Correlate API, worker, adapter, and retry events without raw provider payloads. |
| Alerts | `DriveDeskApiTargetDown`, `DriveDeskApiHighLatencyP95`, `DriveDeskIntegrationDeadLetters`, `DriveDeskAuthFailureSpike`, `DriveDeskNoRecentLogs` | Tie operational symptoms to runbooks and synthetic evidence. |
| Dashboards | API availability, latency, outbox health, integration health, auth health, structured logs | Show the review path an operator would use during an incident. |

## Dashboard Contract

The public proof does not publish live private dashboards. Instead it records the
dashboard contract as public-safe evidence:

- API availability and latency panels use request counters and duration
  histograms;
- outbox and integration panels use retry, dead-letter, and adapter job metrics;
- auth panels use aggregate session and login-attempt metrics;
- structured-log panels use safe event names and service labels;
- dashboard evidence does not include hostnames, addresses, credentials, raw
  logs, production screenshots, or customer data.

## Alert Contract

Each alert must have:

- a stable alert name;
- severity;
- safe signal source;
- public runbook or evidence document;
- no private endpoint, token, address, or raw payload.

## Boundary

This is a public-safe proof of the observability loop. It is not a live
production telemetry export. Private Prometheus, Grafana, Loki, Alertmanager,
and runtime evidence remain outside the public repository. The public evidence
contains synthetic data, sanitized signal names, aggregate labels, and verifier
commands only.

## Related Docs

- `docs/public/AUTH_OBSERVABILITY.md`
- `docs/public/INTEGRATION_OBSERVABILITY.md`
- `docs/public/SLO_CANARY_GATE_EVIDENCE.md`
- `docs/public/RUNTIME_ROLLOUT_EVIDENCE.md`
- `docs/public/PRIVATE_INFRA_SCHEDULED_ALERTING.md`
- `docs/public/TECHNICAL_CAPABILITY_MAP.md`
- `docs/public/PROJECT_STATUS.md`
