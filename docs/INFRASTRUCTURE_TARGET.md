# Infrastructure Target

DriveDesk infrastructure should grow in layers.

Sprint 0 is local and simple:

```text
FastAPI API
Background worker
PostgreSQL
Redis
Docker Compose
CI smoke checks
```

Later layers can add:

- staging with synthetic data;
- container registry;
- Kubernetes;
- Helm;
- Argo CD;
- Terraform/OpenTofu;
- Prometheus, Grafana, Loki, OpenTelemetry;
- backup and restore drills;
- release gates.

## Current Local Foundation

Run from the repository root:

```bash
docker compose -f infra/docker/docker-compose.foundation.yml up --build
```

Services:

- `api`: DriveDesk Core API on `127.0.0.1:8080`;
- `worker`: DriveDesk background worker;
- `postgres`: local DriveDesk PostgreSQL;
- `redis`: local Redis.

Health endpoint:

```bash
curl http://127.0.0.1:8080/health
```

## Verified Outcomes

- Local development no longer depends on the frozen RU server.
- API, worker, PostgreSQL, and Redis can be started together.
- CI can validate the compose file and image build.
- The same shape can later be translated into Helm and Kubernetes.
