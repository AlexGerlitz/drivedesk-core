# ADR-0042: Integration Incident Runbooks

Status: accepted

## Context

DriveDesk has integration outbox execution, retry/dead-letter handling, operator
review, connection diagnostics, and reconciliation evidence.

Those capabilities expose technical state, but operators need a stable workflow:

```text
signal -> runbook -> acknowledged work -> resolved incident
```

The workflow must not copy raw provider payloads, personal data, or secrets into
incident records.

## Decision

Add a public-safe integration runbook catalog and tenant-owned integration
incident records.

Catalog endpoint:

```text
GET /integration-runbooks
```

Tenant incident endpoints:

```text
POST /tenants/{tenant_id}/integration-incidents
GET  /tenants/{tenant_id}/integration-incidents
POST /tenants/{tenant_id}/integration-incidents/{incident_id}/status
```

Incident sources:

- outbox events in `retry` or `dead_letter`;
- reconciliation records in `mismatched`, `blocked`, or `pending`.

Incident statuses:

- `open`;
- `acknowledged`;
- `resolved`.

Each incident stores:

- source type and source id;
- adapter key and operation key;
- runbook key;
- severity;
- status;
- summary;
- recommended action;
- safe evidence JSON.

The incident record does not store raw documents, raw import rows, provider
response bodies, provider tokens, provider references, batch ids, names, phone
numbers, or payment metadata.

Creating an incident writes:

```text
integration.incident.created
```

Changing status writes:

```text
integration.incident.status_changed
```

Prometheus exposes:

```text
drivedesk_integration_incidents{adapter_key,severity,status}
```

## Consequences

- Integration failure handling becomes a first-class operator workflow.
- Public demos can show incident/runbook maturity without private logs.
- Future Alertmanager rules can point to the same runbook keys and incident
  statuses.
- Incident records are not a replacement for outbox, reconciliation, or audit;
  they are an operator workflow layer above those facts.
