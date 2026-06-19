# DriveDesk Core API

Run locally from the repository root:

```bash
bash scripts/run_public_demo_local.sh
```

Health endpoints:

- `GET /health`;
- `GET /ready`.

Demo endpoints:

- `GET /demo/public` returns a read-only synthetic payload for the public demo
  shell.
- `GET /demo/connector-fixture-replay` returns the same connector replay proof
  as a standalone synthetic contract for SDK and external checks.
- `GET /demo/business-intake-pipeline` returns the same business intake
  pipeline proof as a standalone synthetic contract.
- `GET /demo/business-task-handoff` returns the same business task handoff
  proof as a standalone synthetic contract.
- `GET /demo/business-notification-channels` returns the same notification
  channel matrix proof as a standalone synthetic contract.
- `GET /demo/business-context-assistant` returns the same Business Context
  Assistant proof as a standalone synthetic contract.
- `GET /demo/business-action-execution` returns the same action execution proof
  as a standalone synthetic contract.
- `GET /demo/business-approval-gateway` returns the same approval gateway proof
  as a standalone synthetic contract.
- `GET /demo/integration-runtime` returns the same Integration Runtime proof
  as a standalone synthetic contract.
- `GET /demo/integration-execution` returns the same Integration Execution
  timeline proof as a standalone synthetic contract.
- `GET /demo/business-scenario-replay` returns reusable Business OS scenario
  replay data as a standalone synthetic contract.

Public demo contract smoke:

```bash
bash scripts/check_public_demo_api.sh
```

Public-safe GitOps image automation validation:

```bash
bash scripts/check_public_gitops_image_automation.sh
```

The check validates candidate image digest metadata, SBOM attachment, Trivy
scanner evidence, provenance, target GitOps files, pull-request-only apply mode,
and no direct registry or cluster mutation.

Public-safe OpenTofu plan validation:

```bash
bash scripts/check_public_opentofu_plan.sh
```

Public-safe infrastructure state drift validation:

```bash
bash scripts/check_public_infra_state_drift.sh
```

The check validates desired-vs-observed infrastructure state, drift detection,
state backend boundary, secret boundary, and plan-only remediation behavior.

Public-safe runtime rollout validation:

```bash
bash scripts/check_public_runtime_rollout.sh
```

The check validates private staging rollout stages, runtime health gates,
observability gates, sanitized evidence, loopback-only boundary, and no
production data exposure.

Public-safe private infrastructure validation:

```bash
bash scripts/check_public_private_infra_validation.sh
```

The check validates a read-only private staging/control-plane validation
boundary, OpenTofu/GitOps/runtime rollout references, sanitized evidence, and no
runtime mutation.

Public-safe private infrastructure remediation planning:

```bash
bash scripts/check_public_private_infra_remediation.sh
```

The check validates a plan-only remediation boundary after read-only validation
and drift detection, including operator review, preflight gates, rollback
context, postcheck gates, and no public apply.

Public-safe private infrastructure remediation execution validation:

```bash
bash scripts/check_public_private_infra_remediation_execution.sh
```

The check validates reviewed execution after the remediation plan, preflight
gates, postchecks, rollback context, evidence refresh, no public apply, and no
production apply.

Public-safe post-remediation drift refresh validation:

```bash
bash scripts/check_public_private_infra_post_remediation_drift_refresh.sh
```

The check validates read-only drift refresh after reviewed execution, resolved
components, no residual drift, no accepted drift, no apply, and no runtime
mutation.

Public-safe scheduled validation:

```bash
bash scripts/check_public_private_infra_scheduled_validation.sh
bash scripts/check_public_private_infra_scheduled_alerting.sh
```

The check validates the recurring scheduled validation workflow, daily cron,
manual dispatch fallback, missed-run guard, sample successful runs, secret
boundary recheck, and no runtime mutation.

Public-safe scheduled alerting:

```bash
bash scripts/check_public_private_infra_scheduled_alerting.sh
```

The check validates missed-run, failed-run, and secret-boundary alert signals,
the GitHub Actions failure artifact, runbook keys, notification routes, and no
external notification secrets.

Public-safe 70 percent DevOps/platform milestone:

```bash
bash scripts/check_public_platform_maturity_70.sh
```

The check validates the 70-point milestone, public-safe evidence groups,
engineering surface, gates, remaining product work, and redaction boundary.

Core endpoints:

- `POST /auth/login`;
- `GET /auth/me`;
- `POST /auth/logout`;
- `GET /auth/sessions`;
- `POST /auth/sessions/{session_id}/revoke`;
- `POST /platform/admins`;
- `GET /platform/admins`;
- `POST /tenants`;
- `GET /tenants`;
- `GET /tenants/{tenant_id}`;
- `POST /users`;
- `GET /users`;
- `POST /tenants/{tenant_id}/memberships`;
- `GET /tenants/{tenant_id}/memberships`;
- `GET /tenants/{tenant_id}/audit-events`;
- `GET /tenants/{tenant_id}/outbox-events`.
- `POST /tenants/{tenant_id}/outbox-events/{event_id}/retry`.
- `POST /tenants/{tenant_id}/business-records`.
- `GET /tenants/{tenant_id}/business-records`.
- `POST /tenants/{tenant_id}/business-records/{record_id}/transition`.
- `POST /tenants/{tenant_id}/workflow-rules`.
- `GET /tenants/{tenant_id}/workflow-rules`.
- `GET /tenants/{tenant_id}/workflow-action-runs`.
- `GET /integration-adapters`.
- `GET /integration-runbooks`.
- `POST /tenants/{tenant_id}/integration-connections`.
- `GET /tenants/{tenant_id}/integration-connections`.
- `POST /tenants/{tenant_id}/integration-reconciliations`.
- `GET /tenants/{tenant_id}/integration-reconciliations`.
- `POST /tenants/{tenant_id}/integration-incidents`.
- `GET /tenants/{tenant_id}/integration-incidents`.
- `POST /tenants/{tenant_id}/integration-incidents/{incident_id}/status`.
- `POST /tenants/{tenant_id}/integration-mapping-preview`.
- `POST /tenants/{tenant_id}/integration-imports/file`.
- `GET /demo/public`.

Auth endpoints:

- `POST /auth/login` verifies user credentials and returns a bearer access token.
- `GET /auth/me` returns the current user and active memberships.
- `POST /auth/logout` revokes the current bearer access token.
- `GET /auth/sessions` returns redacted tenant-scoped session state for admins.
- `POST /auth/sessions/{session_id}/revoke` lets admins close visible sessions.
- `POST /platform/admins` grants a dedicated platform-admin role to a user.
- `GET /platform/admins` lists platform-admin grants for platform operators.

The auth layer records failed attempts, activates a login guard after repeated
failures, and writes auth lifecycle events into the platform audit log.

Auth observability:

- `/metrics` exposes aggregate session counts with `drivedesk_auth_sessions`;
- `/metrics` exposes aggregate login-attempt outcomes with
  `drivedesk_auth_attempts_total`;
- `/metrics` keeps returning Prometheus text with
  `drivedesk_metrics_storage_available 0` when storage-backed aggregates are
  temporarily unavailable;
- auth metrics avoid emails, tenant ids, token ids, token hashes, bearer tokens,
  and request bodies.

Tenant isolation:

- bearer tokens resolve through active tenant memberships;
- `GET /tenants` and `GET /users` are filtered to the current user's tenants;
- tenant endpoints reject requests for tenants outside the current user's memberships;
- `POST /tenants` and `POST /users` require bootstrap or platform-admin context.
- tenant-owner bearer tokens are rejected for platform-admin and global
  tenant/user creation endpoints.
- tenant-scoped list queries are centralized in
  `apps/api/drivedesk_api/tenant_scope.py`.
- tenant-owned list queries for models with `tenant_id` use
  `apps/api/drivedesk_api/tenant_repository.py`.

Business record endpoints:

- `POST /tenants/{tenant_id}/business-records` creates a tenant-owned
  `contract`, `payment`, `lesson`, `task`, or `document` record.
- `GET /tenants/{tenant_id}/business-records` lists tenant-owned business records.
- `GET /tenants/{tenant_id}/business-records?record_type=contract` filters by
  record type.
- created records write `business_record.created` audit and outbox events.
- status transitions write `business_record.status_changed` audit and outbox events.
- `/metrics` exposes aggregate counts with `drivedesk_business_records`.

Workflow rule endpoints:

- `POST /tenants/{tenant_id}/workflow-rules` creates a tenant-owned automation rule.
- `GET /tenants/{tenant_id}/workflow-rules` lists tenant-owned automation rules.
- the first trigger is `business_record.status_changed`.
- supported actions are `emit_outbox_event`, `create_task_record`, and
  `request_adapter_sync`.
- matching business record transitions write `workflow.rule.triggered` audit events.
- matching workflow actions write `workflow.action_run.created` audit events.
- matching business record transitions can enqueue the configured workflow
  outbox event, create a tenant-owned task record, or request adapter sync work.
- `/metrics` exposes aggregate counts with `drivedesk_workflow_rules`.
- `/metrics` exposes aggregate action-run counts with
  `drivedesk_workflow_action_runs`.

Bearer requests use:

```text
Authorization: Bearer <access-token>
```

Integration endpoints:

- `GET /integration-adapters` lists executable runtime adapters with
  public-safe contract metadata, payload shape, mapping examples, and
  connection-profile support flags.
- `GET /integration-runbooks` lists public-safe runbook descriptors for retry,
  dead-letter, reconciliation mismatch, blocked, and pending integration
  signals.
- `POST /tenants/{tenant_id}/integration-connections` creates a tenant-owned
  adapter profile with safe config and mapping JSON.
  The API validates adapter support, required mapping keys, non-empty mapping
  values, and supported scopes before storing the profile.
- `GET /tenants/{tenant_id}/integration-connections` lists tenant-owned adapter
  profiles.
- `POST /tenants/{tenant_id}/integration-reconciliations` records safe
  provider evidence for an outbox event and compares it with DriveDesk result
  evidence.
- `GET /tenants/{tenant_id}/integration-reconciliations` lists safe
  reconciliation outcomes filtered by status, adapter key, or outbox event.
- `POST /tenants/{tenant_id}/integration-incidents` creates a tenant-owned
  runbook-backed incident from an outbox or reconciliation signal.
- `GET /tenants/{tenant_id}/integration-incidents` lists incident cards by
  status, severity, adapter, or source type.
- `POST /tenants/{tenant_id}/integration-incidents/{incident_id}/status`
  acknowledges or resolves an integration incident.
- `POST /tenants/{tenant_id}/integration-mapping-preview` previews mapping
  transforms and accepted/rejected rows without creating outbox work.
  Stored connection previews require `file_import:preview`.
- `POST /tenants/{tenant_id}/integration-imports/file` creates a synthetic
  file-import job and stores it as an outbox event with
  `adapter_key=file.import.fake`.
- file-import jobs can reference `integration_connection_id`; the API verifies
  tenant ownership, active status, adapter compatibility, and
  `file_import:execute`.
- file-import worker execution applies connection mapping, for example
  `lead_id -> external_id` and `full_name -> display_name`.
- `/metrics` exposes aggregate connection inventory with
  `drivedesk_integration_connections`.
- `POST /tenants/{tenant_id}/outbox-events/{event_id}/retry` moves reviewed
  `retry` or `dead_letter` events back to `pending` and writes
  `outbox_event.retry_requested` audit events.

Development bootstrap RBAC context can still use request headers:

- `X-Actor-Id`;
- `X-Actor-Role`: `owner`, `admin`, `manager`, or `viewer`.

Requests without an explicit role use `viewer` permissions. This is a
development bootstrap path for permissions and audit behavior. Product-style
API requests should use bearer tokens.

Run migrations against a local database:

```bash
PYTHONPATH=apps/api:packages/core alembic -c apps/api/alembic.ini upgrade head
```
