# ADR-0032: Runtime Adapter Catalog

## Status

Accepted

## Context

DriveDesk now has:

- executable integration adapters;
- tenant-owned integration connection profiles;
- outbox jobs that reference adapter keys.

Without a catalog, admin UI code, generated clients, tests, and future adapter
SDK examples would need to hardcode adapter metadata outside the runtime.

That makes the platform harder to extend because the source of truth for
adapter capabilities is split across docs, UI code, tests, and worker code.

## Decision

Add a runtime adapter catalog.

Each executable adapter owns a public-safe descriptor:

- stable adapter key;
- human-readable name;
- runtime status;
- category and direction;
- purpose;
- connection-profile support flags;
- public-safe payload shape;
- safe config and mapping examples;
- capabilities;
- failure modes.

Expose the descriptor list through:

```text
GET /integration-adapters
```

The endpoint lists executable adapters only. Planned adapters can be described
in product docs or public demo data, but they are not part of the runtime
catalog until the worker can execute them.

## Consequences

- Admin and future frontend code can discover adapter contracts instead of
  hardcoding adapter metadata.
- Public smoke tests can prove that runtime metadata, OpenAPI, and docs stay in
  sync.
- Connection-profile creation can continue validating adapter keys against the
  same runtime adapter registry.
- The catalog must stay public-safe: no tenant data, connection names, real
  provider payloads, or sensitive provider values.
