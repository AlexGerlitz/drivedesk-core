# DriveDesk Architecture Diagrams

These diagrams are public-safe and intentionally omit private hostnames,
addresses, credentials, and operational paths.

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
  Outbox --> Adapters["Future Integration Adapters"]
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
  PublicDemo --> DemoAPI["Demo API With Fake Data"]
  DemoAPI --> DemoDB["Demo Database"]

  PrivateRuntime["Private Engineering Runtime"] --> PrivateObservability["Private Observability"]
  PrivateRuntime -. "sanitized summary only" .-> PublicDocs["Public Docs"]
  PublicDocs --> Visitor
```
