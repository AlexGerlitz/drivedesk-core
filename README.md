# DriveDesk Core

[![CI](https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/ci.yml)

DriveDesk Core is a modular monolith backend foundation for a business
operations platform.

It includes:

- FastAPI API;
- PostgreSQL migrations with Alembic;
- background worker;
- tenant, user, membership, RBAC, audit, and outbox foundation;
- fake file import adapter with retry and dead-letter state;
- Docker Compose local runtime;
- pytest coverage for the Core API;
- architecture docs and ADRs.

[![Public Demo Health](https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/public-demo-health.yml/badge.svg)](https://github.com/AlexGerlitz/drivedesk-core/actions/workflows/public-demo-health.yml)

## Live Demo

[Open the public DriveDesk Core demo](https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/)

![DriveDesk Core demo overview](docs/public/assets/drivedesk-core-demo-overview.png)

## Reviewer Path

1. Open the live demo.
2. Review `docs/openapi.json`.
3. Read `docs/public/API_BACKED_DEMO.md`.
4. Read `docs/public/SYSTEM_DESIGN.md`.
5. Read `docs/public/INTEGRATION_ADAPTERS.md`.
6. Read `docs/public/INTEGRATION_OBSERVABILITY.md`.
7. Read `docs/public/PORTFOLIO_CASE_STUDY.md`.
8. Check `.github/workflows/ci.yml`.
9. Run `bash scripts/ci_smoke_public.sh` locally.

## What To Review First

- `docs/public/PORTFOLIO_CASE_STUDY.md` - engineering case study.
- `docs/public/SYSTEM_DESIGN.md` - system design overview.
- `docs/public/API_BACKED_DEMO.md` - read-only synthetic demo API contract.
- `docs/public/INTEGRATION_ADAPTERS.md` - adapter contract and retry model.
- `docs/public/INTEGRATION_OBSERVABILITY.md` - adapter metrics and worker log signals.
- `docs/public/ARCHITECTURE_DIAGRAMS.md` - architecture diagrams.
- `docs/public/SANITIZED_EVIDENCE.md` - sanitized staging evidence.
- `docs/public/PUBLIC_DEMO_PLAN.md` - future public demo plan.
- `docs/public/ROADMAP.md` - public-safe engineering roadmap.
- `apps/admin/public-demo/index.html` - static fake-data product demo shell.
- `docs/openapi.json` - generated FastAPI OpenAPI schema.
- `GET /demo/public` - read-only synthetic demo payload in the exported API.

## Local Run

```bash
python -m pip install -r requirements.txt
PYTHONPATH=apps/api:apps/worker:packages/core uvicorn drivedesk_api.main:app --reload --port 8080
```

Health:

```bash
curl http://127.0.0.1:8080/health
```

Docker Compose:

```bash
docker compose -f infra/docker/docker-compose.foundation.yml up --build
```

## Checks

```bash
bash scripts/ci_smoke_public.sh
```

## Public Demo Shell

Open the hosted demo:

```text
https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/
```

Or open this file directly in a browser:

```text
apps/admin/public-demo/index.html
```

For local API-backed mode, run the FastAPI app and open:

```text
apps/admin/public-demo/index.html?demoApi=http://localhost:8080/demo/public
```

## Architecture

- `docs/PROJECT_DIRECTION.md`
- `docs/DRIVEDESK_CORE.md`
- `docs/INFRASTRUCTURE_TARGET.md`
- `docs/DEVOPS_ROADMAP.md`
- `docs/public/README.md`
- `docs/public/PORTFOLIO_CASE_STUDY.md`
- `docs/public/SYSTEM_DESIGN.md`
- `docs/public/API_BACKED_DEMO.md`
- `docs/public/INTEGRATION_ADAPTERS.md`
- `docs/public/INTEGRATION_OBSERVABILITY.md`
- `docs/public/ARCHITECTURE_DIAGRAMS.md`
- `docs/public/PUBLIC_DEMO_PLAN.md`
- `docs/public/SANITIZED_EVIDENCE.md`
- `docs/public/ROADMAP.md`
- `docs/openapi.json`
- `docs/adr/0001-modular-monolith-first.md`
- `docs/adr/0006-drivedesk-core-foundation.md`
- `docs/adr/0007-identity-rbac-audit-outbox-foundation.md`
- `docs/adr/0014-integration-adapter-foundation.md`
