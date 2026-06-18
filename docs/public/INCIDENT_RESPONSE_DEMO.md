# Incident Response Demo

DriveDesk exposes a public-safe incident response slice in the demo payload and
the static demo shell. The goal is to show the operational loop after an alert:

```text
alert -> incident -> owner -> runbook -> mitigation -> recovery evidence
```

## Demo Contract

`GET /demo/public` includes `incidentResponse` with:

- summary cards for open, resolved, acknowledgement, and evidence state;
- incident cards with alert name, severity, owner, status, source, mitigation,
  and runbook;
- a response timeline from alert firing to resolution;
- recovery actions for acknowledge, mitigate, verify, and resolve;
- resolution evidence for audit, metrics, runbook, rollback, and postcheck.

The same data is present in `apps/admin/public-demo/demo-data.js`, so the
GitHub Pages demo works without a backend.

## Review Path

1. Open the public demo.
2. Switch to the Incidents tab.
3. Check that open, acknowledged, and resolved incidents are visible.
4. Follow the runbook names to these public docs:
   `INTEGRATION_INCIDENT_RUNBOOKS.md`, `SLO_CANARY_GATE_EVIDENCE.md`, and
   `PRIVATE_INFRA_SCHEDULED_ALERTING.md`.
5. Confirm recovery evidence includes audit, aggregate metrics, rollback, and
   postcheck proof.

## Verification

```bash
bash scripts/check_public_demo_api.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/public_repo_release_gate.sh
```

These checks validate the demo HTML, static data, API payload, OpenAPI required
fields, generated SDK files, and public export gate.

## Boundary

The incident response demo is synthetic and public-safe. It does not expose raw
logs, request bodies, private runtime addresses, credentials, customer data,
production incident payloads, or provider-specific secrets.
