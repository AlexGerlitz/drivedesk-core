# Interview Stack Brief

This brief explains the DriveDesk Core stack in interview-friendly language.
It is intentionally tied to public evidence, verifier commands, and current
limits so a technical reviewer can move from explanation to proof.

## How To Describe The Project

DriveDesk Core is a Business OS foundation: a modular monolith backend with a
public-safe operations demo, Integration Hub contracts, workflow automation,
observability, GitOps/IaC evidence, and a release gate that exports a sanitized
public repository from the private source.

Short version:

```text
I built DriveDesk Core as a business operations platform foundation.
The current public surface proves backend architecture, tenant/RBAC boundaries,
workflow and outbox design, provider-neutral integrations, OpenAPI/SDK drift
checks, observability, release safety, GitOps, OpenTofu, and a public/private
export boundary through executable verifier scripts and GitHub Actions.
```

## Stack Map

| Stack | What It Does | Current State | What Remains |
| --- | --- | --- | --- |
| Python / FastAPI | API layer for business operations, demo contracts, auth, tenants, workflows, and integrations. It is the main backend entrypoint. | Public demo API, OpenAPI schema, tests, and smoke checks are wired. | Real commercial endpoints need provider credentials, production auth policy, and live user workflows. |
| PostgreSQL / Alembic | Stores tenants, users, roles, audit events, outbox jobs, business records, and integration state. Alembic keeps schema changes reproducible. | Migrations and Postgres-shaped repository contracts are present and validated by tests. | Production sizing, backup retention, and migration rollout windows need live environment decisions. |
| Redis / Workers / Outbox | Moves slow or risky work out of request handlers: retries, dead-letter handling, notifications, adapter jobs, and recovery actions. | Outbox/retry/dead-letter contracts are documented and covered by public-safe checks. | Real provider workers need secrets, queues, rate limits, and production runbooks. |
| OpenAPI / SDK | Makes the API contract machine-readable and generates clients for Python, JavaScript, and TypeScript. | OpenAPI drift checks and generated SDK examples are validated. | A stable commercial SDK needs versioning, changelogs, and published packages. |
| Integration Hub / Adapters | Normalizes outside systems such as CRM, bank, accounting, ERP, webhook, file import, email, and custom API providers. | Connector certification, fixture replay, provider onboarding, provider sandbox dry-run planning, fake-transport read-only runner, operator CLI, evidence recorder/verifier, runtime, execution, and repair flows are public-safe and checked. | Real adapters need sandbox credentials, provider-specific auth, private HTTP dry-run evidence, and private rollout evidence. |
| Business Control Tower | Turns provider signals into safe facts, detections, action plans, tasks, approvals, notifications, and repair work. | Demo payload, docs, and checks show end-to-end preview flow. | Needs live frontend operator workflow and real provider data in private environments. |
| Docker / Compose | Reproducible local runtime for app, database-shaped services, and developer verification. | Compose config is checked when Docker is available. | Full local one-command production parity still depends on final service split and runtime secrets. |
| Kubernetes / Helm | Package and run the platform in cluster environments with predictable manifests. | Helm chart and render checks are present. | A live cluster rollout needs real ingress, secrets, autoscaling, storage, and environment policy. |
| GitOps / Argo CD | Keeps environment state controlled from Git: changes are reviewed, applied, drift-checked, and remediated. | GitOps layout, image automation, promotion, drift, and remediation evidence are public-safe. | Real Argo CD deployment needs private cluster access and environment-specific apps. |
| OpenTofu / Terraform | Describes infrastructure as code: networks, servers, registries, state, and environment resources. | Public-safe OpenTofu plan and drift evidence are validated. | Real provider state must stay private and needs remote state, locking, and secret handling. |
| CI/CD / GitHub Actions | Runs tests, smoke checks, release gates, public export validation, scheduled validation, and Pages deployment. | Private and public CI paths validate the public engineering surface. | Commercial release pipelines need environment approvals, deploy keys, rollback policy, and release tagging. |
| Observability / Prometheus / Grafana / Loki | Shows health, errors, latency, queues, logs, alerts, dashboards, and incident evidence. | Metrics, dashboard, alert routing, notification delivery, and incident docs are public-safe and checked. | Live production needs real dashboards, retention, alert channels, and on-call policy. |
| Reliability / Recovery | Covers backup restore, rollback, SLO canary gates, staged promotion, retry, dead-letter, and incident response. | Synthetic recovery and release-safety drills are part of public verification. | Real disaster recovery needs live backups, restore drills, RPO/RTO targets, and provider-specific runbooks. |
| Security / Public-Private Boundary | Keeps secrets, raw logs, production data, provider credentials, and private runtime state out of the public repo. | Export gate, secret checks, sanitized evidence, and public evidence index are wired. | Commercial security needs production secret management, audit review, threat model updates, and access reviews. |
| Public Demo / Pages | Gives a browser-visible entrypoint for inspecting system shape, demo flow, evidence, and verification commands. | GitHub Pages, static demo data, public review bundle, and evidence index are connected. | A live SaaS UI still needs authenticated workflows, real tenant data, and role-specific frontend screens. |

## Interview Talking Points

Use these phrases when explaining decisions:

- Modular monolith first: I kept the system understandable and deployable before
  splitting services. The boundaries are still explicit through modules,
  contracts, outbox jobs, and integration adapters.
- Outbox and workers: user-facing requests stay fast, while provider calls,
  notifications, retries, and repairs are handled asynchronously and audited.
- Integration Hub: external systems are adapters, not the core. DriveDesk owns
  the business workflow, while providers supply or receive data through checked
  contracts.
- Provider sandbox dry-run: before a real CRM connector writes anything, I
  verify secret binding, read-only request shape, fake-transport runner
  behavior, operator CLI output, recorded evidence validation, redaction, rate
  limits, and reconciliation evidence without exposing provider tokens.
- GitOps/IaC: infrastructure and deployment intent are described in Git, then
  verified with render, plan, drift, and release-gate checks.
- Observability: metrics, logs, alerts, dashboards, and runbooks are part of the
  system contract, not an afterthought.
- Public/private split: the public repository proves the engineering surface
  without exposing production data, credentials, private runtime addresses, or
  raw logs.

## What Is Ready Versus Not Ready

Public engineering surface:

- ready to review through GitHub Pages, docs, evidence JSON, OpenAPI, SDK
  examples, and verifier scripts;
- validates backend contracts, Integration Hub, observability, release safety,
  GitOps, OpenTofu, and export safety;
- suitable for technical review because claims point to commands and artifacts.

Commercial SaaS product:

- not yet a finished paid product;
- still needs real authenticated UI flows, production provider adapters,
  billing, customer onboarding, support process, mobile applications, production
  secrets, and live operational runbooks.

## Fast Proof Path

Use this command to validate the public review route:

```bash
bash scripts/run_public_review_bundle.sh
```

Use this command to validate this brief:

```bash
bash scripts/check_public_interview_stack_brief.sh
```

Related evidence:

- `docs/public/TECHNICAL_CAPABILITY_MAP.md`;
- `docs/public/PUBLIC_VERIFICATION_MATRIX.md`;
- `docs/public/EVIDENCE_INDEX.md`;
- `docs/public/evidence/interview-stack-brief.sanitized.json`.

## Boundary

This document uses public-safe architecture descriptions and synthetic evidence
only. It does not include production data, credentials, private runtime
addresses, raw logs, customer records, or private provider state.
