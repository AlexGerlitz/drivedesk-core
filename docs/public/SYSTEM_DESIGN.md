# DriveDesk System Design

This document is the public-safe system design overview for DriveDesk Core. It
describes the engineering shape without exposing private infrastructure,
customer operations, hostnames, addresses, credentials, or runtime paths.

## Design Goal

DriveDesk Core is built as a business operations platform foundation.

The first product direction is operational software for driving-school style
workflows, but the backend foundation is intentionally generic:

- tenants and memberships;
- users and roles;
- credential auth and bearer access tokens;
- audit events;
- outbox events;
- background workers;
- integration adapters;
- observability;
- release gates and evidence.

The system starts as a modular monolith. That keeps development and deployment
simple while still creating boundaries that can become services later if there
is a real operational reason.

## High-Level Architecture

```mermaid
flowchart TB
  Reviewer["External Reviewer"] --> PublicDemo["Public Demo UI"]
  PublicDemo --> StaticData["Synthetic Demo Data"]
  PublicDemo -. "optional API-backed mode" .-> DemoAPI["GET /demo/public"]

  AdminClient["Admin Client"] --> API["FastAPI API"]
  API --> Auth["Auth Layer"]
  Auth --> TokenStore["Access Token Store"]
  API --> DemoAPI
  API --> Domain["Core Domain Modules"]
  API --> Database["PostgreSQL"]
  API --> Cache["Redis"]
  API --> Audit["Audit Log"]
  API --> Outbox["Outbox"]

  Worker["Background Worker"] --> Outbox
  Worker --> Database
  Worker --> AdapterHub["Integration Adapter Hub"]
  AdapterHub --> Providers["External Providers"]

  API --> Metrics["Metrics Endpoint"]
  DemoAPI --> SDK["Generated Client SDK"]
  Worker --> Logs["Structured Logs"]
  Metrics --> Observability["Observability Stack"]
  Logs --> Observability
```

## Runtime Responsibilities

| Layer | Responsibility |
| --- | --- |
| Public demo | Reviewable static UI with synthetic data. |
| Demo API | Read-only synthetic payload for API-backed public demo mode. |
| Generated SDK | Python, JavaScript, and TypeScript client artifacts generated from OpenAPI. |
| API | HTTP contract, validation, auth context, tenant-aware operations, audit writes. |
| Auth layer | Credential verification, bearer token hashing, revocation, login guard, audit, current-user lookup, tenant isolation, and RBAC context. |
| Tenant scope | Reusable query helpers that keep tenant/user list behavior scoped to memberships. |
| Core modules | Domain rules that should not depend on web framework details. |
| Database | Durable business state, migrations, audit and outbox storage. |
| Worker | Async processing, retryable jobs, future adapter execution. |
| Adapter hub | Boundary for external systems such as file imports, webhooks, and provider APIs. |
| Observability | Metrics, logs, alerts, dashboards, and runbook-backed evidence. |
| CI/CD | Repeatable checks before code is treated as deployable. |

## Request And Event Flow

```mermaid
sequenceDiagram
  participant Client as Client
  participant API as FastAPI API
  participant DB as PostgreSQL
  participant Outbox as Outbox
  participant Worker as Worker
  participant Adapter as Adapter

  Client->>API: Create or update business object
  API->>API: Validate request and auth context
  API->>DB: Persist state change
  API->>DB: Write audit event
  API->>Outbox: Record integration event
  API-->>Client: Return API response
  Worker->>Outbox: Fetch pending event
  Worker->>Adapter: Execute retryable integration step
  Adapter-->>Worker: Return success or failure
  Worker->>Outbox: Mark delivered or retryable
```

## Auth Boundary

```mermaid
flowchart LR
  Client["Client"] --> Login["POST /auth/login"]
  Login --> UserHash["Credential Hash"]
  Login --> TokenHash["Access Token Hash"]
  Login --> Attempt["Auth Attempt"]
  Login --> AuthAudit["Auth Audit Event"]
  Client --> Bearer["Authorization: Bearer token"]
  Bearer --> Actor["Actor Context"]
  Actor --> Membership["Tenant Membership Role"]
  Membership --> Permission["Permission Check"]
  Permission --> Endpoint["Core Endpoint"]
  Client --> Logout["POST /auth/logout"]
  Logout --> Revoked["Revoked Token"]
  Logout --> AuthAudit
```

The auth foundation keeps two paths separate:

- development actor headers for bootstrap and local setup;
- bearer-token auth for product-style API requests.

Bearer requests are resolved into the same actor context used by RBAC. For
tenant endpoints, the permission check uses the membership role for the
requested tenant.

Auth lifecycle events are stored as platform audit events. Failed login
attempts are stored separately so repeated failures can activate the login
guard without mixing operational security state into user records.

## Tenant Isolation Boundary

```mermaid
flowchart LR
  Actor["Bearer Actor"] --> Roles["Tenant Membership Roles"]
  Roles --> TenantList["GET /tenants"]
  Roles --> UserList["GET /users"]
  Roles --> TenantEndpoint["Tenant Endpoint"]
  TenantList --> OwnTenants["Only Member Tenants"]
  UserList --> SharedUsers["Only Shared-Tenant Users"]
  TenantEndpoint --> TenantCheck["Requested Tenant Membership"]
  TenantCheck --> Allow["Allow"]
  TenantCheck --> Deny["Deny Cross-Tenant Access"]
  Actor --> Bootstrap["POST /tenants or POST /users"]
  Bootstrap --> DenyBootstrap["Reject Bearer Token"]
```

Tenant roles are not platform roles. A bearer token can operate only through
memberships. Platform bootstrap endpoints remain separate until a dedicated
platform-admin model exists.

Tenant list filtering is centralized in a tenant-scope module. Current handlers
still perform explicit permission checks, then delegate scoped list queries to
that module.

## Adapter Boundary

DriveDesk should not let external systems leak into the core domain directly.
Each external connection should pass through an adapter contract:

```mermaid
flowchart LR
  Core["DriveDesk Core"] --> Event["Domain Event"]
  Event --> Mapper["Mapping Layer"]
  Mapper --> Adapter["Adapter Contract"]
  Adapter --> Transport["HTTP / Webhook / File / Import"]
  Transport --> Provider["External Provider"]
  Provider --> Response["Provider Response"]
  Response --> Normalizer["Normalizer"]
  Normalizer --> Core
```

Adapter rules:

- core objects stay provider-neutral;
- provider payloads are normalized before reaching the domain;
- retries are owned by the worker and outbox layer;
- failed delivery becomes visible operational state;
- sensitive provider details stay out of public docs and public demo data.

The first implemented adapter is documented in `INTEGRATION_ADAPTERS.md`. It
uses synthetic file-import data to prove the API -> outbox -> worker -> adapter
flow, including retry and dead-letter states.

Integration observability is documented in `INTEGRATION_OBSERVABILITY.md`. It
shows how adapter jobs become metrics, structured worker logs, and
runbook-backed operational signals.

## Workflow Boundary

The public demo also exposes a synthetic business workflow:

```text
lead -> student -> contract -> audit -> outbox -> integration sync
```

```mermaid
flowchart LR
  Lead["Lead Captured"] --> Student["Student Record"]
  Student --> Contract["Contract Prepared"]
  Contract --> Audit["Audit Event"]
  Audit --> OutboxEvent["Outbox Event"]
  OutboxEvent --> Integration["Integration Sync"]
```

This workflow is part of the `GET /demo/public` payload. The UI receives
`workflow`, `timeline`, and `domainEvents` fields from the same contract as the
static fallback data.

The separation is intentional:

- workflow stages explain current business state;
- timeline entries explain what a user or reviewer sees;
- domain events explain how platform components communicate;
- audit events explain reviewability;
- outbox events explain async integration handoff.

The public workflow is documented in `WORKFLOW_DEMO.md`.

## CI/CD And Evidence Flow

```mermaid
flowchart LR
  Change["Code Change"] --> CI["CI Smoke Checks"]
  CI --> ExportGate["Public Export Gate"]
  ExportGate --> SDKSmoke["Generated SDK Smoke"]
  CI --> DeployGate["Deployment Gate"]
  DeployGate --> Health["Health Checks"]
  Health --> Evidence["Sanitized Evidence"]
  Evidence --> Docs["Public-Safe Docs"]
```

The important idea is that the project does not treat started containers as
enough evidence. A change is stronger when checks prove API behavior, schema
generation, demo availability, observability configuration, and public export
boundaries. The generated SDK smoke adds another proof point: the exported
OpenAPI schema can produce working public client code.

## Public And Private Boundary

```mermaid
flowchart TB
  PrivateRepo["Private Source Repository"] --> ExportScript["Public Export Script"]
  ExportScript --> ReleaseGate["Public Release Gate"]
  ReleaseGate --> PublicRepo["Public Review Repository"]
  PublicRepo --> Pages["GitHub Pages Demo"]
  Pages --> Reviewer["Reviewer"]

  PrivateRepo -. "not exported" .-> PrivateOps["Private Operations Context"]
  PrivateOps -. "sanitized summaries only" .-> PublicDocs["Public Docs"]
```

Public repository content is meant to show engineering quality:

- source code for the platform foundation;
- OpenAPI schema;
- public demo shell;
- read-only synthetic demo API contract;
- public CI;
- public demo health workflow;
- ADRs and architecture docs;
- sanitized evidence.

Private repository content remains the working product and operations source:

- deployment internals;
- real operational history;
- live environment details;
- customer or tenant-specific context;
- sensitive configuration.

## Scaling Direction

The first scaling step is not microservices. The first scaling step is stronger
boundaries inside the modular monolith:

1. Keep domain logic out of HTTP handlers.
2. Keep provider-specific logic inside adapters.
3. Keep async delivery behind outbox and worker contracts.
4. Keep tenant and role checks explicit.
5. Keep observability and release evidence part of every serious change.

Services can be extracted later when the reason is concrete: independent
scaling, independent release cadence, provider isolation, or operational risk
reduction.

## Human Explanation

This page is the short answer to "how is the system built?" It lets a reviewer
see the shape of the platform before reading code: where requests enter, where
state is stored, how background work runs, where integrations belong, and how
the public demo is separated from private operations.
