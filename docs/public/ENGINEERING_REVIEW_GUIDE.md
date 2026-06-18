# Engineering Review Guide

This guide is the short review path for DriveDesk Core. It points to the
running demo, executable checks, API contract, and public-safe evidence that
prove the current engineering surface.

## First Pass

| Step | What to inspect | Proof |
| --- | --- | --- |
| 1 | Live demo Proof tab | `engineeringProof` payload with gates and evidence |
| 2 | Root CI badge | `bash scripts/ci_smoke_public.sh` |
| 3 | Proof contract | `bash scripts/check_public_engineering_proof.sh` |
| 4 | API contract | `docs/openapi.json` and `GET /demo/public` |
| 5 | Capability map | `docs/public/TECHNICAL_CAPABILITY_MAP.md` |
| 6 | Recovery and release safety | backup/restore, rollback, canary, staged promotion checks |
| 7 | Infrastructure story | Helm, GitOps, OpenTofu, drift, and sanitized runtime evidence |

## Review Commands

```bash
bash scripts/ci_smoke_public.sh
bash scripts/check_public_review_guide.sh
bash scripts/check_public_technical_capability_map.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_demo_api.sh
bash scripts/check_public_demo_sdk.sh
bash scripts/check_public_backup_restore.sh
bash scripts/check_public_release_rollback.sh
bash scripts/check_public_slo_canary_gate.sh
bash scripts/check_public_staged_promotion.sh
bash scripts/check_public_gitops_layout.sh
bash scripts/check_public_opentofu_plan.sh
```

## Evidence Map

| Area | Evidence |
| --- | --- |
| System design | `docs/public/SYSTEM_DESIGN.md` |
| Public proof contract | `docs/public/ENGINEERING_PROOF.md` |
| Capability map | `docs/public/TECHNICAL_CAPABILITY_MAP.md` |
| Case study | `docs/public/PORTFOLIO_CASE_STUDY.md` |
| Sanitized runtime evidence | `docs/public/SANITIZED_EVIDENCE.md` |
| Backup and restore | `docs/public/BACKUP_RESTORE_EVIDENCE.md` |
| Release safety | `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`, `docs/public/SLO_CANARY_GATE_EVIDENCE.md`, `docs/public/STAGED_PROMOTION_EVIDENCE.md` |
| GitOps and IaC | `docs/public/GITOPS_DELIVERY.md`, `docs/public/OPENTOFU_PLAN_EVIDENCE.md`, `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md` |
| API and SDK | `docs/public/API_BACKED_DEMO.md`, `docs/public/CLIENT_SDK.md`, `sdk/generated/public-demo/` |

## Boundary

The public repository contains synthetic data and sanitized evidence only. It
does not contain production data, private runtime addresses, operational
credentials, raw logs, or private deployment state.
