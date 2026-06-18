# Reviewer Quickstart

This is the shortest external review path for DriveDesk Core. Use it when you
want to verify the project shape before reading the full documentation set.

For the compact system map, start with `docs/public/SYSTEM_REVIEW_PATH.md`.

## 5-Minute Pass

| Step | Inspect | What it proves |
| --- | --- | --- |
| 1 | `docs/public/SYSTEM_REVIEW_PATH.md` | The compact system path ties the public root, demo, API, SDK, operations evidence, release safety, GitOps, OpenTofu, and evidence index together. |
| 2 | GitHub Pages root review hub | The public entrypoint is published and wired to demo, CI, OpenAPI, docs, and evidence. |
| 3 | Public demo Workflow, Operations, Incidents, and Proof tabs | The demo is not a static screenshot; it exposes an end-to-end workflow-to-proof path, operational contracts, incidents, and proof payloads. |
| 4 | `docs/public/PROJECT_STATUS.md` | Current capability state, limits, and next work are explicit. |
| 5 | `docs/public/TECHNICAL_CAPABILITY_MAP.md` | Each visible capability maps to implementation surface, evidence, and verifier commands. |
| 6 | `docs/public/ENGINEERING_PROOF.md` | The proof tab, API payload, OpenAPI schema, SDK artifacts, and CI gates share one contract. |

Pass criteria: the reviewer can identify the current architecture, public demo,
API contract, SDK surface, observability evidence, incident response evidence,
end-to-end scenario, and release safety gates without private access.

## 15-Minute Verification

Run the fast public checks:

```bash
bash scripts/check_public_pages_entrypoint.sh
bash scripts/check_public_system_review_path.sh
bash scripts/check_public_reviewer_quickstart.sh
bash scripts/check_public_project_status.sh
bash scripts/check_public_technical_capability_map.sh
bash scripts/check_public_evidence_index.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
```

Then inspect:

- `docs/openapi.json`;
- `docs/public/API_BACKED_DEMO.md`;
- `docs/public/CLIENT_SDK.md`;
- `examples/python/demo_adapter_operation_plan.py`;
- `examples/js/demo-adapter-operation-plan.mjs`.

Pass criteria: the API contract, generated SDK, adapter operation plan helpers,
and public proof contract validate from the repository without private
infrastructure.

## 45-Minute Deep Check

Run the full public smoke path:

```bash
bash scripts/ci_smoke_public.sh
```

Then inspect the operational evidence:

- `docs/public/OBSERVABILITY_PROOF.md`;
- `docs/public/ALERT_ROUTING_EVIDENCE.md`;
- `docs/public/INCIDENT_RESPONSE_DEMO.md`;
- `docs/public/SANITIZED_EVIDENCE.md`;
- `docs/public/BACKUP_RESTORE_EVIDENCE.md`;
- `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`;
- `docs/public/SLO_CANARY_GATE_EVIDENCE.md`;
- `docs/public/STAGED_PROMOTION_EVIDENCE.md`;
- `docs/public/GITOPS_DELIVERY.md`;
- `docs/public/OPENTOFU_PLAN_EVIDENCE.md`;
- `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md`.

Pass criteria: the repository proves a coherent engineering chain:

```text
review hub -> demo -> API -> SDK -> workflow -> adapter -> observability -> incident -> release gate -> evidence
```

The fastest demo-specific chain is:

```text
approval -> notification -> adapter -> incident -> recovery -> proof
```

## Boundary

The public review path uses synthetic data and sanitized evidence. It does not
include production data, credentials, private runtime addresses, raw logs,
payment provider details, or private deployment state.

For the longer route, continue with `docs/public/ENGINEERING_REVIEW_GUIDE.md`
and `docs/public/EVIDENCE_INDEX.md`.
