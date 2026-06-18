# Alert Routing Evidence

DriveDesk Core includes a public-safe alert-routing contract for the
observability layer. It shows how alert signals are grouped, routed, deduplicated,
escalated, silenced for maintenance, and tied back to runbooks and evidence.

## Evidence

Machine-readable evidence:

```text
docs/public/evidence/alert-routing.sanitized.json
infra/observability/alert-routing.sanitized.json
```

Verifier:

```bash
bash scripts/check_public_alert_routing.sh
```

The same synthetic routing contract is also visible in the public demo
Operations tab and exposed by the read-only `GET /demo/public` `alertRouting`
payload.

## Route Model

| Route | Signal | Receiver | Escalation |
| --- | --- | --- | --- |
| `platform-critical-page` | `severity=critical` | `public-oncall-page` | ticket queue after 15 minutes |
| `platform-warning-ticket` | `severity=warning` | `public-ticket-queue` | ticket queue after 60 minutes |
| `scheduled-validation-notice` | `service=scheduled-validation` | `public-chat-notice` | ticket queue after 45 minutes |

The public receivers are synthetic placeholders. They prove routing shape
without publishing external destinations, notification tokens, payload bodies,
or private runtime metadata.

## Alert Bindings

The evidence binds operational symptoms to routes:

- `DriveDeskApiTargetDown` -> critical platform page;
- `DriveDeskApiHighLatencyP95` -> warning ticket route;
- `DriveDeskIntegrationDeadLetters` -> integration incident route;
- `DriveDeskAuthFailureSpike` -> critical security route;
- `DriveDeskScheduledValidationMissed` -> scheduled validation notice.

Each binding records severity, service, owner, runbook, dedupe key, and
escalation receiver.

## Runbook Contract

Every routed alert must have:

- alert name;
- severity;
- service;
- owner;
- first action;
- evidence artifact;
- rollback or mitigation path.

The public contract does not require raw logs, request bodies, private runtime
access, or production telemetry exports. It requires sanitized evidence.

## Silence Contract

Planned maintenance silences must include:

- `alertname`;
- `service`;
- `stage`;
- maximum duration of 120 minutes;
- audit event `alert.silence.created`.

This keeps maintenance handling explicit without publishing private comments or
live Alertmanager state.

## Boundary

This is a public-safe routing proof. It does not publish live notification
destinations, private Alertmanager config, raw alert payloads, production logs,
customer data, addresses, or credentials.

## Related Docs

- `docs/public/OBSERVABILITY_PROOF.md`
- `docs/public/RUNTIME_ROLLOUT_EVIDENCE.md`
- `docs/public/SLO_CANARY_GATE_EVIDENCE.md`
- `docs/public/AUTH_OBSERVABILITY.md`
- `docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md`
- `docs/public/PRIVATE_INFRA_SCHEDULED_ALERTING.md`
