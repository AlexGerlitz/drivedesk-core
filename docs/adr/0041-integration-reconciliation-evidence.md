# ADR-0041: Integration Reconciliation Evidence

Status: accepted

## Context

DriveDesk already has adapter execution through outbox events, retry/dead-letter
handling, operator review, accounting export, and connection diagnostics.

That proves the platform can run integration jobs, but production operations
also need a second question answered:

```text
Did the external provider evidence match the result DriveDesk recorded?
```

Raw provider payloads can contain personal data, document fields, payment
metadata, or credentials. Reconciliation must therefore be useful without
turning into another storage location for sensitive provider responses.

## Decision

Add tenant-owned integration reconciliation records linked to outbox events.

The reconciliation record stores:

- tenant id;
- outbox event id;
- adapter key;
- operation key;
- reconciliation status;
- safe expected evidence from the outbox result;
- safe actual evidence from the provider/operator;
- safe aggregate diff.

Supported statuses:

- `matched`;
- `mismatched`;
- `pending`;
- `blocked`.

The API surface is:

```text
POST /tenants/{tenant_id}/integration-reconciliations
GET  /tenants/{tenant_id}/integration-reconciliations
```

The create payload accepts only safe provider evidence: provider status,
provider reference, record counts, and optional note presence. It does not
accept raw documents, imported rows, provider tokens, provider response bodies,
names, phones, or payment metadata.

Creating a reconciliation writes `integration.reconciliation.recorded` to the
audit log.

Prometheus exposes only aggregate metrics:

```text
drivedesk_integration_reconciliations{adapter_key,status}
```

## Consequences

- Operators can prove that DriveDesk and an external provider agree on an
  integration result.
- Mismatches become visible without opening raw payloads.
- Reconciliation can be shown safely in the public engineering surface.
- Future provider adapters can plug their provider-side checks into the same
  evidence shape.
- Full raw provider responses must stay outside this public-safe reconciliation
  table unless a private data-plane storage policy explicitly allows them.
