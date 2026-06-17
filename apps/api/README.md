# DriveDesk Core API

Run locally from the repository root:

```bash
PYTHONPATH=apps/api:apps/worker:packages/core uvicorn drivedesk_api.main:app --reload --port 8080
```

Health endpoints:

- `GET /health`;
- `GET /ready`.

Demo endpoints:

- `GET /demo/public` returns a read-only synthetic payload for the public demo
  shell.

Core endpoints:

- `POST /tenants`;
- `GET /tenants`;
- `GET /tenants/{tenant_id}`;
- `POST /users`;
- `GET /users`;
- `POST /tenants/{tenant_id}/memberships`;
- `GET /tenants/{tenant_id}/memberships`;
- `GET /tenants/{tenant_id}/audit-events`;
- `GET /tenants/{tenant_id}/outbox-events`.
- `POST /tenants/{tenant_id}/integration-imports/file`.
- `GET /demo/public`.

Integration endpoints:

- `POST /tenants/{tenant_id}/integration-imports/file` creates a synthetic
  file-import job and stores it as an outbox event with
  `adapter_key=file.import.fake`.

Temporary development RBAC context uses request headers:

- `X-Actor-Id`;
- `X-Actor-Role`: `owner`, `admin`, `manager`, or `viewer`.

Requests without an explicit role use `viewer` permissions. This is a
development foundation for permissions and audit behavior, not the final
authentication system.

Run migrations against a local database:

```bash
PYTHONPATH=apps/api:packages/core alembic -c apps/api/alembic.ini upgrade head
```
