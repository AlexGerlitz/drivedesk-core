# Observability Dashboard

DriveDesk Core includes a public-safe dashboard contract for the operations
surface. It describes the Grafana-style views an operator would use without
exporting private Prometheus, Loki, Grafana, Alertmanager, hostnames, raw logs,
or production screenshots.

## Evidence

Machine-readable evidence:

```text
docs/public/evidence/observability-dashboard.sanitized.json
infra/observability/observability-dashboard.sanitized.json
```

API surface:

```text
GET /demo/observability-dashboard
GET /demo/public
```

Verifier:

```bash
bash scripts/check_public_observability_dashboard.sh
```

## Dashboard Groups

| Group | Owner | What It Shows |
| --- | --- | --- |
| API runtime health | Platform operator | Request rate, p95 latency, and error ratio. |
| Integration health | Integration operator | Outbox backlog, retry rate, and dead-lettered jobs. |
| Business workflow health | Operations owner | Workflow action runs, business exceptions, and approval queue. |
| Security and auth health | Security operator | Auth attempts, session revocations, and audit events. |

## Panel Contract

Each panel records:

- stable panel key;
- datasource type: Prometheus-compatible or Loki-compatible;
- public-safe query shape;
- safe labels only;
- linked alert;
- linked public runbook or evidence document.

The public contract includes examples such as:

```text
sum by (route, status) (rate(drivedesk_http_requests_total[5m]))
histogram_quantile(0.95, sum by (le, route) (rate(drivedesk_http_request_duration_seconds_bucket[5m])))
sum by (adapter_key) (drivedesk_outbox_events{status="dead_letter"})
{app="drivedesk"} | json | event_type="adapter.completed"
```

## No raw payloads or PII

## Boundary

This document is dashboard-as-code evidence, not a live telemetry export. Public
evidence is synthetic and sanitized. It must not include:

- raw logs;
- request bodies;
- credentials;
- private hostnames or addresses;
- customer data;
- production screenshots.

## Related Docs

- `docs/public/OBSERVABILITY_PROOF.md`
- `docs/public/ALERT_ROUTING_EVIDENCE.md`
- `docs/public/RUNTIME_ROLLOUT_EVIDENCE.md`
- `docs/public/INTEGRATION_REPAIR.md`
- `docs/public/BUSINESS_CONTROL_TOWER.md`
- `docs/public/AUTH_OBSERVABILITY.md`
- `docs/public/TECHNICAL_CAPABILITY_MAP.md`
- `docs/public/PROJECT_STATUS.md`
