# DriveDesk Architecture Diagrams

These diagrams are public-safe and intentionally omit private hostnames,
addresses, credentials, and operational paths.

For the narrative system overview, start with `SYSTEM_DESIGN.md`. This file is
kept as the compact diagram set.

## Modular Monolith

```mermaid
flowchart LR
  Client["Admin / API Client"] --> API["FastAPI API"]
  API --> Core["Core Domain Package"]
  API --> DB["PostgreSQL"]
  API --> Redis["Redis"]
  API --> Outbox["Outbox Events"]
  Worker["Background Worker"] --> Outbox
  Worker --> DB
  Outbox --> Adapters["Integration Adapters"]
  Adapters --> Providers["External Systems"]
```

## Runtime Shape

```mermaid
flowchart TB
  CI["GitHub Actions"] --> Deploy["Deploy Workflow"]
  Deploy --> Runtime["Private Staging Runtime"]
  Runtime --> API["API Container"]
  Runtime --> Worker["Worker Container"]
  Runtime --> DB["PostgreSQL"]
  Runtime --> Redis["Redis"]
  Runtime --> Observability["Observability Stack"]
  Observability --> Prometheus["Prometheus"]
  Observability --> Loki["Loki"]
  Observability --> Alloy["Grafana Alloy"]
  Observability --> Grafana["Grafana"]
  Observability --> Alertmanager["Alertmanager"]
```

## Auth And RBAC

```mermaid
flowchart LR
  Client["API Client"] --> Login["POST /auth/login"]
  Login --> UserHash["Credential Hash"]
  Login --> TokenHash["Access Token Hash"]
  Login --> Attempt["Auth Attempt"]
  Login --> Audit["Auth Audit"]
  Client --> Bearer["Bearer Token Request"]
  Bearer --> Actor["Actor Context"]
  Actor --> Membership["Tenant Membership"]
  Membership --> RBAC["Permission Check"]
  RBAC --> Endpoint["Core Endpoint"]
  Client --> Logout["POST /auth/logout"]
  Logout --> Revoked["Revoked Token"]
  Logout --> Audit
  Actor --> Sessions["GET /auth/sessions"]
  Sessions --> Redacted["Redacted Session State"]
```

## Tenant Isolation

```mermaid
flowchart LR
  Bearer["Bearer Token"] --> Membership["Tenant Memberships"]
  Membership --> Scope["Tenant Scope Helpers"]
  Scope --> Repository["Tenant-Owned Repository Helpers"]
  Repository --> TenantA["Tenant A Allowed"]
  Repository --> TenantB["Tenant B Rejected Without Membership"]
  Bearer --> Bootstrap["Global Bootstrap Endpoint"]
  Bootstrap --> Rejected["Rejected For Bearer Token"]
```

## Observability Flow

```mermaid
flowchart LR
  API["API /metrics"] --> Prometheus["Prometheus"]
  Worker["Worker Logs"] --> DockerLogs["Docker Logs"]
  APILogs["API Logs"] --> DockerLogs
  DockerLogs --> Alloy["Grafana Alloy"]
  Alloy --> Loki["Loki"]
  Prometheus --> Grafana["Grafana Dashboards"]
  Loki --> Grafana
  Prometheus --> AlertRules["Alert Rules"]
  AlertRules --> Alertmanager["Alertmanager"]
```

## Adapter Execution

```mermaid
flowchart LR
  API["POST integration import"] --> Outbox["Outbox Event"]
  Outbox --> Worker["Worker"]
  Worker --> Adapter["file.import.fake"]
  Adapter --> Processed["processed + result_json"]
  Adapter --> Retry["retry + next_retry_at"]
  Adapter --> DeadLetter["dead_letter + last_error"]
```

## CI/CD and Evidence

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant GH as GitHub Actions
  participant Runtime as Private Staging Runtime
  participant Evidence as Evidence Artifact

  Dev->>GH: Push code
  GH->>GH: Run CI smoke checks
  GH->>Runtime: Deploy staging
  Runtime-->>GH: Health, metrics, logs, alerts
  GH->>Runtime: Run health workflow
  GH->>Runtime: Collect evidence workflow
  GH->>Evidence: Upload sanitized-safe JSON artifact
```

## Future Public Demo Boundary

```mermaid
flowchart LR
  Visitor["External Reviewer"] --> PublicDemo["Public Demo UI"]
  PublicDemo --> DemoAPI["Demo API With Synthetic Data"]
  DemoAPI --> DemoDB["Demo Database"]

  PrivateRuntime["Private Engineering Runtime"] --> PrivateObservability["Private Observability"]
  PrivateRuntime -. "sanitized summary only" .-> PublicDocs["Public Docs"]
  PublicDocs --> Visitor
```
