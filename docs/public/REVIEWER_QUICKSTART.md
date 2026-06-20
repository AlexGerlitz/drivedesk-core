# Verification Quickstart

This is the shortest external verification path for DriveDesk Core. Use it when you
want to verify the project shape before reading the full documentation set.

For the compact system map, start with `docs/public/SYSTEM_REVIEW_PATH.md`.
For the product route, open `docs/public/PLATFORM_TOUR.md`.
For a one-command check, open `docs/public/PUBLIC_REVIEW_BUNDLE.md` and run:

```bash
bash scripts/run_public_review_bundle.sh
```

## 5-Minute Pass

| Step | Inspect | What it proves |
| --- | --- | --- |
| 1 | `docs/public/PUBLIC_REVIEW_BUNDLE.md` | One-command public review route and machine-readable review evidence. |
| 2 | `docs/public/SYSTEM_REVIEW_PATH.md` | The compact system path ties the public root, demo, API, SDK, operations evidence, release safety, GitOps, OpenTofu, and evidence index together. |
| 3 | `docs/public/PLATFORM_TOUR.md` | Business OS tour through business event -> workflow -> adapter -> incident -> proof. |
| 4 | GitHub Pages engineering reference | The public entrypoint is published and wired to demo, CI, OpenAPI, docs, and evidence. |
| 5 | Public demo Workflow, Control Tower, Integrations, Operations, Incidents, and Proof tabs | The demo is not a static screenshot; it exposes an end-to-end workflow-to-proof path, operational contracts, incidents, and proof payloads. |
| 6 | `docs/public/PROJECT_STATUS.md` | Current capability state, limits, and next work are explicit. |
| 7 | `docs/public/TECHNICAL_CAPABILITY_MAP.md` | Each visible capability maps to implementation surface, evidence, and verifier commands. |
| 8 | `docs/public/PUBLIC_VERIFICATION_MATRIX.md` | Each engineering claim has an artifact, verifier command, and pass signal. |
| 9 | `docs/public/ENGINEERING_PROOF.md` | The proof tab, API payload, OpenAPI schema, SDK artifacts, and CI gates share one contract. |

Pass criteria: a technical reader can identify the current architecture, public demo,
API contract, SDK surface, observability evidence, incident response evidence,
end-to-end scenario, and release safety gates without private access.

## 15-Minute Verification

Run the fast public checks:

```bash
bash scripts/run_public_review_bundle.sh
bash scripts/check_public_review_bundle.sh
bash scripts/check_public_pages_entrypoint.sh
bash scripts/check_public_system_review_path.sh
bash scripts/check_public_platform_tour.sh
bash scripts/check_public_reviewer_quickstart.sh
bash scripts/check_public_verification_matrix.sh
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
engineering reference -> Business OS tour -> demo -> API -> SDK -> workflow -> adapter -> observability -> incident -> release gate -> evidence
```

The fastest demo-specific chain is:

```text
approval -> notification -> adapter -> incident -> recovery -> proof
```

## Boundary

The public verification path uses synthetic data and sanitized evidence. It does not
include production data, credentials, private runtime addresses, raw logs,
payment provider details, or private deployment state.

For the longer route, continue with `docs/public/ENGINEERING_REVIEW_GUIDE.md`
and `docs/public/EVIDENCE_INDEX.md`. Use
`docs/public/PUBLIC_VERIFICATION_MATRIX.md` when you need the shortest
claim-to-evidence checklist.
