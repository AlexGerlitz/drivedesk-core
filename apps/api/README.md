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

Public demo contract smoke:

```bash
bash scripts/check_public_demo_api.sh
```

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
- `POST /tenants/{tenant_id}/business-records`.
- `GET /tenants/{tenant_id}/business-records`.
- `POST /tenants/{tenant_id}/business-records/{record_id}/transition`.
- `POST /tenants/{tenant_id}/workflow-rules`.
- `GET /tenants/{tenant_id}/workflow-rules`.
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
- matching business record transitions can enqueue the configured workflow
  outbox event, create a tenant-owned task record, or request adapter sync work.
- `/metrics` exposes aggregate counts with `drivedesk_workflow_rules`.

Bearer requests use:

```text
Authorization: Bearer <access-token>
```

Integration endpoints:

- `POST /tenants/{tenant_id}/integration-imports/file` creates a synthetic
  file-import job and stores it as an outbox event with
  `adapter_key=file.import.fake`.

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
