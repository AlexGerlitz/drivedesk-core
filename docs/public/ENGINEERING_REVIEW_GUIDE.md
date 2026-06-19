# Engineering Review Guide

This guide is the short verification path for DriveDesk Core. It points to the
running demo, executable checks, API contract, and public-safe evidence that
prove the current engineering surface.

## First Pass

| Step | What to inspect | Proof |
| --- | --- | --- |
| 1 | System review path | `docs/public/SYSTEM_REVIEW_PATH.md` |
| 2 | Platform Tour | `docs/public/PLATFORM_TOUR.md` |
| 3 | Verification quickstart | `docs/public/REVIEWER_QUICKSTART.md` |
| 4 | Live demo Workflow, Control Tower, Integrations, Operations, Incidents, and Proof tabs | `businessControlTower`, `adapterStudio`, `endToEndScenario`, `alertRouting`, `incidentResponse`, and `engineeringProof` payloads |
| 5 | Root CI badge | `bash scripts/ci_smoke_public.sh` |
| 6 | Project status | `docs/public/PROJECT_STATUS.md` |
| 7 | Proof contract | `bash scripts/check_public_engineering_proof.sh` |
| 8 | API contract | `docs/openapi.json` and `GET /demo/public` |
| 9 | Capability map | `docs/public/TECHNICAL_CAPABILITY_MAP.md` |
| 10 | Evidence index | `docs/public/EVIDENCE_INDEX.md`, `docs/public/evidence/public-evidence-index.sanitized.json` |
| 11 | Observability proof | `docs/public/OBSERVABILITY_PROOF.md` |
| 12 | Observability dashboard | Operations tab and `docs/public/OBSERVABILITY_DASHBOARD.md` |
| 13 | Notification delivery | Operations tab, `GET /demo/notification-delivery`, `notificationDelivery`, and `docs/public/NOTIFICATION_DELIVERY.md` |
| 14 | Alert routing | Operations tab and `docs/public/ALERT_ROUTING_EVIDENCE.md` |
| 15 | Connector fixture replay | `docs/public/CONNECTOR_FIXTURE_REPLAY.md` and `bash scripts/check_public_connector_fixture_replay.sh` |
| 16 | Recovery and release safety | backup/restore, rollback, canary, staged promotion checks |
| 17 | Infrastructure story | Helm, GitOps, OpenTofu, drift, and sanitized runtime evidence |

## Review Commands

```bash
bash scripts/ci_smoke_public.sh
bash scripts/check_public_system_review_path.sh
bash scripts/check_public_platform_tour.sh
bash scripts/check_public_reviewer_quickstart.sh
bash scripts/check_public_review_guide.sh
bash scripts/check_public_project_status.sh
bash scripts/check_public_technical_capability_map.sh
bash scripts/check_public_evidence_index.sh
bash scripts/check_public_observability_proof.sh
bash scripts/check_public_observability_dashboard.sh
bash scripts/check_public_notification_delivery.sh
bash scripts/check_public_alert_routing.sh
bash scripts/check_public_engineering_proof.sh
bash scripts/check_public_connector_fixture_replay.sh
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
| System review path | `docs/public/SYSTEM_REVIEW_PATH.md` |
| Business OS tour | `docs/public/PLATFORM_TOUR.md` |
| Verification quickstart | `docs/public/REVIEWER_QUICKSTART.md` |
| System design | `docs/public/SYSTEM_DESIGN.md` |
| Project status | `docs/public/PROJECT_STATUS.md` |
| Public proof contract | `docs/public/ENGINEERING_PROOF.md` |
| Capability map | `docs/public/TECHNICAL_CAPABILITY_MAP.md` |
| Evidence index | `docs/public/EVIDENCE_INDEX.md`, `docs/public/evidence/public-evidence-index.sanitized.json` |
| Observability proof | `docs/public/OBSERVABILITY_PROOF.md` |
| Observability dashboard | `docs/public/OBSERVABILITY_DASHBOARD.md`, `docs/public/evidence/observability-dashboard.sanitized.json` |
| Notification delivery | `docs/public/NOTIFICATION_DELIVERY.md`, `docs/public/evidence/notification-delivery.sanitized.json`, `GET /demo/notification-delivery`, `notificationDelivery` |
| Alert routing | `docs/public/ALERT_ROUTING_EVIDENCE.md` |
| Incident response | `docs/public/INCIDENT_RESPONSE_DEMO.md` |
| Case study | `docs/public/ENGINEERING_CASE_STUDY.md` |
| Sanitized runtime evidence | `docs/public/SANITIZED_EVIDENCE.md` |
| Backup and restore | `docs/public/BACKUP_RESTORE_EVIDENCE.md` |
| Release safety | `docs/public/RELEASE_ROLLBACK_EVIDENCE.md`, `docs/public/SLO_CANARY_GATE_EVIDENCE.md`, `docs/public/STAGED_PROMOTION_EVIDENCE.md` |
| GitOps and IaC | `docs/public/GITOPS_DELIVERY.md`, `docs/public/OPENTOFU_PLAN_EVIDENCE.md`, `docs/public/INFRA_STATE_DRIFT_EVIDENCE.md` |
| API and SDK | `docs/public/API_BACKED_DEMO.md`, `docs/public/CLIENT_SDK.md`, `sdk/generated/public-demo/` |
| Connector fixture replay | `docs/public/CONNECTOR_FIXTURE_REPLAY.md`, `docs/public/evidence/connector-fixture-replay.sanitized.json`, `examples/connector-fixtures/replay-fixtures.sanitized.json` |

## Boundary

The public repository contains synthetic data and sanitized evidence only. It
does not contain production data, private runtime addresses, operational
credentials, raw logs, or private deployment state.
