# ADR-0040: Integration Connection Diagnostics

## Status

Accepted

## Context

DriveDesk integration connections can now define adapter keys, config, mapping,
and least-privilege scopes. The Integration Hub can execute inbound imports and
outbound exports through the outbox worker.

Operators still need a safe way to answer whether a connection profile is
usable before business work is queued. That check must not expose provider
credentials, config values, mapping values, tenant payloads, imported records,
or exported documents.

## Decision

Add an integration connection diagnostics surface:

- `POST /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks`;
- `GET /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks`;
- `GET /tenants/{tenant_id}/integration-connections/{connection_id}/health`;
- `dd_integration_connection_checks` storage;
- aggregate Prometheus metrics grouped by adapter key and check status;
- an audit event named `integration_connection.health_checked`.

The diagnostics check validates the connection profile and records only safe
details:

- adapter key;
- connection status;
- config key names;
- mapping key names;
- resolved scopes;
- operation keys;
- executable operation keys;
- missing operation scopes;
- safe failure summary.

## Consequences

- Operators can verify integration readiness before running imports or exports.
- The admin UI can show latest status, last success, last failure, and check
  history.
- Metrics can track diagnostics health without high-cardinality or sensitive
  labels.
- Real provider checks can later reuse the same storage, API, and audit shape.
- The public repository remains safe because no provider secrets or raw payloads
  are exposed.
