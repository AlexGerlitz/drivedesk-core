from __future__ import annotations

from typing import Any

from drivedesk_core import list_adapter_descriptors


def _public_operation_contracts(descriptor: dict[str, Any]) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for contract in descriptor.get("operation_contracts", []):
        if not isinstance(contract, dict):
            continue
        contracts.append(
            {
                "key": contract.get("key", ""),
                "title": contract.get("title", ""),
                "trigger": contract.get("trigger", ""),
                "eventType": contract.get("event_type", ""),
                "endpoint": contract.get("endpoint", ""),
                "requiredConnectionScope": contract.get("required_connection_scope"),
                "idempotencyKeys": contract.get("idempotency_keys", []),
                "retryable": contract.get("retryable", False),
                "deadLetter": contract.get("dead_letter", False),
                "operatorReview": contract.get("operator_review", False),
            }
        )
    return contracts


def _public_adapter_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for descriptor in list_adapter_descriptors():
        rows.append(
            {
                "key": descriptor["key"],
                "name": descriptor["name"],
                "status": descriptor["status"],
                "direction": descriptor["direction"],
                "connectionProfileSupported": descriptor["connection_profile_supported"],
                "requiredMappingKeys": descriptor["required_mapping_keys"],
                "supportedConnectionScopes": descriptor["supported_connection_scopes"],
                "defaultConnectionScopes": descriptor["default_connection_scopes"],
                "operationContracts": _public_operation_contracts(descriptor),
                "contract": descriptor["purpose"],
            }
        )
    return rows


def build_public_demo_payload() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "generatedAt": "2026-06-17T10:55:00Z",
        "dataSource": "api.synthetic",
        "apiContract": {
            "path": "/demo/public",
            "mode": "read_only",
            "data_profile": "synthetic_fake_data",
            "fallback": "apps/admin/public-demo/demo-data.js",
        },
        "tenant": {
            "name": "DriveDesk Demo Academy",
            "slug": "demo-academy",
            "status": "active",
            "plan": "Core Preview",
        },
        "health": {
            "api": "ready",
            "worker": "processing",
            "database": "online",
            "observability": "validated",
        },
        "metrics": [
            {
                "label": "API checks",
                "value": "47",
                "detail": "private smoke tests",
                "tone": "blue",
            },
            {
                "label": "Public CI",
                "value": "green",
                "detail": "GitHub Actions",
                "tone": "green",
            },
            {
                "label": "OpenAPI paths",
                "value": "24",
                "detail": "generated contract",
                "tone": "violet",
            },
            {
                "label": "Workflow stages",
                "value": "5",
                "detail": "lead to sync",
                "tone": "green",
            },
            {
                "label": "Pending events",
                "value": "1",
                "detail": "retry queue",
                "tone": "amber",
            },
        ],
        "workQueue": [
            {
                "id": "DD-TASK-101",
                "title": "Review new learner intake",
                "owner": "Front desk",
                "status": "in review",
                "priority": "high",
            },
            {
                "id": "DD-TASK-102",
                "title": "Prepare instructor schedule sync",
                "owner": "Ops manager",
                "status": "planned",
                "priority": "medium",
            },
            {
                "id": "DD-TASK-103",
                "title": "Check payment adapter sandbox",
                "owner": "Finance",
                "status": "blocked",
                "priority": "medium",
            },
            {
                "id": "DD-TASK-104",
                "title": "Publish demo evidence package",
                "owner": "Platform",
                "status": "done",
                "priority": "low",
            },
        ],
        "members": [
            {
                "name": "Demo Owner",
                "email": "owner@example.test",
                "role": "owner",
                "status": "active",
            },
            {
                "name": "Ops Manager",
                "email": "ops@example.test",
                "role": "manager",
                "status": "active",
            },
            {
                "name": "Instructor Lead",
                "email": "instructor@example.test",
                "role": "viewer",
                "status": "active",
            },
        ],
        "auditEvents": [
            {
                "time": "08:12",
                "actor": "seed",
                "event": "tenant.created",
                "summary": "Demo tenant initialized",
            },
            {
                "time": "08:13",
                "actor": "owner",
                "event": "membership.created",
                "summary": "Ops manager role assigned",
            },
            {
                "time": "08:14",
                "actor": "worker",
                "event": "outbox.processed",
                "summary": "Public evidence event processed",
            },
            {
                "time": "09:21",
                "actor": "workflow",
                "event": "contract.generated",
                "summary": "Demo learner contract prepared",
            },
            {
                "time": "09:22",
                "actor": "outbox",
                "event": "student.sync.requested",
                "summary": "Student sync event queued",
            },
        ],
        "outbox": [
            {
                "event": "tenant.created",
                "status": "processed",
                "attempts": 1,
            },
            {
                "event": "membership.created",
                "status": "processed",
                "attempts": 1,
            },
            {
                "event": "integration.file_import.requested",
                "status": "processed",
                "attempts": 1,
            },
            {
                "event": "integration.provider.sync",
                "status": "pending",
                "attempts": 0,
            },
            {
                "event": "student.sync.requested",
                "status": "pending",
                "attempts": 0,
            },
        ],
        "adapters": _public_adapter_rows(),
        "integrationJobs": [
            {
                "event": "integration.file_import.requested",
                "adapter": "file.import.fake",
                "status": "processed",
                "attempts": 1,
                "summary": "2 accepted, 1 rejected",
            },
            {
                "event": "integration.file_import.requested",
                "adapter": "file.import.fake",
                "status": "retry",
                "attempts": 1,
                "summary": "temporary provider failure, next retry scheduled",
            },
            {
                "event": "integration.file_import.requested",
                "adapter": "file.import.fake",
                "status": "dead_letter",
                "attempts": 1,
                "summary": "permanent contract failure, operator review required",
            },
        ],
        "integrationHealth": [
            {
                "label": "Processed jobs",
                "value": "1",
                "state": "processed",
                "detail": "file.import.fake",
                "metric": "drivedesk_integration_jobs",
            },
            {
                "label": "Retry queue",
                "value": "1",
                "state": "retry",
                "detail": "temporary provider failure",
                "metric": "drivedesk_integration_job_errors",
            },
            {
                "label": "Dead letters",
                "value": "1",
                "state": "dead_letter",
                "detail": "operator review required",
                "metric": "drivedesk_integration_jobs",
            },
            {
                "label": "Avg duration",
                "value": "12 ms",
                "state": "observed",
                "detail": "last adapter sample",
                "metric": "drivedesk_integration_adapter_duration_milliseconds",
            },
            {
                "label": "Reconciliation",
                "value": "1 match",
                "state": "matched",
                "detail": "provider evidence verified",
                "metric": "drivedesk_integration_reconciliations",
            },
            {
                "label": "Open incidents",
                "value": "2",
                "state": "open",
                "detail": "runbook-backed operator cards",
                "metric": "drivedesk_integration_incidents",
            },
        ],
        "integrationReadiness": [
            {
                "name": "File import adapter",
                "state": "active",
                "progress": 75,
            },
            {
                "name": "Payment sandbox adapter",
                "state": "waiting",
                "progress": 20,
            },
            {
                "name": "Accounting export adapter",
                "state": "active",
                "progress": 55,
            },
            {
                "name": "Connection diagnostics",
                "state": "active",
                "progress": 45,
            },
            {
                "name": "Reconciliation evidence",
                "state": "active",
                "progress": 40,
            },
            {
                "name": "Incident runbooks",
                "state": "active",
                "progress": 35,
            },
            {
                "name": "Public demo runtime",
                "state": "active",
                "progress": 35,
            },
        ],
        "recoveryEvidence": [
            {
                "name": "Synthetic backup",
                "state": "success",
                "detail": "temporary SQLite backup artifact created",
                "evidence": "backup_sha256_recorded",
            },
            {
                "name": "Restore drill",
                "state": "success",
                "detail": "restored into a separate temporary database",
                "evidence": "restore_integrity_ok",
            },
            {
                "name": "Schema contract",
                "state": "success",
                "detail": "core tables and row counts matched after restore",
                "evidence": "counts_match",
            },
            {
                "name": "Data boundary",
                "state": "success",
                "detail": "synthetic fake data only",
                "evidence": "production_data_touched_false",
            },
        ],
        "workflow": {
            "id": "wf-demo-lead-to-student",
            "title": "Lead to enrolled student",
            "owner": "Front desk",
            "currentStage": "student_sync",
            "summary": "Synthetic intake flow that turns a lead into a student record, contract, audit trail, and integration event.",
            "stages": [
                {
                    "key": "lead_created",
                    "label": "Lead captured",
                    "state": "done",
                    "owner": "Website adapter",
                    "evidence": "lead.created",
                },
                {
                    "key": "student_created",
                    "label": "Student record",
                    "state": "done",
                    "owner": "Front desk",
                    "evidence": "student.created",
                },
                {
                    "key": "contract_ready",
                    "label": "Contract prepared",
                    "state": "done",
                    "owner": "Operations",
                    "evidence": "contract.generated",
                },
                {
                    "key": "audit_recorded",
                    "label": "Audit recorded",
                    "state": "done",
                    "owner": "Core API",
                    "evidence": "audit.recorded",
                },
                {
                    "key": "student_sync",
                    "label": "External sync queued",
                    "state": "current",
                    "owner": "Outbox worker",
                    "evidence": "student.sync.requested",
                },
            ],
        },
        "timeline": [
            {
                "time": "09:16",
                "actor": "website.adapter",
                "title": "Lead captured",
                "detail": "Synthetic website form normalized into a DriveDesk lead.",
                "event": "lead.created",
            },
            {
                "time": "09:18",
                "actor": "front_desk",
                "title": "Lead converted",
                "detail": "Front desk accepted the lead and opened a student record.",
                "event": "student.created",
            },
            {
                "time": "09:21",
                "actor": "contract.service",
                "title": "Contract generated",
                "detail": "Contract draft attached to the synthetic student workflow.",
                "event": "contract.generated",
            },
            {
                "time": "09:22",
                "actor": "audit",
                "title": "Audit trail written",
                "detail": "Workflow state change recorded for review.",
                "event": "audit.recorded",
            },
            {
                "time": "09:22",
                "actor": "outbox",
                "title": "Sync queued",
                "detail": "Integration event queued for a future external system adapter.",
                "event": "student.sync.requested",
            },
        ],
        "domainEvents": [
            {
                "event": "lead.created",
                "producer": "website.adapter",
                "consumer": "workflow.engine",
                "status": "processed",
            },
            {
                "event": "student.created",
                "producer": "workflow.engine",
                "consumer": "audit.log",
                "status": "processed",
            },
            {
                "event": "contract.generated",
                "producer": "contract.service",
                "consumer": "document.archive",
                "status": "processed",
            },
            {
                "event": "student.sync.requested",
                "producer": "outbox",
                "consumer": "integration.hub",
                "status": "pending",
            },
        ],
    }
