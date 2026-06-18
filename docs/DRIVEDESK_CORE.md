# DriveDesk Core

DriveDesk Core is the industry-neutral backend foundation.

It should own the parts that every future domain pack needs:

- tenants;
- users;
- roles;
- audit events;
- domain events;
- tasks;
- documents;
- payments;
- notifications;
- integration records;
- analytics events.

The driving-school module is the first domain pack, but Core should stay usable
for future business domains.

## Sprint 0 Foundation

Sprint 0 adds a minimal runnable foundation:

```text
apps/api/drivedesk_api/
  FastAPI app
  /health
  /ready
  SQLAlchemy metadata
  Alembic migration skeleton

apps/worker/drivedesk_worker/
  worker heartbeat

packages/core/drivedesk_core/
  TenantRef
  ActorRef
  DomainEvent
  build_event()
```

## What This Gives Us

- The new product has its own entrypoint instead of growing inside the old bot.
- Core primitives can be tested without Telegram or web templates.
- API and worker can be deployed separately later while still living in one
  modular monolith repository.
- The repository now has a place for platform code, not only legacy code.

## Sprint 1 Foundation

Sprint 1 adds the first real Core workflow:

- tenants;
- users;
- tenant memberships;
- RBAC permission checks;
- audit events;
- outbox events;
- worker-side pending outbox processing.

New tables:

- `dd_users`;
- `dd_memberships`;
- `dd_outbox_events`.

New endpoint groups:

- tenant create/read/list;
- user create/list;
- tenant membership create/list;
- tenant audit read;
- tenant outbox read.

What this gives us:

- DriveDesk now has a multi-tenant identity base.
- Users can belong to organizations with roles.
- Important writes produce audit events.
- Important writes also enqueue outbox events for future integrations,
  notifications, retries, and dead-letter handling.
- The worker has a real job loop target, even though external delivery is not
  implemented yet.

Sprint 1 started with temporary header-based actor context:

- `X-Actor-Id`;
- `X-Actor-Role`.

This proved RBAC behavior before the auth layer existed. The headers still
exist as a development bootstrap path for creating the first tenant, user, and
membership records. Requests without an explicit role use `viewer` permissions.

## Sprint 2 Auth Foundation

Sprint 2 adds the first real Core auth path:

- optional user credential secret on `POST /users`;
- derived credential hash stored on `dd_users`;
- `dd_access_tokens` table for bearer token state;
- `POST /auth/login`;
- `GET /auth/me`;
- `POST /auth/logout`;
- `GET /auth/sessions`;
- `POST /auth/sessions/{session_id}/revoke`;
- `POST /platform/admins`;
- `GET /platform/admins`;
- token-backed actor context for existing RBAC checks;
- tenant-aware permission checks for tenant endpoints.
- tenant isolation for bearer-token tenant and user listing;
- platform-scoped endpoints for global tenant/user creation.
- dedicated platform-admin grants for bearer-token platform operations.
- reusable tenant-scope helpers for Core list queries.
- tenant-owned repository helpers for Core list queries with `tenant_id`.

What this gives us:

- DriveDesk can authenticate a real API user instead of relying only on dev
  headers.
- Access tokens are returned once while only their hashes are stored.
- `/auth/me` proves current-user and membership lookup.
- `/auth/logout` proves token revocation.
- `/auth/sessions` proves redacted tenant-scoped session review for admins.
- `/auth/sessions/{session_id}/revoke` proves admin-triggered visible session revocation.
- `/metrics` exposes aggregate auth session and login-attempt counters without
  leaking emails, token ids, token hashes, or bearer tokens.
- Prometheus staging rules turn auth metric degradation, failed-login spikes,
  and locked attempts into runbook-backed alerts.
- Auth attempts and platform audit events make failed access, guard activation,
  successful login, logout, and admin session revocation reviewable.
- Tenant endpoints can reject a valid token when that user has no membership in
  the requested tenant.
- A tenant owner cannot use a bearer token to create global tenants or global
  users.
- A platform-admin grant lets a bearer-token user create global tenants/users
  without making tenant `owner` a global role.

New table:

- `dd_access_tokens`.
- `dd_auth_attempts`.
- `dd_platform_admins`.
- `dd_business_records`.

New field:

- `dd_users.credential_hash`.

New endpoint group:

- auth login, current-user lookup, logout/token revocation, and redacted session
  listing/revocation.
- platform-admin grant creation and listing.
- tenant-owned business record create/list/filter.

Tenant isolation rules:

- `GET /tenants` is filtered to the bearer user's memberships;
- `GET /users` is filtered to shared-tenant users;
- tenant endpoints require membership in the requested tenant;
- `POST /platform/admins`, `POST /tenants`, and `POST /users` require
  bootstrap or platform-admin context.

Tenant-scope module:

- `apps/api/drivedesk_api/tenant_scope.py`;
- `actor_member_tenant_ids()`;
- `list_tenants_for_actor()`;
- `list_users_for_actor()`.

Tenant-owned repository module:

- `apps/api/drivedesk_api/tenant_repository.py`;
- `tenant_owned_select()`;
- `list_tenant_owned()`.

## Sprint 3 Business Record Foundation

Sprint 3 adds the first product-shaped tenant-owned records without committing
too early to detailed domain schemas.

New table:

- `dd_business_records`.

New endpoint group:

- `POST /tenants/{tenant_id}/business-records`;
- `GET /tenants/{tenant_id}/business-records`;
- `GET /tenants/{tenant_id}/business-records?record_type=contract`.
- `POST /tenants/{tenant_id}/business-records/{record_id}/transition`.

Supported record types:

- `contract`;
- `payment`;
- `lesson`;
- `task`;
- `document`.

What this gives us:

- Future domain packs can start from one proven tenant-owned path.
- Managers can create business records inside their tenant.
- Viewers can read business records but cannot write them.
- Cross-tenant bearer-token access is rejected.
- Each created record writes `business_record.created` audit and outbox events.
- Each status transition writes `business_record.status_changed` audit and
  outbox events.
- `/metrics` exposes aggregate business record counts by `record_type` and
  `status` with `drivedesk_business_records`.
- The business list path exercises the tenant-owned repository helper on real
  product-shaped data.

## Sprint 4 Workflow Rule Foundation

Sprint 4 adds a small automation layer on top of business record lifecycle
events.

New table:

- `dd_workflow_rules`.

New endpoint group:

- `POST /tenants/{tenant_id}/workflow-rules`;
- `GET /tenants/{tenant_id}/workflow-rules`.

First supported trigger:

- `business_record.status_changed`.

First supported actions:

- `emit_outbox_event`.
- `create_task_record`.
- `request_adapter_sync`.

What this gives us:

- DriveDesk can react to a business state change without hardcoding one-off
  side effects into the endpoint.
- A matching transition writes `workflow.rule.triggered` audit events.
- A matching transition enqueues the configured workflow outbox event, such as
  `workflow.contract_approved`.
- A matching transition can create a tenant-owned task record, such as
  `Prepare signature package`.
- A matching transition can request adapter work, such as
  `workflow.contract_sync.requested` for `accounting.fake`.
- Workflow side effects travel through the same retryable outbox path as
  integrations.
- `/metrics` exposes aggregate rule counts with `drivedesk_workflow_rules`.
- Workflow metrics expose only `status`, `trigger_event_type`, and
  `action_type` labels.

## Sprint 4B Workflow Action Run History

Sprint 4B adds execution history for matched workflow actions.

New table:

- `dd_workflow_action_runs`.

New endpoint:

- `GET /tenants/{tenant_id}/workflow-action-runs`.

What this gives us:

- each matched workflow action records `workflow.action_run.created` in audit;
- each action run links the source business record and workflow rule;
- task-creating actions store `task_record_id`;
- outbox-producing actions store `outbox_event_id`;
- `/metrics` exposes aggregate action-run counts with
  `drivedesk_workflow_action_runs`;
- action-run metrics expose only `status` and `action_type` labels.

## Sprint 4C Outbox Recovery

Sprint 4C adds operator recovery for failed outbox and integration jobs.

New endpoint:

- `POST /tenants/{tenant_id}/outbox-events/{event_id}/retry`.

What this gives us:

- reviewed `retry` and `dead_letter` events can move back to `pending`;
- `processed` and already `pending` events are rejected;
- recovery writes `outbox_event.retry_requested` audit events;
- old error, retry time, dead-letter time, result, and duration are cleared
  before the worker sees the event again;
- attempts are preserved unless the request explicitly sets
  `reset_attempts=true`;
- operators no longer need direct database access to retry failed jobs.

## Sprint 4D Integration Connection Profiles

Sprint 4D adds tenant-owned adapter profiles.

New table:

- `dd_integration_connections`.

New endpoints:

- `POST /tenants/{tenant_id}/integration-connections`;
- `GET /tenants/{tenant_id}/integration-connections`.

What this gives us:

- tenants can define adapter connections with safe config and mapping JSON;
- adapter keys are validated against the runtime adapter registry;
- connection creation writes `integration_connection.created` audit events;
- file-import jobs can reference `integration_connection_id`;
- the API verifies tenant ownership, active status, and file-import adapter
  compatibility before creating the job;
- outbox payloads include the selected connection id and mapping;
- `/metrics` exposes aggregate connection inventory with
  `drivedesk_integration_connections`;
- connection metrics expose only `adapter_key` and `status` labels.

## Sprint 4E Runtime Adapter Catalog

Sprint 4E adds a runtime catalog for executable integration adapters.

New API:

- `GET /integration-adapters`.

Why this matters:

- admin UI and generated clients can discover adapter metadata instead of
  hardcoding adapter keys;
- connection-profile screens can show which adapters support tenant-owned
  profiles;
- public smoke tests can verify that runtime adapter contracts, OpenAPI, docs,
  and demo data stay aligned;
- planned adapters stay out of the runtime catalog until the worker can execute
  them.

The current catalog exposes:

| Adapter | Direction | Connection Profile | Purpose |
| --- | --- | --- | --- |
| `file.import.fake` | `inbound` | supported | Synthetic file import contract tests and public demos. |
| `internal.noop` | `internal` | not supported | Default internal outbox acknowledgement path. |

## Sprint 4F Integration Mapping Validation

Sprint 4F validates tenant-owned integration connection mappings against the
runtime adapter catalog.

Why this matters:

- bad connection mappings are rejected before they become outbox work;
- `file.import.fake` requires `external_id` and `display_name` mappings;
- mapping values must be non-empty strings;
- adapters that do not support tenant-owned profiles, such as `internal.noop`,
  are rejected by the connection API;
- file-import job creation re-validates stored mapping before using a
  connection profile.

Public docs:

- `docs/public/INTEGRATION_MAPPING_VALIDATION.md`;
- `docs/adr/0033-integration-mapping-validation.md`.

## Sprint 4G Integration Mapping Transform Preview

Sprint 4G turns stored mapping into runtime behavior.

New API:

- `POST /tenants/{tenant_id}/integration-mapping-preview`.

Why this matters:

- provider-shaped rows such as `lead_id` and `full_name` can be normalized into
  adapter-owned fields such as `external_id` and `display_name`;
- the worker executes file-import jobs against normalized records;
- the preview endpoint lets clients inspect accepted and rejected rows before
  creating outbox work;
- preview is read-only and uses existing tenant read permissions;
- stored connection mappings can be previewed by passing
  `integration_connection_id`.

Public docs:

- `docs/public/INTEGRATION_MAPPING_TRANSFORM.md`;
- `docs/adr/0034-integration-mapping-transform-preview.md`.

## Sprint 4H Integration Connection Scopes

Sprint 4H adds least-privilege scopes for tenant-owned integration profiles.

Migration head:

- `20260618_0012`.

New field:

- `dd_integration_connections.scopes_json`.

Why this matters:

- adapter descriptors declare `supported_connection_scopes` and
  `default_connection_scopes`;
- `file.import.fake` supports `file_import:preview` and
  `file_import:execute`;
- connection creation rejects unsupported scopes;
- preview with a stored connection requires `file_import:preview`;
- file-import job creation with a stored connection requires
  `file_import:execute`;
- connection scope labels are public-safe and do not expose tenant ids,
  provider payloads, credentials, or real connection names.

Public docs:

- `docs/public/INTEGRATION_CONNECTION_SCOPES.md`;
- `docs/adr/0035-integration-connection-scopes.md`.

## Sprint 4I Structured Adapter Operation Contracts

Sprint 4I adds machine-readable operation contracts to runtime adapter
descriptors.

New descriptor field:

- `operation_contracts`.

Why this matters:

- adapter operations are discoverable through `GET /integration-adapters`;
- `file.import.fake` declares separate preview and execute operations;
- each operation exposes endpoint, event type, required scope, idempotency keys,
  retry behavior, dead-letter behavior, and operator-review behavior;
- public demo cards can show operation boundaries without exposing private
  provider configuration;
- future 1C, bank, KKT, webhook, and file adapters can reuse the same contract
  shape.

Public docs:

- `docs/public/INTEGRATION_OPERATION_CONTRACTS.md`;
- `docs/adr/0036-structured-adapter-operation-contracts.md`.

## Sprint 4J Integration Operator Review Queue

Sprint 4J adds a tenant-scoped review queue for failed integration work.

New endpoint:

- `GET /tenants/{tenant_id}/integration-operator-review`.

Why this matters:

- operators can see only `retry` and `dead_letter` integration jobs;
- review cards include adapter key, operation key, event type, status, attempts,
  last error, required scope, redacted payload summary, recommended action, and
  retry endpoint;
- raw records, source names, credentials, config values, mapping values, and
  provider payloads are not returned;
- recovery remains a separate audited action through
  `POST /tenants/{tenant_id}/outbox-events/{event_id}/retry`;
- future 1C, bank, KKT, webhook, and file adapters can reuse the same operator
  review shape.

Public docs:

- `docs/public/INTEGRATION_OPERATOR_REVIEW.md`;
- `docs/adr/0037-integration-operator-review-queue.md`.

## Sprint 4K Business Record Lifecycle Policy Catalog

Sprint 4K adds machine-readable lifecycle policies for business records.

New endpoints:

- `GET /business-record-lifecycle-policies`;
- `POST /tenants/{tenant_id}/business-records/lifecycle-preview`.

Why this matters:

- contracts, payments, lessons, tasks, and documents now have explicit initial
  statuses, known statuses, terminal statuses, and allowed next statuses;
- UI and workflow automation can preview a proposed status transition before
  mutating data;
- lifecycle preview returns `valid`, `reason`, `allowed_next_statuses`, and
  `terminal`;
- the current mutation endpoint remains
  `POST /tenants/{tenant_id}/business-records/{record_id}/transition`;
- future hard enforcement can reuse the same core helper.

Public docs:

- `docs/public/BUSINESS_RECORD_LIFECYCLE.md`;
- `docs/adr/0038-business-record-lifecycle-policy-catalog.md`.

## Sprint 4L Mock Accounting Export Adapter

Sprint 4L adds an executable outbound integration adapter.

New endpoint:

- `POST /tenants/{tenant_id}/integration-exports/accounting`.

Why this matters:

- `accounting.export.mock` proves the outbound side of the Integration Hub;
- accounting export jobs use the same outbox, worker, retry, dead-letter,
  metrics, and operator-review path as inbound file imports;
- tenant-owned connection profiles can scope the adapter with
  `accounting:export`;
- operator review redacts raw `documents` and exposes only safe batch, count,
  and type summaries;
- future 1C, KKT, bank, and ERP adapters can reuse the same shape without
  adding a new service boundary.

Public docs:

- `docs/public/INTEGRATION_ACCOUNTING_EXPORT.md`;
- `docs/adr/0039-mock-accounting-export-adapter.md`.

## Sprint 4M Integration Connection Diagnostics

Sprint 4M adds a safe diagnostics surface for tenant-owned integration
connections.

New endpoints:

- `POST /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks`;
- `GET /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks`;
- `GET /tenants/{tenant_id}/integration-connections/{connection_id}/health`.

Why this matters:

- operators can test a connection profile before scheduling imports or exports;
- diagnostics store latest status, last success, last failure, and check history;
- details expose config key names, mapping key names, scopes, operation keys,
  executable operations, and missing scopes, but not values or raw payloads;
- each run writes `integration_connection.health_checked`;
- Prometheus exposes `drivedesk_integration_connection_checks` and
  `drivedesk_integration_connection_check_duration_milliseconds`;
- real provider checks can reuse the same storage and API later.

Public docs:

- `docs/public/INTEGRATION_CONNECTION_DIAGNOSTICS.md`;
- `docs/adr/0040-integration-connection-diagnostics.md`.

## Sprint 4N Integration Reconciliation Evidence

Sprint 4N adds safe reconciliation records for adapter-backed outbox jobs.

New endpoints:

- `POST /tenants/{tenant_id}/integration-reconciliations`;
- `GET /tenants/{tenant_id}/integration-reconciliations`.

Why this matters:

- operators can compare DriveDesk outbox result evidence with provider-side
  evidence after a job runs;
- processed jobs become `matched` or `mismatched`;
- pending/retry jobs become `pending`;
- dead-letter jobs become `blocked`;
- reconciliation stores only safe provider status, reference, counts, expected
  evidence, and aggregate diff;
- raw documents, imported rows, names, phones, payment metadata, tokens, and
  provider response bodies stay out of reconciliation storage;
- each reconciliation writes `integration.reconciliation.recorded`;
- Prometheus exposes `drivedesk_integration_reconciliations`.

Public docs:

- `docs/public/INTEGRATION_RECONCILIATION.md`;
- `docs/adr/0041-integration-reconciliation-evidence.md`.

## Sprint 4O Integration Incident Runbooks

Sprint 4O adds runbook-backed incident workflow for integration signals.

New endpoints:

- `GET /integration-runbooks`;
- `POST /tenants/{tenant_id}/integration-incidents`;
- `GET /tenants/{tenant_id}/integration-incidents`;
- `POST /tenants/{tenant_id}/integration-incidents/{incident_id}/status`.

Why this matters:

- retry/dead-letter outbox events and reconciliation mismatches can become
  operator-owned incident cards;
- incidents attach a stable runbook key, severity, recommended action, safe
  evidence, and lifecycle status;
- status flow is `open -> acknowledged -> resolved`;
- safe evidence excludes raw documents, imported rows, names, phone numbers,
  provider responses, provider references, batch ids, and secrets;
- creating an incident writes `integration.incident.created`;
- status changes write `integration.incident.status_changed`;
- Prometheus exposes `drivedesk_integration_incidents`;
- future Alertmanager rules can point at the same runbook keys.

Public docs:

- `docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md`;
- `docs/adr/0042-integration-incident-runbooks.md`.

## Local Commands

Run the API without Docker:

```bash
PYTHONPATH=apps/api:apps/worker:packages/core uvicorn drivedesk_api.main:app --reload --port 8080
```

Run the worker:

```bash
PYTHONPATH=apps/api:apps/worker:packages/core python -m drivedesk_worker.main
```

Run the foundation smoke check:

```bash
python scripts/check_drivedesk_foundation.py
```

Run the first migration against a local DriveDesk database:

```bash
PYTHONPATH=apps/api:packages/core alembic -c apps/api/alembic.ini upgrade head
```
