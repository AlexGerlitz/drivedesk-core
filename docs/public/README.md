# DriveDesk Public Engineering Surface

This folder contains the public-safe engineering surface for DriveDesk. It is
written so an external reviewer can understand the project without access to
private infrastructure, production history, customer data, or operational
credentials.

## Documents

- `PORTFOLIO_CASE_STUDY.md` - engineering case study and current system shape.
- `SYSTEM_DESIGN.md` - public-safe system design overview.
- `API_BACKED_DEMO.md` - read-only synthetic API contract for the public demo.
- `WORKFLOW_DEMO.md` - synthetic business workflow, timeline, events, audit,
  and outbox overview.
- `WORKFLOW_RULES.md` - tenant-owned automation rules, audit, outbox, and metrics.
- `WORKFLOW_ACTION_RUNS.md` - workflow execution history, links, and metrics.
- `AUTH_FOUNDATION.md` - credential auth, bearer token, and RBAC overview.
- `AUTH_OBSERVABILITY.md` - aggregate auth metrics, alert names, and runbook shape.
- `SESSION_REVOCATION.md` - admin-triggered tenant/platform session revocation.
- `PLATFORM_ADMIN.md` - dedicated platform-admin model and SaaS control-plane boundary.
- `TENANT_ISOLATION.md` - tenant-scoped bearer access and cross-tenant boundaries.
- `BUSINESS_RECORDS.md` - tenant-owned business record foundation.
- `BUSINESS_RECORD_LIFECYCLE.md` - lifecycle policies and transition preview.
- `CLIENT_SDK.md` - generated OpenAPI client SDK example.
- `INTEGRATION_ADAPTER_CATALOG.md` - runtime adapter metadata and discovery contract.
- `INTEGRATION_MAPPING_VALIDATION.md` - mapping validation against adapter requirements.
- `INTEGRATION_MAPPING_TRANSFORM.md` - runtime field mapping transform and preview.
- `INTEGRATION_CONNECTION_SCOPES.md` - least-privilege connection scopes.
- `INTEGRATION_OPERATION_CONTRACTS.md` - operation-level adapter contracts.
- `INTEGRATION_ACCOUNTING_EXPORT.md` - executable outbound accounting export adapter.
- `INTEGRATION_CONNECTION_DIAGNOSTICS.md` - safe connection health-checks and metrics.
- `INTEGRATION_RECONCILIATION.md` - safe provider evidence comparison and diff.
- `INTEGRATION_INCIDENT_RUNBOOKS.md` - incident cards and runbook-backed operator flow.
- `INTEGRATION_OPERATOR_REVIEW.md` - safe operator queue for failed integration jobs.
- `INTEGRATION_CONNECTIONS.md` - tenant-owned adapter profiles and mapping.
- `INTEGRATION_ADAPTERS.md` - adapter contract, outbox, retry, and dead-letter overview.
- `INTEGRATION_OBSERVABILITY.md` - adapter metrics, worker logs, and failure visibility overview.
- `OUTBOX_RECOVERY.md` - operator retry path for failed outbox events.
- `BACKUP_RESTORE_EVIDENCE.md` - public-safe synthetic backup and restore drill.
- `RELEASE_ROLLBACK_EVIDENCE.md` - public-safe bad-release rollback drill.
- `SLO_CANARY_GATE_EVIDENCE.md` - public-safe SLO canary promotion gate drill.
- `ARCHITECTURE_DIAGRAMS.md` - public-safe architecture diagrams.
- `PUBLIC_DEMO_PLAN.md` - future live demo plan.
- `ROADMAP.md` - public-safe engineering roadmap.
- `SANITIZED_EVIDENCE.md` - human-readable staging evidence summary.
- `evidence/de-staging-evidence.sanitized.json` - machine-readable sanitized
  evidence snapshot.
- `evidence/backup-restore-drill.sanitized.json` - machine-readable synthetic
  backup/restore evidence snapshot.
- `evidence/release-rollback-drill.sanitized.json` - machine-readable synthetic
  release rollback evidence snapshot.
- `evidence/slo-canary-gate.sanitized.json` - machine-readable synthetic SLO
  canary gate evidence snapshot.
- `assets/drivedesk-core-demo-overview.png` - public demo screenshot.

The public repository export also generates:

- `docs/openapi.json` - FastAPI OpenAPI schema from the exported API.
- `apps/admin/public-demo/index.html` - static fake-data product demo shell.
- `GET /demo/public` - read-only synthetic demo payload in the exported API.
- `GET /business-record-lifecycle-policies` - public-safe lifecycle policy catalog.
- `POST /tenants/{tenant_id}/integration-exports/accounting` - public-safe
  outbound accounting export contract in the exported API.
- `POST /tenants/{tenant_id}/integration-connections/{connection_id}/health-checks` -
  public-safe connection diagnostics contract in the exported API.
- `POST /tenants/{tenant_id}/integration-reconciliations` - public-safe
  provider evidence reconciliation contract in the exported API.
- `POST /tenants/{tenant_id}/integration-incidents` - public-safe incident
  runbook creation contract in the exported API.
- `GET /tenants/{tenant_id}/integration-operator-review` - public-safe
  integration failure review contract in the exported API.
- `workflow`, `timeline`, and `domainEvents` - synthetic workflow contract in
  the public demo payload.
- `scripts/run_public_demo_local.sh` - one-command local API run.
- `scripts/check_public_demo_api.sh` - local API contract and client-example smoke.
- `scripts/check_public_backup_restore.sh` - public-safe synthetic recovery drill.
- `scripts/check_public_release_rollback.sh` - public-safe release rollback drill.
- `scripts/check_public_slo_canary_gate.sh` - public-safe SLO canary gate drill.
- `scripts/generate_public_demo_sdk.py` - generated SDK builder from OpenAPI.
- `scripts/check_public_demo_sdk.sh` - generated SDK drift and runtime smoke.
- `sdk/generated/public-demo/` - generated Python, JavaScript, and TypeScript
  client artifacts.
- `examples/curl/demo-public.sh` - curl client example.
- `examples/python/demo_public_client.py` - Python client example.
- `examples/js/demo-public-fetch.js` - JavaScript fetch client example.
- `PUBLIC_EXPORT_MANIFEST.md` - file list and export boundary summary.

Hosted demo:

```text
https://alexgerlitz.github.io/drivedesk-core/apps/admin/public-demo/
```

## Reviewer Path

1. Open the hosted demo.
2. Review the generated OpenAPI schema.
3. Run `bash scripts/check_public_demo_api.sh`.
4. Run one client example from `examples/`.
5. Read the API-backed demo overview.
6. Read the workflow demo overview.
7. Read the workflow action run overview.
8. Read the auth foundation overview.
9. Read the auth observability overview.
10. Read the session revocation overview.
11. Read the platform-admin overview.
12. Read the tenant isolation overview.
13. Read the business records overview.
14. Read the business record lifecycle overview.
15. Read the generated client SDK overview.
16. Read the system design overview.
17. Read the integration adapter catalog overview.
18. Read the integration mapping validation overview.
19. Read the integration mapping transform overview.
20. Read the integration connection scopes overview.
21. Read the integration operation contracts overview.
22. Read the accounting export adapter overview.
23. Read the integration connection diagnostics overview.
24. Read the integration reconciliation overview.
25. Read the integration incident runbooks overview.
26. Read the integration operator review overview.
27. Read the integration connections overview.
28. Read the integration adapters overview.
29. Read the integration observability overview.
30. Read the outbox recovery overview.
31. Read the backup and restore evidence overview.
32. Read the release rollback evidence overview.
33. Read the SLO canary gate evidence overview.
34. Read the case study.
35. Check CI and public demo health workflow results.
36. Run the public smoke checks locally.

## Human Explanation

The private repository keeps building the real product. This folder is the
clean explanation layer for hiring and public review: what was built, why it was
built that way, what checks exist, and how the architecture can evolve.

The export release gate makes this repeatable. Instead of manually copying
files, the private source builds a fresh public package, validates the schema,
runs public smoke checks, validates the demo shell, and leaves the result ready
for a separate public repository.
