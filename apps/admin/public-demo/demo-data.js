window.DRIVEDESK_DEMO_DATA = {
  "schemaVersion": 1,
  "generatedAt": "2026-06-17T08:20:00Z",
  "dataSource": "static.fallback",
  "apiContract": {
    "path": "/demo/public",
    "mode": "read_only",
    "data_profile": "synthetic_fake_data",
    "fallback": "apps/admin/public-demo/demo-data.js"
  },
  "tenant": {
    "name": "DriveDesk Demo Academy",
    "slug": "demo-academy",
    "status": "active",
    "plan": "Core Preview"
  },
  "health": {
    "api": "ready",
    "worker": "processing",
    "database": "online",
    "observability": "validated"
  },
  "metrics": [
    {
      "label": "API checks",
      "value": "47",
      "detail": "private smoke tests",
      "tone": "blue"
    },
    {
      "label": "Public CI",
      "value": "green",
      "detail": "GitHub Actions",
      "tone": "green"
    },
    {
      "label": "OpenAPI paths",
      "value": "24",
      "detail": "generated contract",
      "tone": "violet"
    },
    {
      "label": "Workflow stages",
      "value": "5",
      "detail": "lead to sync",
      "tone": "green"
    },
    {
      "label": "Pending events",
      "value": "1",
      "detail": "retry queue",
      "tone": "amber"
    }
  ],
  "workQueue": [
    {
      "id": "DD-TASK-101",
      "title": "Review new learner intake",
      "owner": "Front desk",
      "status": "in review",
      "priority": "high"
    },
    {
      "id": "DD-TASK-102",
      "title": "Prepare instructor schedule sync",
      "owner": "Ops manager",
      "status": "planned",
      "priority": "medium"
    },
    {
      "id": "DD-TASK-103",
      "title": "Check payment adapter sandbox",
      "owner": "Finance",
      "status": "blocked",
      "priority": "medium"
    },
    {
      "id": "DD-TASK-104",
      "title": "Publish demo evidence package",
      "owner": "Platform",
      "status": "done",
      "priority": "low"
    }
  ],
  "members": [
    {
      "name": "Demo Owner",
      "email": "owner@example.test",
      "role": "owner",
      "status": "active"
    },
    {
      "name": "Ops Manager",
      "email": "ops@example.test",
      "role": "manager",
      "status": "active"
    },
    {
      "name": "Instructor Lead",
      "email": "instructor@example.test",
      "role": "viewer",
      "status": "active"
    }
  ],
  "auditEvents": [
    {
      "time": "08:12",
      "actor": "seed",
      "event": "tenant.created",
      "summary": "Demo tenant initialized"
    },
    {
      "time": "08:13",
      "actor": "owner",
      "event": "membership.created",
      "summary": "Ops manager role assigned"
    },
    {
      "time": "08:14",
      "actor": "worker",
      "event": "outbox.processed",
      "summary": "Public evidence event processed"
    },
    {
      "time": "09:21",
      "actor": "workflow",
      "event": "contract.generated",
      "summary": "Demo learner contract prepared"
    },
    {
      "time": "09:22",
      "actor": "outbox",
      "event": "student.sync.requested",
      "summary": "Student sync event queued"
    }
  ],
  "outbox": [
    {
      "event": "tenant.created",
      "status": "processed",
      "attempts": 1
    },
    {
      "event": "membership.created",
      "status": "processed",
      "attempts": 1
    },
    {
      "event": "integration.file_import.requested",
      "status": "processed",
      "attempts": 1
    },
    {
      "event": "integration.provider.sync",
      "status": "pending",
      "attempts": 0
    },
    {
      "event": "student.sync.requested",
      "status": "pending",
      "attempts": 0
    }
  ],
  "adapters": [
    {
      "key": "file.import.fake",
      "name": "Fake File Import",
      "status": "active",
      "direction": "inbound",
      "connectionProfileSupported": true,
      "requiredMappingKeys": ["external_id", "display_name"],
      "supportedConnectionScopes": ["file_import:execute", "file_import:preview"],
      "defaultConnectionScopes": ["file_import:execute", "file_import:preview"],
      "operationContracts": [
        {
          "key": "file_import_preview",
          "title": "Preview mapped import rows",
          "trigger": "api.request",
          "eventType": "integration.mapping_preview.requested",
          "endpoint": "POST /tenants/{tenant_id}/integration-mapping-preview",
          "requiredConnectionScope": "file_import:preview",
          "idempotencyKeys": ["tenant_id", "integration_connection_id", "records_hash"],
          "retryable": false,
          "deadLetter": false,
          "operatorReview": false
        },
        {
          "key": "file_import_execute",
          "title": "Execute file import job",
          "trigger": "api.outbox.enqueue",
          "eventType": "integration.file_import.requested",
          "endpoint": "POST /tenants/{tenant_id}/integration-imports/file",
          "requiredConnectionScope": "file_import:execute",
          "idempotencyKeys": ["tenant_id", "source_name", "source_format", "records_hash"],
          "retryable": true,
          "deadLetter": true,
          "operatorReview": true
        }
      ],
      "contract": "Normalizes provider rows, previews mapped records, returns accepted and rejected counts, and stores the result on the outbox event."
    },
    {
      "key": "internal.noop",
      "name": "Internal Noop",
      "status": "active",
      "direction": "internal",
      "connectionProfileSupported": false,
      "requiredMappingKeys": [],
      "supportedConnectionScopes": [],
      "defaultConnectionScopes": [],
      "operationContracts": [
        {
          "key": "internal_event_ack",
          "title": "Acknowledge internal outbox event",
          "trigger": "worker.outbox.pending",
          "eventType": "internal.*",
          "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
          "requiredConnectionScope": null,
          "idempotencyKeys": ["outbox_event.id"],
          "retryable": false,
          "deadLetter": false,
          "operatorReview": false
        }
      ],
      "contract": "Acknowledges internal domain events without calling an external provider."
    },
    {
      "key": "accounting.export.mock",
      "name": "Mock Accounting Export",
      "status": "active",
      "direction": "outbound",
      "connectionProfileSupported": true,
      "requiredMappingKeys": [],
      "supportedConnectionScopes": ["accounting:export"],
      "defaultConnectionScopes": ["accounting:export"],
      "operationContracts": [
        {
          "key": "accounting_export_execute",
          "title": "Export accounting documents",
          "trigger": "api.outbox.enqueue",
          "eventType": "accounting.export.requested",
          "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
          "requiredConnectionScope": "accounting:export",
          "idempotencyKeys": ["tenant_id", "export_batch_id", "documents_hash"],
          "retryable": true,
          "deadLetter": true,
          "operatorReview": true
        }
      ],
      "contract": "Exports synthetic accounting document batches through the shared outbox adapter boundary."
    }
  ],
  "integrationJobs": [
    {
      "event": "integration.file_import.requested",
      "adapter": "file.import.fake",
      "status": "processed",
      "attempts": 1,
      "summary": "2 accepted, 1 rejected"
    },
    {
      "event": "integration.file_import.requested",
      "adapter": "file.import.fake",
      "status": "retry",
      "attempts": 1,
      "summary": "temporary provider failure, next retry scheduled"
    },
    {
      "event": "integration.file_import.requested",
      "adapter": "file.import.fake",
      "status": "dead_letter",
      "attempts": 1,
      "summary": "permanent contract failure, operator review required"
    }
  ],
  "integrationHealth": [
    {
      "label": "Processed jobs",
      "value": "1",
      "state": "processed",
      "detail": "file.import.fake",
      "metric": "drivedesk_integration_jobs"
    },
    {
      "label": "Retry queue",
      "value": "1",
      "state": "retry",
      "detail": "temporary provider failure",
      "metric": "drivedesk_integration_job_errors"
    },
    {
      "label": "Dead letters",
      "value": "1",
      "state": "dead_letter",
      "detail": "operator review required",
      "metric": "drivedesk_integration_jobs"
    },
    {
      "label": "Avg duration",
      "value": "12 ms",
      "state": "observed",
      "detail": "last adapter sample",
      "metric": "drivedesk_integration_adapter_duration_milliseconds"
    },
    {
      "label": "Reconciliation",
      "value": "1 match",
      "state": "matched",
      "detail": "provider evidence verified",
      "metric": "drivedesk_integration_reconciliations"
    },
    {
      "label": "Open incidents",
      "value": "2",
      "state": "open",
      "detail": "runbook-backed operator cards",
      "metric": "drivedesk_integration_incidents"
    }
  ],
  "integrationReadiness": [
    {
      "name": "File import adapter",
      "state": "active",
      "progress": 75
    },
    {
      "name": "Payment sandbox adapter",
      "state": "waiting",
      "progress": 20
    },
    {
      "name": "Accounting export adapter",
      "state": "active",
      "progress": 55
    },
    {
      "name": "Connection diagnostics",
      "state": "active",
      "progress": 45
    },
    {
      "name": "Reconciliation evidence",
      "state": "active",
      "progress": 40
    },
    {
      "name": "Incident runbooks",
      "state": "active",
      "progress": 35
    },
    {
      "name": "Public demo runtime",
      "state": "active",
      "progress": 35
    }
  ],
  "recoveryEvidence": [
    {
      "name": "Synthetic backup",
      "state": "success",
      "detail": "temporary SQLite backup artifact created",
      "evidence": "backup_sha256_recorded"
    },
    {
      "name": "Restore drill",
      "state": "success",
      "detail": "restored into a separate temporary database",
      "evidence": "restore_integrity_ok"
    },
    {
      "name": "Schema contract",
      "state": "success",
      "detail": "core tables and row counts matched after restore",
      "evidence": "counts_match"
    },
    {
      "name": "Data boundary",
      "state": "success",
      "detail": "synthetic fake data only",
      "evidence": "production_data_touched_false"
    },
    {
      "name": "Release rollback",
      "state": "success",
      "detail": "bad candidate release rolled back to stable",
      "evidence": "release.rollback.executed"
    },
    {
      "name": "Stable after rollback",
      "state": "success",
      "detail": "stable release healthy after rollback",
      "evidence": "stable_release_healthy_after_rollback"
    },
    {
      "name": "SLO canary gate",
      "state": "success",
      "detail": "candidate release blocked before promotion",
      "evidence": "release.canary_gate.blocked"
    },
    {
      "name": "Promotion blocked",
      "state": "success",
      "detail": "availability, latency, and burn-rate violations detected",
      "evidence": "promotion_blocked"
    },
    {
      "name": "Error budget burn",
      "state": "success",
      "detail": "synthetic candidate exceeded the burn-rate threshold",
      "evidence": "burn_rate_violation_detected"
    },
    {
      "name": "Staged promotion",
      "state": "success",
      "detail": "safe release promoted through build, staging, canary, and production",
      "evidence": "release.staged_promotion.completed"
    },
    {
      "name": "Production approval",
      "state": "success",
      "detail": "synthetic production approval recorded before promotion",
      "evidence": "production_approval_recorded"
    },
    {
      "name": "Promotion history",
      "state": "success",
      "detail": "promotion history hash recorded for auditability",
      "evidence": "promotion_history_hash_recorded"
    },
    {
      "name": "Runtime rollout",
      "state": "success",
      "detail": "private staging rollout passed health and observability gates",
      "evidence": "runtime.rollout.evidence_collected"
    },
    {
      "name": "Loopback boundary",
      "state": "success",
      "detail": "public evidence records no public runtime route",
      "evidence": "loopback_boundary_recorded"
    },
    {
      "name": "Private infra validation",
      "state": "success",
      "detail": "read-only staging/control-plane validation recorded before changes",
      "evidence": "infra.private_state.validated"
    },
    {
      "name": "No runtime mutation",
      "state": "success",
      "detail": "validation evidence records no apply, restart, or runtime mutation",
      "evidence": "no_runtime_mutation_recorded"
    },
    {
      "name": "Infra remediation plan",
      "state": "success",
      "detail": "drift converted into operator-reviewed plan-only actions",
      "evidence": "infra.remediation.plan.ready"
    },
    {
      "name": "Rollback attached",
      "state": "success",
      "detail": "each planned remediation action keeps rollback context",
      "evidence": "rollback_attached"
    },
    {
      "name": "Remediation execution",
      "state": "success",
      "detail": "reviewed private staging execution completed with no production apply",
      "evidence": "infra.remediation.execution.completed"
    },
    {
      "name": "Post-remediation validation",
      "state": "success",
      "detail": "postchecks and sanitized evidence refresh recorded",
      "evidence": "post_remediation_validation_recorded"
    },
    {
      "name": "Drift refresh clean",
      "state": "success",
      "detail": "read-only refresh marks repaired components aligned",
      "evidence": "infra.post_remediation_drift.clean"
    },
    {
      "name": "No residual drift",
      "state": "success",
      "detail": "sanitized refresh records no residual or accepted drift",
      "evidence": "no_residual_drift_recorded"
    },
    {
      "name": "Scheduled validation",
      "state": "success",
      "detail": "daily public-safe validation workflow is recorded",
      "evidence": "infra.scheduled_validation.healthy"
    },
    {
      "name": "Missed-run guard",
      "state": "success",
      "detail": "missed scheduled checks require operator review",
      "evidence": "missed_run_guard_recorded"
    },
    {
      "name": "Scheduled alerting",
      "state": "success",
      "detail": "failed or missed scheduled checks produce runbook-backed alert evidence",
      "evidence": "infra.scheduled_validation.alerting.ready"
    },
    {
      "name": "Failure artifact",
      "state": "success",
      "detail": "workflow failures upload a public-safe alert artifact",
      "evidence": "public-scheduled-validation-alert"
    }
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
        "evidence": "lead.created"
      },
      {
        "key": "student_created",
        "label": "Student record",
        "state": "done",
        "owner": "Front desk",
        "evidence": "student.created"
      },
      {
        "key": "contract_ready",
        "label": "Contract prepared",
        "state": "done",
        "owner": "Operations",
        "evidence": "contract.generated"
      },
      {
        "key": "audit_recorded",
        "label": "Audit recorded",
        "state": "done",
        "owner": "Core API",
        "evidence": "audit.recorded"
      },
      {
        "key": "student_sync",
        "label": "External sync queued",
        "state": "current",
        "owner": "Outbox worker",
        "evidence": "student.sync.requested"
      }
    ]
  },
  "timeline": [
    {
      "time": "09:16",
      "actor": "website.adapter",
      "title": "Lead captured",
      "detail": "Synthetic website form normalized into a DriveDesk lead.",
      "event": "lead.created"
    },
    {
      "time": "09:18",
      "actor": "front_desk",
      "title": "Lead converted",
      "detail": "Front desk accepted the lead and opened a student record.",
      "event": "student.created"
    },
    {
      "time": "09:21",
      "actor": "contract.service",
      "title": "Contract generated",
      "detail": "Contract draft attached to the synthetic student workflow.",
      "event": "contract.generated"
    },
    {
      "time": "09:22",
      "actor": "audit",
      "title": "Audit trail written",
      "detail": "Workflow state change recorded for review.",
      "event": "audit.recorded"
    },
    {
      "time": "09:22",
      "actor": "outbox",
      "title": "Sync queued",
      "detail": "Integration event queued for a future external system adapter.",
      "event": "student.sync.requested"
    }
  ],
  "domainEvents": [
    {
      "event": "lead.created",
      "producer": "website.adapter",
      "consumer": "workflow.engine",
      "status": "processed"
    },
    {
      "event": "student.created",
      "producer": "workflow.engine",
      "consumer": "audit.log",
      "status": "processed"
    },
    {
      "event": "contract.generated",
      "producer": "contract.service",
      "consumer": "document.archive",
      "status": "processed"
    },
    {
      "event": "student.sync.requested",
      "producer": "outbox",
      "consumer": "integration.hub",
      "status": "pending"
    }
  ]
};
