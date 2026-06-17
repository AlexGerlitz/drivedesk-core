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

Auth endpoints:

- `POST /auth/login` verifies user credentials and returns a bearer access token.
- `GET /auth/me` returns the current user and active memberships.
- `POST /auth/logout` revokes the current bearer access token.

The auth layer records failed attempts, activates a login guard after repeated
failures, and writes auth lifecycle events into the platform audit log.

Tenant isolation:

- bearer tokens resolve through active tenant memberships;
- `GET /tenants` and `GET /users` are filtered to the current user's tenants;
- tenant endpoints reject requests for tenants outside the current user's memberships;
- `POST /tenants` and `POST /users` are bootstrap-only platform endpoints and
  reject bearer-token requests until a dedicated platform-admin model exists.
- tenant-scoped list queries are centralized in
  `apps/api/drivedesk_api/tenant_scope.py`.

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
