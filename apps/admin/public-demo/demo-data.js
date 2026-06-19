window.DRIVEDESK_DEMO_DATA = {
  "adapterScenarios": [
    {
      "adapter": "file.import.fake",
      "detail": "Tenant mapping is validated against sample records before any outbox event is created.",
      "endpoint": "POST /tenants/{tenant_id}/integration-mapping-preview",
      "evidence": "integration.mapping_preview.completed",
      "id": "adapter-file-import-preview",
      "inputs": [
        "connection_profile",
        "mapping",
        "records"
      ],
      "operation": "file_import_preview",
      "outputs": [
        "mapping_preview",
        "validation_errors",
        "no_outbox_event"
      ],
      "phase": "preview",
      "requiredScope": "file_import:preview",
      "status": "processed",
      "title": "File import mapping preview"
    },
    {
      "adapter": "file.import.fake",
      "detail": "Accepted records are queued through the outbox with idempotency keys and an audit event.",
      "endpoint": "POST /tenants/{tenant_id}/integration-imports/file",
      "evidence": "integration.file_import.requested",
      "id": "adapter-file-import-execute",
      "inputs": [
        "source_name",
        "source_format",
        "records_hash"
      ],
      "operation": "file_import_execute",
      "outputs": [
        "outbox_event",
        "adapter_job",
        "audit_event"
      ],
      "phase": "execute",
      "requiredScope": "file_import:execute",
      "status": "processed",
      "title": "File import execution"
    },
    {
      "adapter": "crm.bitrix24.mock",
      "detail": "Bitrix-style CRM deal data is mapped into a safe provider intake preview before DriveDesk records any business state.",
      "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "evidence": "business_provider_intake.previewed",
      "id": "adapter-crm-deal-preview",
      "inputs": [
        "provider_key",
        "subject_ref",
        "payload_hash"
      ],
      "operation": "crm_deal_intake_preview",
      "outputs": [
        "safe_payload",
        "normalized_observation",
        "no_provider_call"
      ],
      "phase": "preview",
      "requiredScope": "crm:deal.preview",
      "status": "mapped",
      "title": "CRM deal intake preview"
    },
    {
      "adapter": "crm.bitrix24.mock",
      "detail": "Accepted CRM facts are queued through the outbox for retryable worker execution.",
      "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
      "evidence": "integration.crm_deal.ingest.requested",
      "id": "adapter-crm-deal-ingest",
      "inputs": [
        "batch_id",
        "deals_hash",
        "idempotency_key"
      ],
      "operation": "crm_deal_ingest_execute",
      "outputs": [
        "outbox_event",
        "adapter_job",
        "redaction_evidence"
      ],
      "phase": "execute",
      "requiredScope": "crm:deal.ingest",
      "status": "pending",
      "title": "CRM deal intake queue"
    },
    {
      "adapter": "accounting.export.mock",
      "detail": "Temporary provider failure keeps the job retryable and visible to operations.",
      "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
      "evidence": "integration.export.retry_scheduled",
      "id": "adapter-accounting-export-retry",
      "inputs": [
        "export_batch_id",
        "documents_hash",
        "idempotency_key"
      ],
      "operation": "accounting_export_execute",
      "outputs": [
        "retry_scheduled",
        "attempt_count",
        "operator_visible_status"
      ],
      "phase": "retry",
      "requiredScope": "accounting:export",
      "status": "retry",
      "title": "Accounting export retry"
    },
    {
      "adapter": "file.import.fake",
      "detail": "Permanent contract failure creates a review card with runbook context and a manual retry endpoint.",
      "endpoint": "GET /tenants/{tenant_id}/integration-operator-review",
      "evidence": "integration.operator_review.created",
      "id": "adapter-dead-letter-review",
      "inputs": [
        "outbox_event",
        "last_error",
        "payload_summary"
      ],
      "operation": "file_import_execute",
      "outputs": [
        "review_card",
        "runbook",
        "manual_retry_endpoint"
      ],
      "phase": "operator_review",
      "requiredScope": "file_import:execute",
      "status": "dead_letter",
      "title": "Dead-letter operator review"
    }
  ],
  "adapterStudio": {
    "boundaries": [
      {
        "detail": "oauth2_or_webhook_boundary keeps token exchange in private connector code.",
        "evidence": "server_secret_store",
        "name": "auth_profile",
        "state": "server_only"
      },
      {
        "detail": "no_browser_token_storage and server_side_provider_calls_only prevent provider tokens from entering the public UI.",
        "evidence": "private_connector_only",
        "name": "browser token boundary",
        "state": "clean"
      },
      {
        "detail": "safe_payload excludes access_token, full_name, phone, raw provider payload, and tenant secrets.",
        "evidence": "redaction_evidence",
        "name": "redaction",
        "state": "clean"
      },
      {
        "detail": "Public demo never calls Bitrix, bank, accounting, Telegram, email, or provider APIs.",
        "evidence": "safeToRunAgainstPublicDemo=false",
        "name": "public run mode",
        "state": "contract_only"
      }
    ],
    "diagnostics": [
      {
        "detail": "Provider readiness without raw payloads",
        "metric": "drivedesk_integration_connection_checks",
        "name": "Connection checks",
        "state": "passed"
      },
      {
        "detail": "Provider evidence comparison",
        "metric": "drivedesk_integration_reconciliations",
        "name": "Reconciliation",
        "state": "matched"
      },
      {
        "detail": "Runbook-backed operator flow",
        "metric": "drivedesk_integration_incidents",
        "name": "Incident cards",
        "state": "open"
      },
      {
        "detail": "Manual review for failed jobs",
        "metric": "integration.operator_review.created",
        "name": "Dead-letter review",
        "state": "ready"
      }
    ],
    "docs": [
      {
        "check": "bash scripts/check_public_adapter_developer_guide.sh",
        "label": "Adapter developer guide",
        "path": "docs/public/ADAPTER_DEVELOPER_GUIDE.md"
      },
      {
        "check": "bash scripts/check_public_demo_sdk.sh",
        "label": "Generated SDK",
        "path": "docs/public/CLIENT_SDK.md"
      },
      {
        "check": "bash scripts/check_public_provider_connector_guide.sh",
        "label": "Provider connector guide",
        "path": "docs/public/PROVIDER_CONNECTOR_GUIDE.md"
      }
    ],
    "flow": [
      {
        "detail": "GET /integration-adapters exposes crm.bitrix24.mock descriptors, auth_profile, scopes, and operation contracts.",
        "evidence": "GET /integration-adapters",
        "name": "Runtime catalog",
        "state": "ready",
        "step": "1"
      },
      {
        "detail": "Generated Python and JavaScript SDK builds adapter-crm-deal-preview and adapter-crm-deal-ingest request plans without live provider writes.",
        "evidence": "sdk/generated/public-demo/",
        "name": "SDK operation plan",
        "state": "contract_only",
        "step": "2"
      },
      {
        "detail": "CRM payload is normalized through business-provider-intake preview; raw payload, phone, full_name, and access_token are dropped.",
        "evidence": "business_provider_intake.previewed",
        "name": "Preview boundary",
        "state": "preview_only",
        "step": "3"
      },
      {
        "detail": "Accepted CRM facts become integration.crm_deal.ingest.requested and are handled by worker:drivedesk_worker.main.process_pending_outbox.",
        "evidence": "integration.crm_deal.ingest.requested",
        "name": "Worker ingest",
        "state": "queued",
        "step": "4"
      },
      {
        "detail": "Connection checks, reconciliations, incident cards, retry, dead-letter, and operator_review make failures recoverable.",
        "evidence": "drivedesk_integration_incidents",
        "name": "Diagnostics and review",
        "state": "observable",
        "step": "5"
      }
    ],
    "operationPlans": [
      {
        "adapter": "crm.bitrix24.mock",
        "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
        "evidence": "business_provider_intake.previewed",
        "executionMode": "contract_only",
        "method": "POST",
        "operation": "crm_deal_intake_preview",
        "requestShape": [
          "dryRun",
          "provider_key",
          "source_type",
          "subject_type",
          "subject_id",
          "external_ref",
          "provider_payload"
        ],
        "safeOutputs": [
          "safe_payload",
          "normalized_observation",
          "no_provider_call"
        ],
        "safeToRunAgainstPublicDemo": false,
        "scenarioId": "adapter-crm-deal-preview",
        "scope": "crm:deal.preview"
      },
      {
        "adapter": "crm.bitrix24.mock",
        "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
        "evidence": "integration.crm_deal.ingest.requested",
        "executionMode": "contract_only",
        "method": "WORKER",
        "operation": "crm_deal_ingest_execute",
        "requestShape": [
          "batch_id",
          "deals_hash",
          "mapping",
          "idempotency_key"
        ],
        "safeOutputs": [
          "outbox_event",
          "adapter_job",
          "redaction_evidence"
        ],
        "safeToRunAgainstPublicDemo": false,
        "scenarioId": "adapter-crm-deal-ingest",
        "scope": "crm:deal.ingest"
      }
    ],
    "summary": [
      {
        "detail": "Contract-only adapter operations",
        "label": "SDK plans",
        "tone": "blue",
        "value": "6"
      },
      {
        "detail": "Redacted Bitrix-style provider intake",
        "label": "CRM preview",
        "tone": "green",
        "value": "safe"
      },
      {
        "detail": "Server-side retry boundary",
        "label": "Worker ingest",
        "tone": "violet",
        "value": "outbox"
      },
      {
        "detail": "No browser token storage",
        "label": "Secrets",
        "tone": "amber",
        "value": "server"
      }
    ]
  },
  "adapters": [
    {
      "authProfile": {
        "credentialPlacement": "server_secret_store",
        "dataBoundaries": [
          "no_public_secrets",
          "server_side_provider_calls_only"
        ],
        "externalTokenExchange": false,
        "mode": "mock_outbound_boundary",
        "publicDemoRequiresSecret": false,
        "realProviderRequiresSecret": true,
        "secretRefs": [
          "ACCOUNTING_PROVIDER_API_KEY",
          "ACCOUNTING_PROVIDER_ENDPOINT"
        ],
        "tokenExchange": "private_connector_only"
      },
      "connectionProfileSupported": true,
      "contract": "Export synthetic accounting documents through the shared outbox adapter boundary.",
      "defaultConnectionScopes": [
        "accounting:export"
      ],
      "direction": "outbound",
      "key": "accounting.export.mock",
      "name": "Mock Accounting Export",
      "operationContracts": [
        {
          "deadLetter": true,
          "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
          "eventType": "accounting.export.requested",
          "idempotencyKeys": [
            "tenant_id",
            "export_batch_id",
            "documents_hash"
          ],
          "key": "accounting_export_execute",
          "operatorReview": true,
          "requiredConnectionScope": "accounting:export",
          "retryable": true,
          "title": "Export accounting documents",
          "trigger": "api.outbox.enqueue"
        }
      ],
      "requiredMappingKeys": [],
      "status": "active",
      "supportedConnectionScopes": [
        "accounting:export"
      ]
    },
    {
      "authProfile": {
        "credentialPlacement": "server_secret_store",
        "dataBoundaries": [
          "no_public_secrets",
          "no_browser_token_storage",
          "server_side_provider_calls_only"
        ],
        "externalTokenExchange": false,
        "mode": "oauth2_or_webhook_boundary",
        "publicDemoRequiresSecret": false,
        "realProviderRequiresSecret": true,
        "secretRefs": [
          "BITRIX24_WEBHOOK_URL",
          "BITRIX24_CLIENT_SECRET"
        ],
        "tokenExchange": "private_connector_only"
      },
      "connectionProfileSupported": true,
      "contract": "Normalize synthetic CRM deal facts into safe DriveDesk observations without calling a real CRM provider.",
      "defaultConnectionScopes": [
        "crm:deal.ingest",
        "crm:deal.preview"
      ],
      "direction": "inbound",
      "key": "crm.bitrix24.mock",
      "name": "Mock Bitrix24 CRM Intake",
      "operationContracts": [
        {
          "deadLetter": false,
          "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
          "eventType": "business_provider_intake.previewed",
          "idempotencyKeys": [
            "tenant_id",
            "provider_key",
            "subject_ref",
            "payload_hash"
          ],
          "key": "crm_deal_intake_preview",
          "operatorReview": false,
          "requiredConnectionScope": "crm:deal.preview",
          "retryable": false,
          "title": "Preview CRM deal intake",
          "trigger": "api.request"
        },
        {
          "deadLetter": true,
          "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
          "eventType": "integration.crm_deal.ingest.requested",
          "idempotencyKeys": [
            "tenant_id",
            "batch_id",
            "deals_hash"
          ],
          "key": "crm_deal_ingest_execute",
          "operatorReview": true,
          "requiredConnectionScope": "crm:deal.ingest",
          "retryable": true,
          "title": "Queue CRM deal intake",
          "trigger": "api.outbox.enqueue"
        }
      ],
      "requiredMappingKeys": [
        "deal_id",
        "source_state"
      ],
      "status": "active",
      "supportedConnectionScopes": [
        "crm:deal.ingest",
        "crm:deal.preview"
      ]
    },
    {
      "authProfile": {
        "credentialPlacement": "none",
        "dataBoundaries": [
          "no_public_secrets",
          "tenant_owned_mapping_only"
        ],
        "externalTokenExchange": false,
        "mode": "local_file_boundary",
        "publicDemoRequiresSecret": false,
        "realProviderRequiresSecret": false,
        "secretRefs": [],
        "tokenExchange": "none"
      },
      "connectionProfileSupported": true,
      "contract": "Normalize synthetic imported rows and report accepted or rejected records.",
      "defaultConnectionScopes": [
        "file_import:execute",
        "file_import:preview"
      ],
      "direction": "inbound",
      "key": "file.import.fake",
      "name": "Synthetic File Import",
      "operationContracts": [
        {
          "deadLetter": false,
          "endpoint": "POST /tenants/{tenant_id}/integration-mapping-preview",
          "eventType": "integration.mapping_preview.requested",
          "idempotencyKeys": [
            "tenant_id",
            "integration_connection_id",
            "records_hash"
          ],
          "key": "file_import_preview",
          "operatorReview": false,
          "requiredConnectionScope": "file_import:preview",
          "retryable": false,
          "title": "Preview mapped import rows",
          "trigger": "api.request"
        },
        {
          "deadLetter": true,
          "endpoint": "POST /tenants/{tenant_id}/integration-imports/file",
          "eventType": "integration.file_import.requested",
          "idempotencyKeys": [
            "tenant_id",
            "source_name",
            "source_format",
            "records_hash"
          ],
          "key": "file_import_execute",
          "operatorReview": true,
          "requiredConnectionScope": "file_import:execute",
          "retryable": true,
          "title": "Execute file import job",
          "trigger": "api.outbox.enqueue"
        }
      ],
      "requiredMappingKeys": [
        "external_id",
        "display_name"
      ],
      "status": "active",
      "supportedConnectionScopes": [
        "file_import:execute",
        "file_import:preview"
      ]
    },
    {
      "authProfile": {
        "credentialPlacement": "none",
        "dataBoundaries": [
          "internal_event_only"
        ],
        "externalTokenExchange": false,
        "mode": "none",
        "publicDemoRequiresSecret": false,
        "realProviderRequiresSecret": false,
        "secretRefs": [],
        "tokenExchange": "none"
      },
      "connectionProfileSupported": false,
      "contract": "Acknowledge internal domain events without calling an external provider.",
      "defaultConnectionScopes": [],
      "direction": "internal",
      "key": "internal.noop",
      "name": "Internal Noop",
      "operationContracts": [
        {
          "deadLetter": false,
          "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
          "eventType": "internal.*",
          "idempotencyKeys": [
            "outbox_event.id"
          ],
          "key": "internal_event_ack",
          "operatorReview": false,
          "requiredConnectionScope": null,
          "retryable": false,
          "title": "Acknowledge internal outbox event",
          "trigger": "worker.outbox.pending"
        }
      ],
      "requiredMappingKeys": [],
      "status": "active",
      "supportedConnectionScopes": []
    }
  ],
  "alertRouting": {
    "bindings": [
      {
        "alert": "DriveDeskApiTargetDown",
        "dedupe": "alertname:service:stage",
        "owner": "platform",
        "route": "platform-critical-page",
        "runbook": "RUNTIME_ROLLOUT_EVIDENCE.md",
        "service": "api",
        "severity": "critical",
        "state": "routed"
      },
      {
        "alert": "DriveDeskApiHighLatencyP95",
        "dedupe": "alertname:service:stage",
        "owner": "platform",
        "route": "platform-warning-ticket",
        "runbook": "SLO_CANARY_GATE_EVIDENCE.md",
        "service": "api",
        "severity": "warning",
        "state": "routed"
      },
      {
        "alert": "DriveDeskIntegrationDeadLetters",
        "dedupe": "alertname:service:stage",
        "owner": "integrations",
        "route": "platform-warning-ticket",
        "runbook": "INTEGRATION_INCIDENT_RUNBOOKS.md",
        "service": "integrations",
        "severity": "warning",
        "state": "routed"
      },
      {
        "alert": "DriveDeskAuthFailureSpike",
        "dedupe": "alertname:service:stage",
        "owner": "security",
        "route": "platform-critical-page",
        "runbook": "AUTH_OBSERVABILITY.md",
        "service": "auth",
        "severity": "critical",
        "state": "routed"
      },
      {
        "alert": "DriveDeskScheduledValidationMissed",
        "dedupe": "alertname:service",
        "owner": "platform",
        "route": "scheduled-validation-notice",
        "runbook": "PRIVATE_INFRA_SCHEDULED_ALERTING.md",
        "service": "scheduled-validation",
        "severity": "warning",
        "state": "routed"
      }
    ],
    "routes": [
      {
        "artifact": "public-alert-routing-artifact",
        "escalation": "15m",
        "match": "severity=critical",
        "name": "platform-critical-page",
        "receiver": "public-oncall-page",
        "repeat": "30m",
        "state": "active"
      },
      {
        "artifact": "public-alert-routing-artifact",
        "escalation": "60m",
        "match": "severity=warning",
        "name": "platform-warning-ticket",
        "receiver": "public-ticket-queue",
        "repeat": "240m",
        "state": "active"
      },
      {
        "artifact": "public-scheduled-validation-alert",
        "escalation": "45m",
        "match": "service=scheduled-validation",
        "name": "scheduled-validation-notice",
        "receiver": "public-chat-notice",
        "repeat": "180m",
        "state": "active"
      }
    ],
    "runbookActions": [
      {
        "detail": "Open the public runbook and inspect the sanitized evidence artifact.",
        "evidence": "ALERT_ROUTING_EVIDENCE.md",
        "name": "First response",
        "state": "ready"
      },
      {
        "detail": "Critical alerts escalate to the ticket queue after 15 minutes.",
        "evidence": "public-ticket-queue",
        "name": "Escalation path",
        "state": "ready"
      },
      {
        "detail": "Maintenance silences require alertname, service, stage, and an expiry.",
        "evidence": "alert.silence.created",
        "name": "Silence contract",
        "state": "ready"
      }
    ],
    "summary": [
      {
        "detail": "critical, warning, scheduled validation",
        "label": "Routes",
        "tone": "blue",
        "value": "3"
      },
      {
        "detail": "page, chat, ticket queue",
        "label": "Receivers",
        "tone": "green",
        "value": "3"
      },
      {
        "detail": "runbook-backed signals",
        "label": "Bound alerts",
        "tone": "violet",
        "value": "5"
      },
      {
        "detail": "critical route to ticket queue",
        "label": "Escalation",
        "tone": "amber",
        "value": "15m"
      }
    ]
  },
  "apiContract": {
    "data_profile": "synthetic_demo_data",
    "fallback": "apps/admin/public-demo/demo-data.js",
    "mode": "read_only",
    "path": "/demo/public"
  },
  "auditEvents": [
    {
      "actor": "seed",
      "event": "tenant.created",
      "summary": "Demo tenant initialized",
      "time": "08:12"
    },
    {
      "actor": "owner",
      "event": "membership.created",
      "summary": "Ops manager role assigned",
      "time": "08:13"
    },
    {
      "actor": "worker",
      "event": "outbox.processed",
      "summary": "Public evidence event processed",
      "time": "08:14"
    },
    {
      "actor": "workflow",
      "event": "contract.generated",
      "summary": "Demo learner contract prepared",
      "time": "09:21"
    },
    {
      "actor": "outbox",
      "event": "student.sync.requested",
      "summary": "Student sync event queued",
      "time": "09:22"
    }
  ],
  "businessActionExecution": {
    "api": {
      "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
      "preview": "POST /tenants/{tenant_id}/business-action-executions/preview",
      "repairExecute": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
      "standalone": "GET /demo/business-action-execution",
      "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview"
    },
    "approvalGates": [
      {
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "gate": "operator_review_gate",
        "requiresApproval": true,
        "status": "required"
      },
      {
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "gate": "external_write_gate",
        "requiresApproval": true,
        "status": "closed"
      },
      {
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "gate": "idempotent_outbox_gate",
        "requiresApproval": false,
        "status": "ready"
      }
    ],
    "command": "POST /tenants/{tenant_id}/business-action-executions/preview",
    "dataBoundaries": [
      {
        "externalMutation": false,
        "name": "dry_run_only",
        "status": "preview_only"
      },
      {
        "externalMutation": false,
        "name": "no_provider_write",
        "status": "closed"
      },
      {
        "containsPii": false,
        "name": "safe_execution_payload",
        "rawPayloadIncluded": false,
        "status": "clean"
      },
      {
        "externalMutation": false,
        "name": "audit_and_outbox_contract",
        "status": "documented"
      }
    ],
    "docs": [
      {
        "label": "Business Action Execution",
        "path": "docs/public/BUSINESS_ACTION_EXECUTION.md"
      },
      {
        "label": "Business Task Handoff",
        "path": "docs/public/BUSINESS_TASK_HANDOFF.md"
      },
      {
        "label": "Business Context Assistant",
        "path": "docs/public/BUSINESS_CONTEXT_ASSISTANT.md"
      }
    ],
    "dryRunResults": [
      {
        "action": "open_reconciliation_plan",
        "adapterKey": "internal.noop",
        "containsPii": false,
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "rawPayloadIncluded": false,
        "resultKey": "dry_run.001",
        "status": "would_enqueue",
        "wouldEnqueueEvent": "business.action.review_requested",
        "wouldRecord": "WorkflowActionRun"
      },
      {
        "action": "queue_accounting_export_after_review",
        "adapterKey": "accounting.export.mock",
        "containsPii": false,
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "rawPayloadIncluded": false,
        "resultKey": "dry_run.002",
        "status": "would_enqueue",
        "wouldEnqueueEvent": "accounting.export.requested",
        "wouldRecord": "WorkflowActionRun"
      },
      {
        "action": "prepare_internal_notification",
        "adapterKey": "internal.notification",
        "containsPii": false,
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "rawPayloadIncluded": false,
        "resultKey": "dry_run.003",
        "status": "would_enqueue",
        "wouldEnqueueEvent": "notification.delivery.requested",
        "wouldRecord": "WorkflowActionRun"
      }
    ],
    "executionPlan": [
      {
        "action": "open_reconciliation_plan",
        "adapterKey": "internal.noop",
        "commitWouldMutateProvider": false,
        "containsPii": false,
        "dryRun": true,
        "evidence": "business_action_execution.previewed",
        "executionKey": "execution.preview.001",
        "externalMutation": false,
        "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:open_reconciliation_plan:001",
        "mode": "dry_run",
        "rawPayloadIncluded": false,
        "requiresApproval": false,
        "safePayloadProfile": "role_subject_action_reference",
        "safeToAutoRun": true,
        "status": "dry_run_ready",
        "wouldEnqueueEvent": "business.action.review_requested"
      },
      {
        "action": "queue_accounting_export_after_review",
        "adapterKey": "accounting.export.mock",
        "commitWouldMutateProvider": true,
        "containsPii": false,
        "dryRun": true,
        "evidence": "business_action_execution.previewed",
        "executionKey": "execution.preview.002",
        "externalMutation": false,
        "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:queue_accounting_export_after_review:002",
        "mode": "dry_run",
        "rawPayloadIncluded": false,
        "requiresApproval": true,
        "safePayloadProfile": "role_subject_action_reference",
        "safeToAutoRun": false,
        "status": "approval_required",
        "wouldEnqueueEvent": "accounting.export.requested"
      },
      {
        "action": "prepare_internal_notification",
        "adapterKey": "internal.notification",
        "commitWouldMutateProvider": false,
        "containsPii": false,
        "dryRun": true,
        "evidence": "business_action_execution.previewed",
        "executionKey": "execution.preview.003",
        "externalMutation": false,
        "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:prepare_internal_notification:003",
        "mode": "dry_run",
        "rawPayloadIncluded": false,
        "requiresApproval": false,
        "safePayloadProfile": "role_subject_action_reference",
        "safeToAutoRun": true,
        "status": "dry_run_ready",
        "wouldEnqueueEvent": "notification.delivery.requested"
      }
    ],
    "preflightChecks": [
      {
        "check": "safe_payload_profile",
        "detail": "Only role, subject key, action key, and evidence references are included.",
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "status": "passed"
      },
      {
        "check": "idempotency_key_ready",
        "detail": "Every execution candidate has a deterministic idempotency key.",
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "status": "passed"
      },
      {
        "check": "approval_gate_attached",
        "detail": "Provider-changing commits stay behind operator approval.",
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "status": "required"
      },
      {
        "browserTokenStorage": false,
        "check": "connector_secret_boundary",
        "detail": "Preview does not require credentials or browser token storage.",
        "evidence": "business_action_execution.previewed",
        "externalMutation": false,
        "requiresSecret": false,
        "status": "clean"
      }
    ],
    "role": "accountant",
    "rollbackPlan": [
      {
        "detail": "Dry-run preview writes nothing and has no external state to roll back.",
        "externalMutation": false,
        "status": "not_needed",
        "step": "preview_has_no_rollback"
      },
      {
        "detail": "Future commit execution uses outbox retry, dead-letter review, and audit evidence.",
        "externalMutation": false,
        "status": "documented",
        "step": "commit_uses_outbox_recovery"
      }
    ],
    "status": "previewed",
    "subject": "deal:DEAL-2026-001",
    "summary": [
      {
        "detail": "review, accounting export, notification",
        "label": "Execution plans",
        "tone": "blue",
        "value": "3"
      },
      {
        "detail": "payload, idempotency, approval, secrets",
        "label": "Preflight checks",
        "tone": "green",
        "value": "4"
      },
      {
        "detail": "operator review and provider write boundaries",
        "label": "Approval gates",
        "tone": "amber",
        "value": "3"
      },
      {
        "detail": "dry-run preview sends nothing",
        "label": "External writes",
        "tone": "violet",
        "value": "0"
      }
    ]
  },
  "businessApprovalGateway": {
    "api": {
      "actionExecution": "POST /tenants/{tenant_id}/business-action-executions/preview",
      "preview": "POST /tenants/{tenant_id}/business-approval-gateway/preview",
      "standalone": "GET /demo/business-approval-gateway",
      "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview"
    },
    "approvalRequests": [
      {
        "action": "queue_accounting_export_after_review",
        "approvalKey": "approval.preview.001",
        "approverRole": "owner",
        "commitWouldMutateProvider": true,
        "containsPii": false,
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "idempotencyKey": "business-approval-gateway:deal:DEAL-2026-001:queue_accounting_export_after_review:001",
        "rawPayloadIncluded": false,
        "requesterRole": "accountant",
        "requiresDualControl": true,
        "sourceIdempotencyKey": "business-action-execution:deal:DEAL-2026-001:queue_accounting_export_after_review:002",
        "status": "approval_required",
        "subject": "deal:DEAL-2026-001"
      }
    ],
    "approverRouting": [
      {
        "evidence": "business_approval_gateway.previewed",
        "externalDelivery": false,
        "notificationChannel": "in_app",
        "ownerRole": "owner",
        "queue": "approval.review",
        "route": "owner_or_accountant_review",
        "slaMinutes": 120,
        "status": "ready"
      },
      {
        "evidence": "business_approval_gateway.previewed",
        "externalDelivery": false,
        "notificationChannel": "in_app",
        "ownerRole": "owner",
        "queue": "approval.escalation",
        "route": "escalate_if_sla_missed",
        "slaMinutes": 240,
        "status": "armed"
      }
    ],
    "auditTrail": [
      {
        "actorRole": "accountant",
        "event": "business_approval.requested",
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "status": "would_record",
        "subject": "deal:DEAL-2026-001"
      },
      {
        "actorRole": "system",
        "event": "business_approval.policy_checked",
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "status": "would_record",
        "subject": "deal:DEAL-2026-001"
      },
      {
        "actorRole": "owner",
        "event": "business_approval.commit_unlocked",
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "status": "blocked_until_approved",
        "subject": "deal:DEAL-2026-001"
      }
    ],
    "command": "POST /tenants/{tenant_id}/business-approval-gateway/preview",
    "commitUnlocks": [
      {
        "action": "queue_accounting_export_after_review",
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "outboxReady": true,
        "providerWriteUnlocked": false,
        "rollbackAttached": true,
        "status": "blocked_until_approved",
        "unlockKey": "commit.unlock.001",
        "wouldEnqueueEvent": "business.action.approval_granted",
        "wouldRecord": "WorkflowActionRun"
      }
    ],
    "dataBoundaries": [
      {
        "externalMutation": false,
        "name": "preview_only_no_approval_record",
        "status": "preview_only"
      },
      {
        "externalMutation": false,
        "name": "provider_write_locked",
        "status": "closed"
      },
      {
        "externalMutation": false,
        "name": "rbac_dual_control",
        "status": "enforced"
      },
      {
        "containsPii": false,
        "name": "safe_approval_payload",
        "rawPayloadIncluded": false,
        "status": "clean"
      }
    ],
    "docs": [
      {
        "label": "Business Approval Gateway",
        "path": "docs/public/BUSINESS_APPROVAL_GATEWAY.md"
      },
      {
        "label": "Business Action Execution",
        "path": "docs/public/BUSINESS_ACTION_EXECUTION.md"
      },
      {
        "label": "Business Task Handoff",
        "path": "docs/public/BUSINESS_TASK_HANDOFF.md"
      }
    ],
    "policyChecks": [
      {
        "check": "rbac_approver_role",
        "detail": "Approver role is allowed to review provider-changing commits.",
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "status": "passed"
      },
      {
        "check": "dual_control_required",
        "detail": "Requester and approver stay separated before commit unlock.",
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "status": "required"
      },
      {
        "check": "idempotency_preserved",
        "detail": "Approval request keeps source and approval idempotency keys.",
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "status": "passed"
      },
      {
        "check": "provider_write_closed_until_approval",
        "detail": "Provider write stays locked until approval is recorded.",
        "evidence": "business_approval_gateway.previewed",
        "externalMutation": false,
        "status": "closed"
      }
    ],
    "role": "accountant",
    "status": "previewed",
    "subject": "deal:DEAL-2026-001",
    "summary": [
      {
        "detail": "provider-changing commit candidate",
        "label": "Approval requests",
        "tone": "amber",
        "value": "1"
      },
      {
        "detail": "RBAC, dual control, idempotency, write lock",
        "label": "Policy checks",
        "tone": "green",
        "value": "4"
      },
      {
        "detail": "blocked until approved",
        "label": "Commit unlocks",
        "tone": "blue",
        "value": "1"
      },
      {
        "detail": "approval preview unlocks nothing",
        "label": "Provider writes",
        "tone": "violet",
        "value": "0"
      }
    ]
  },
  "businessContextAssistant": {
    "api": {
      "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
      "preview": "POST /tenants/{tenant_id}/business-workbench-context/preview",
      "providerIntake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "standalone": "GET /demo/business-context-assistant"
    },
    "command": "POST /tenants/{tenant_id}/business-workbench-context/preview",
    "contextCards": [
      {
        "containsPii": false,
        "evidence": "business_workbench_context.previewed",
        "externalFetch": false,
        "externalMutation": false,
        "id": "context.crm.deal-state",
        "rawPayloadIncluded": false,
        "reason": "CRM stage expects payment confirmation before accounting export.",
        "safeFact": "invoice_sent",
        "sourceSystem": "crm.bitrix24.mock",
        "status": "attention",
        "systemFamily": "crm",
        "title": "CRM deal state"
      },
      {
        "containsPii": false,
        "evidence": "business_workbench_context.previewed",
        "externalFetch": false,
        "externalMutation": false,
        "id": "context.bank.payment-evidence",
        "rawPayloadIncluded": false,
        "reason": "Bank statement has a matching amount bucket but no raw payer details are exposed.",
        "safeFact": "amount_bucket:1000-2000",
        "sourceSystem": "bank.statement.mock",
        "status": "ready",
        "systemFamily": "bank",
        "title": "Bank payment evidence"
      },
      {
        "containsPii": false,
        "evidence": "business_workbench_context.previewed",
        "externalFetch": false,
        "externalMutation": false,
        "id": "context.accounting.export-gap",
        "rawPayloadIncluded": false,
        "reason": "Payment can be reconciled before the accounting export is queued.",
        "safeFact": "export_pending",
        "sourceSystem": "accounting.export.mock",
        "status": "action_required",
        "systemFamily": "accounting",
        "title": "Accounting export gap"
      },
      {
        "containsPii": false,
        "evidence": "business_workbench_context.previewed",
        "externalFetch": false,
        "externalMutation": false,
        "fullTextIncluded": false,
        "id": "context.legal.policy-reference",
        "rawPayloadIncluded": false,
        "reason": "The operator gets a template reference, not copied legal text or external account data.",
        "safeFact": "payment_status_note_template",
        "sourceSystem": "legal.reference.mock",
        "status": "documented",
        "systemFamily": "legal",
        "title": "Policy reference"
      }
    ],
    "dataBoundaries": [
      {
        "externalFetch": false,
        "externalMutation": false,
        "name": "read_only_context_preview",
        "status": "preview_only"
      },
      {
        "containsPii": false,
        "name": "no_raw_provider_payload",
        "rawPayloadIncluded": false,
        "status": "clean"
      },
      {
        "browserTokenStorage": false,
        "name": "secret_boundary",
        "requiresSecret": false,
        "status": "clean"
      },
      {
        "externalAccountDataIncluded": false,
        "fullTextIncluded": false,
        "name": "legal_reference_link_only",
        "status": "documented"
      }
    ],
    "docs": [
      {
        "label": "Business Context Assistant",
        "path": "docs/public/BUSINESS_CONTEXT_ASSISTANT.md"
      },
      {
        "label": "Business Control Tower",
        "path": "docs/public/BUSINESS_CONTROL_TOWER.md"
      },
      {
        "label": "Provider Connector Guide",
        "path": "docs/public/PROVIDER_CONNECTOR_GUIDE.md"
      }
    ],
    "insightRules": [
      {
        "evidence": "business_workbench_context.previewed",
        "externalMutation": false,
        "result": "bank amount bucket can support CRM payment review",
        "rule": "correlate_payment_evidence",
        "sources": [
          "crm.bitrix24.mock",
          "bank.statement.mock"
        ],
        "status": "ready"
      },
      {
        "evidence": "business_workbench_context.previewed",
        "externalMutation": false,
        "result": "accounting export remains pending until operator review",
        "rule": "detect_accounting_export_gap",
        "sources": [
          "accounting.export.mock"
        ],
        "status": "attention"
      },
      {
        "evidence": "business_workbench_context.previewed",
        "externalMutation": false,
        "fullTextIncluded": false,
        "result": "operator sees a policy/template reference without copied external content",
        "rule": "attach_policy_reference",
        "sources": [
          "legal.reference.mock"
        ],
        "status": "documented"
      }
    ],
    "role": "accountant",
    "sourceSystems": [
      "crm.bitrix24.mock",
      "bank.statement.mock",
      "accounting.export.mock",
      "legal.reference.mock"
    ],
    "status": "previewed",
    "subject": "deal:DEAL-2026-001",
    "suggestedActions": [
      {
        "action": "open_reconciliation_plan",
        "endpoint": "POST /tenants/{tenant_id}/business-action-plans/preview",
        "evidence": "business_action_plan.previewed",
        "externalMutation": false,
        "mode": "operator_review",
        "requiresApproval": false,
        "status": "recommended"
      },
      {
        "action": "queue_accounting_export_after_review",
        "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
        "evidence": "accounting.export.requested",
        "externalMutation": false,
        "mode": "approval_required",
        "requiresApproval": true,
        "status": "approval_required"
      },
      {
        "action": "attach_policy_reference",
        "endpoint": "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
        "evidence": "business_workbench_context.previewed",
        "externalMutation": false,
        "mode": "internal_reference",
        "requiresApproval": false,
        "status": "ready"
      },
      {
        "action": "prepare_internal_notification",
        "endpoint": "POST /tenants/{tenant_id}/business-notification-channels/preview",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalMutation": false,
        "mode": "draft_only",
        "requiresApproval": false,
        "status": "draft_only"
      }
    ],
    "summary": [
      {
        "detail": "CRM, bank, accounting, legal reference",
        "label": "Context cards",
        "tone": "blue",
        "value": "4"
      },
      {
        "detail": "safe facts normalized into one work surface",
        "label": "Source systems",
        "tone": "green",
        "value": "4"
      },
      {
        "detail": "operator-review and draft-only next steps",
        "label": "Suggested actions",
        "tone": "amber",
        "value": "4"
      },
      {
        "detail": "context preview never mutates providers",
        "label": "External writes",
        "tone": "violet",
        "value": "0"
      }
    ]
  },
  "businessControlTower": {
    "actionPlan": {
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-action-plans/preview"
      },
      "approvalGates": [
        {
          "evidence": "repair_action.approved",
          "externalMutation": false,
          "name": "repair_action_approval",
          "requiresApproval": true,
          "status": "satisfied"
        }
      ],
      "automationCandidates": [
        {
          "action": "execute_repair_dry_run",
          "adapterKey": "internal.noop",
          "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "evidence": "repair_action.approved",
          "externalMutation": false,
          "name": "queue_repair_execution",
          "status": "ready"
        },
        {
          "action": "run_read_only_connection_check",
          "adapterKey": "accounting.export.mock",
          "endpoint": "POST /tenants/{tenant_id}/integration-connections/{connection_id}/checks",
          "evidence": "integration_connection.check.requested",
          "externalMutation": false,
          "name": "recheck_accounting_export",
          "status": "available"
        }
      ],
      "lanes": [
        {
          "lane": "finance_reconciliation",
          "ownerRole": "accountant",
          "slaMinutes": 120,
          "status": "active",
          "workItems": 1
        }
      ],
      "planKind": "exception_resolution",
      "reviewPoints": [
        {
          "detail": "Cross-system facts become ordered work inside DriveDesk.",
          "name": "single_work_surface",
          "status": "ready"
        },
        {
          "detail": "External-facing repair remains behind approval and dry-run evidence.",
          "name": "approval_boundary",
          "status": "satisfied"
        },
        {
          "detail": "The action plan preview does not create tasks, notify users, or mutate external systems.",
          "name": "automation_boundary",
          "status": "preview_only"
        }
      ],
      "riskLevel": "attention",
      "role": "accountant",
      "steps": [
        {
          "endpoint": "GET /tenants/{tenant_id}/business-state/observations",
          "evidence": "business_state.observation.recorded",
          "externalMutation": false,
          "lane": "finance_reconciliation",
          "ownerRole": "accountant",
          "requiresApproval": false,
          "sequence": 1,
          "sourceSystems": [
            "crm.bitrix24.mock",
            "bank.statement.mock",
            "accounting.export.mock"
          ],
          "status": "ready",
          "step": "verify_source_evidence",
          "summary": "Review CRM, bank, and accounting state before any repair."
        },
        {
          "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "evidence": "repair_action.approved",
          "externalMutation": false,
          "lane": "finance_reconciliation",
          "ownerRole": "accountant",
          "requiresApproval": false,
          "sequence": 2,
          "status": "ready",
          "step": "execute_repair_dry_run",
          "summary": "Queue the approved sync_status repair in dry-run mode."
        },
        {
          "endpoint": "POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/status",
          "evidence": "business_exception.status_changed",
          "externalMutation": false,
          "lane": "finance_reconciliation",
          "ownerRole": "accountant",
          "requiresApproval": false,
          "sequence": 3,
          "status": "waiting_for_repair",
          "step": "close_or_acknowledge_exception",
          "summary": "Record the accountant decision after dry-run evidence is reviewed."
        }
      ],
      "summary": "The accountant gets one ordered work plan from CRM, bank, accounting, exception, and repair evidence."
    },
    "api": {
      "approve": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/approve",
      "exceptions": "POST /tenants/{tenant_id}/business-exceptions",
      "execute": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
      "intake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "observe": "POST /tenants/{tenant_id}/business-state/observations",
      "repair": "POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/repair-actions"
    },
    "briefing": {
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-briefings/preview"
      },
      "highlights": [
        {
          "detail": "One open crm_payment_mismatch affects deal:DEAL-2026-001.",
          "evidence": "business_exception.created",
          "title": "Payment received but CRM and accounting lag behind",
          "type": "business_exception"
        },
        {
          "detail": "bank.statement.mock reports paid with matched payment reference.",
          "evidence": "business_state.observation.recorded",
          "title": "Bank state",
          "type": "state_observation"
        },
        {
          "detail": "sync_status can queue a dry-run repair event without external mutation.",
          "evidence": "repair_action.approved",
          "title": "Approved dry-run repair",
          "type": "repair_context"
        }
      ],
      "recommendedActions": [
        {
          "action": "execute_repair_dry_run",
          "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "evidence": "repair_action.approved",
          "status": "ready"
        },
        {
          "action": "review_accounting_export",
          "endpoint": "GET /tenants/{tenant_id}/business-exceptions",
          "evidence": "accounting.export.mock:not_exported",
          "status": "available"
        }
      ],
      "reviewPoints": [
        {
          "detail": "CRM, bank, and accounting states are visible in one briefing.",
          "name": "source_evidence",
          "status": "ready"
        },
        {
          "detail": "External writes stay behind approval and outbox evidence.",
          "name": "external_mutation",
          "status": "review_required"
        }
      ],
      "riskLevel": "attention",
      "role": "accountant",
      "sourceSystems": [
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock"
      ],
      "summary": "Payment is visible in bank evidence, but CRM still shows invoice_sent and accounting export is waiting."
    },
    "detection": {
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-detections/preview"
      },
      "detectedExceptions": [
        {
          "confidence": "high",
          "evidence": "business_detection.previewed",
          "severity": "warning",
          "subject": "deal:DEAL-2026-001",
          "type": "crm_payment_mismatch",
          "wouldCreate": "BusinessException"
        }
      ],
      "ruleSet": "payment_reconciliation",
      "rules": [
        {
          "if": [
            "crm.state=invoice_sent",
            "bank.state=paid",
            "accounting.state=not_exported"
          ],
          "key": "payment_reconciliation.crm_bank_accounting_mismatch",
          "status": "active",
          "then": [
            "detect crm_payment_mismatch",
            "suggest sync_status repair"
          ]
        }
      ],
      "status": "detected",
      "suggestedRepairActions": [
        {
          "action": "sync_status",
          "evidence": "business_detection.previewed",
          "externalMutation": false,
          "requiresApproval": true,
          "status": "suggested",
          "wouldCreate": "RepairAction"
        }
      ],
      "summary": "Detector reviewed CRM, bank, and accounting observations and found one payment reconciliation exception candidate."
    },
    "escalation": {
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-escalations/preview"
      },
      "items": [
        {
          "escalationLevel": "L2",
          "evidence": "business_escalation.previewed",
          "exceptionType": "crm_payment_mismatch",
          "externalMutation": false,
          "nextAction": "execute_repair_dry_run",
          "nextActionStatus": "ready",
          "ownerRole": "accountant",
          "queue": "finance_reconciliation",
          "severity": "warning",
          "slaMinutes": 120,
          "status": "open",
          "subject": "deal:DEAL-2026-001"
        }
      ],
      "policy": "exception_triage",
      "queues": [
        {
          "highestSeverity": "warning",
          "minSlaMinutes": 120,
          "openItems": 1,
          "ownerRole": "accountant",
          "queue": "finance_reconciliation",
          "status": "active"
        }
      ],
      "reviewPoints": [
        {
          "detail": "Escalation does not create tasks, approve repairs, or mutate external systems.",
          "name": "write_boundary",
          "status": "preview_only"
        },
        {
          "detail": "Exception type and severity map to role, queue, and SLA.",
          "name": "owner_routing",
          "status": "ready"
        }
      ],
      "riskLevel": "attention",
      "suggestedActions": [
        {
          "action": "execute_repair_dry_run",
          "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "evidence": "repair_action.approved",
          "externalMutation": false,
          "status": "ready"
        }
      ],
      "summary": "One warning exception is routed to the finance reconciliation queue with a dry-run repair next step."
    },
    "exceptions": [
      {
        "evidence": "business_exception.created",
        "id": "bex-payment-crm-mismatch",
        "impact": "cash received but CRM and accounting are not aligned",
        "severity": "warning",
        "status": "open",
        "subject": "deal:DEAL-2026-001",
        "type": "crm_payment_mismatch"
      }
    ],
    "flow": [
      {
        "detail": "Provider payload is reduced to safe normalized observation fields.",
        "evidence": "business_provider_intake.previewed",
        "owner": "adapter",
        "state": "preview_only",
        "step": "intake"
      },
      {
        "detail": "CRM, bank, and accounting states are normalized into one subject.",
        "evidence": "business_state.observation.recorded",
        "owner": "adapter",
        "state": "done",
        "step": "observe"
      },
      {
        "detail": "Role-specific cards summarize external state without provider reads, secrets, or PII.",
        "evidence": "business_workbench_context.previewed",
        "owner": "workbench",
        "state": "preview_only",
        "step": "context"
      },
      {
        "detail": "Payment state mismatch becomes a business exception with impact.",
        "evidence": "business_exception.created",
        "owner": "control_tower",
        "state": "done",
        "step": "detect"
      },
      {
        "detail": "Repair action is proposed without direct external mutation.",
        "evidence": "repair_action.proposed",
        "owner": "repair_engine",
        "state": "done",
        "step": "propose"
      },
      {
        "detail": "Human approval is recorded before execution.",
        "evidence": "repair_action.approved",
        "owner": "operator",
        "state": "done",
        "step": "approve"
      },
      {
        "detail": "The operator receives an ordered action plan with approval and automation boundaries.",
        "evidence": "business_action_plan.previewed",
        "owner": "workbench",
        "state": "ready",
        "step": "plan"
      },
      {
        "detail": "DriveDesk prepares notification drafts without external delivery.",
        "evidence": "business_notification.previewed",
        "owner": "workbench",
        "state": "preview_only",
        "step": "notify"
      },
      {
        "detail": "Dry-run execution queues a repair event and records result evidence.",
        "evidence": "repair_action.execution_requested",
        "owner": "outbox",
        "state": "done",
        "step": "execute"
      }
    ],
    "metrics": [
      "drivedesk_business_state_observations",
      "drivedesk_business_exceptions",
      "drivedesk_repair_actions"
    ],
    "notifications": {
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-notifications/preview"
      },
      "approvalGates": [
        {
          "evidence": "business_notification.previewed",
          "externalDelivery": false,
          "name": "notification_content_review",
          "requiresApproval": false,
          "status": "ready"
        },
        {
          "evidence": "repair_action.approved",
          "externalDelivery": false,
          "name": "repair_action_approval",
          "requiresApproval": true,
          "status": "satisfied"
        }
      ],
      "channels": [
        {
          "channel": "in_app",
          "configured": true,
          "evidence": "business_notification.previewed",
          "externalDelivery": false,
          "requiresSecret": false,
          "status": "ready"
        },
        {
          "channel": "telegram",
          "configured": false,
          "evidence": "business_notification.previewed",
          "externalDelivery": false,
          "requiresSecret": true,
          "status": "requires_channel_config"
        }
      ],
      "deliveryPlan": [
        {
          "channel": "in_app",
          "evidence": "business_notification.previewed",
          "externalDelivery": false,
          "recipientRole": "accountant",
          "requiresSecret": false,
          "sendMode": "preview_only",
          "status": "ready",
          "wouldEnqueueEvent": "notification.delivery.requested"
        },
        {
          "channel": "telegram",
          "evidence": "business_notification.previewed",
          "externalDelivery": false,
          "recipientRole": "accountant",
          "requiresSecret": true,
          "sendMode": "preview_only",
          "status": "requires_channel_config",
          "wouldEnqueueEvent": "notification.delivery.requested"
        }
      ],
      "drafts": [
        {
          "actionEndpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "body": "deal:DEAL-2026-001 has a ready action plan step: execute_repair_dry_run.",
          "channel": "in_app",
          "draftId": "action_plan_updates.in_app.accountant",
          "evidence": "business_notification.previewed",
          "externalDelivery": false,
          "piiIncluded": false,
          "recipientRole": "accountant",
          "status": "ready",
          "title": "Payment mismatch action plan is ready"
        },
        {
          "actionEndpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "body": "deal:DEAL-2026-001 has a ready action plan step: execute_repair_dry_run.",
          "channel": "telegram",
          "draftId": "action_plan_updates.telegram.accountant",
          "evidence": "business_notification.previewed",
          "externalDelivery": false,
          "piiIncluded": false,
          "recipientRole": "accountant",
          "status": "preview_only",
          "title": "Payment mismatch action plan is ready"
        }
      ],
      "notificationKind": "action_plan_updates",
      "reviewPoints": [
        {
          "detail": "Notification preview does not call Telegram, email, CRM, or any other provider.",
          "name": "no_external_send",
          "status": "preview_only"
        },
        {
          "detail": "Drafts avoid raw personal data and use role, subject key, endpoint, and evidence labels.",
          "name": "pii_boundary",
          "status": "clean"
        }
      ],
      "riskLevel": "attention",
      "role": "accountant",
      "summary": "DriveDesk prepares safe in-app and Telegram notification drafts from the current action plan."
    },
    "observations": [
      {
        "evidence": "business_state.observation.recorded",
        "id": "obs-crm-deal",
        "observedAt": "2026-06-19T06:05:00Z",
        "state": "invoice_sent",
        "subject": "deal:DEAL-2026-001",
        "system": "crm.bitrix24.mock"
      },
      {
        "evidence": "business_state.observation.recorded",
        "id": "obs-bank-payment",
        "observedAt": "2026-06-19T06:06:00Z",
        "state": "paid",
        "subject": "deal:DEAL-2026-001",
        "system": "bank.statement.mock"
      },
      {
        "evidence": "business_state.observation.recorded",
        "id": "obs-accounting-export",
        "observedAt": "2026-06-19T06:07:00Z",
        "state": "not_exported",
        "subject": "deal:DEAL-2026-001",
        "system": "accounting.export.mock"
      }
    ],
    "providerIntake": {
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-provider-intake/preview"
      },
      "dataBoundaries": [
        {
          "detail": "Provider intake preview does not create observations or call provider APIs.",
          "name": "preview_only_no_persist",
          "status": "preview_only"
        },
        {
          "detail": "Only safe fields and dropped key names are returned to the workbench.",
          "name": "raw_provider_payload_not_returned",
          "status": "clean"
        },
        {
          "detail": "No Bitrix, bank, accounting, Telegram, or email credentials are required.",
          "name": "secret_boundary",
          "status": "clean"
        }
      ],
      "droppedKeys": [
        "access_token",
        "full_name",
        "phone"
      ],
      "nextSteps": [
        {
          "endpoint": "POST /tenants/{tenant_id}/business-state/observations",
          "evidence": "business_state.observation.recorded",
          "externalMutation": false,
          "status": "available",
          "step": "record_normalized_observation"
        },
        {
          "endpoint": "POST /tenants/{tenant_id}/business-workbench-context/preview",
          "evidence": "business_workbench_context.previewed",
          "externalMutation": false,
          "status": "available",
          "step": "open_workbench_context"
        },
        {
          "endpoint": "POST /tenants/{tenant_id}/business-detections/preview",
          "evidence": "business_detection.previewed",
          "externalMutation": false,
          "status": "available",
          "step": "run_detection_preview"
        }
      ],
      "normalizedObservation": {
        "externalFetch": false,
        "externalMutation": false,
        "externalRef": "crm-deal-001",
        "piiIncluded": false,
        "rawPayloadIncluded": false,
        "requiresSecret": false,
        "state": "invoice_sent",
        "subject": "deal:DEAL-2026-001",
        "systemFamily": "crm",
        "systemKey": "crm.bitrix24.mock",
        "wouldCreate": "BusinessStateObservation",
        "wouldRecordEvent": "business_state.observation.recorded"
      },
      "payloadKeys": [
        "access_token",
        "amount",
        "full_name",
        "owner_role",
        "phone",
        "stage"
      ],
      "providerKey": "crm.bitrix24.mock",
      "safePayload": {
        "amount_bucket": "1000-2000",
        "owner_role": "sales",
        "source_state": "invoice_sent"
      },
      "sourceType": "crm_deal",
      "status": "mapped",
      "subject": "deal:DEAL-2026-001",
      "summary": "Bitrix-style deal payload is mapped into a normalized observation before DriveDesk builds workbench context."
    },
    "repairActions": [
      {
        "action": "sync_status",
        "evidence": "repair_action.executed",
        "externalMutation": false,
        "id": "repair-sync-crm-payment",
        "mode": "dry_run",
        "requiresApproval": true,
        "safety": "medium",
        "status": "approved"
      }
    ],
    "summary": [
      {
        "detail": "crm, bank, accounting",
        "label": "Observed systems",
        "tone": "blue",
        "value": "3"
      },
      {
        "detail": "payment state mismatch",
        "label": "Open exceptions",
        "tone": "amber",
        "value": "1"
      },
      {
        "detail": "approval-gated dry-run",
        "label": "Repair actions",
        "tone": "green",
        "value": "1"
      },
      {
        "detail": "public-safe execution",
        "label": "External writes",
        "tone": "violet",
        "value": "0"
      },
      {
        "detail": "role workbench preview",
        "label": "Context cards",
        "tone": "blue",
        "value": "3"
      },
      {
        "detail": "safe CRM payload preview",
        "label": "Provider intake",
        "tone": "green",
        "value": "1"
      }
    ],
    "workbenchContext": {
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-workbench-context/preview"
      },
      "contextCards": [
        {
          "cardId": "crm.deal.DEAL-2026-001.invoice_sent",
          "evidence": "business_workbench_context.previewed",
          "externalFetch": false,
          "externalMutation": false,
          "payloadKeys": [
            "amount_bucket",
            "owner_role"
          ],
          "piiIncluded": false,
          "rawPayloadIncluded": false,
          "safeFacts": [
            {
              "key": "amount_bucket",
              "value": "1000-2000"
            },
            {
              "key": "owner_role",
              "value": "sales"
            }
          ],
          "state": "invoice_sent",
          "status": "needs_cross_check",
          "subject": "deal:DEAL-2026-001",
          "systemFamily": "crm",
          "systemKey": "crm.bitrix24.mock",
          "title": "CRM deal context"
        },
        {
          "cardId": "bank.deal.DEAL-2026-001.paid",
          "evidence": "business_workbench_context.previewed",
          "externalFetch": false,
          "externalMutation": false,
          "payloadKeys": [
            "amount_bucket",
            "matched_by"
          ],
          "piiIncluded": false,
          "rawPayloadIncluded": false,
          "safeFacts": [
            {
              "key": "amount_bucket",
              "value": "1000-2000"
            },
            {
              "key": "matched_by",
              "value": "payment_reference"
            }
          ],
          "state": "paid",
          "status": "confirmed",
          "subject": "deal:DEAL-2026-001",
          "systemFamily": "bank",
          "systemKey": "bank.statement.mock",
          "title": "Payment evidence"
        },
        {
          "cardId": "accounting.deal.DEAL-2026-001.not_exported",
          "evidence": "business_workbench_context.previewed",
          "externalFetch": false,
          "externalMutation": false,
          "payloadKeys": [
            "export_batch_id",
            "reason"
          ],
          "piiIncluded": false,
          "rawPayloadIncluded": false,
          "safeFacts": [
            {
              "key": "export_batch_id",
              "value": "batch-001"
            },
            {
              "key": "reason",
              "value": "waiting_for_crm_status"
            }
          ],
          "state": "not_exported",
          "status": "action_required",
          "subject": "deal:DEAL-2026-001",
          "systemFamily": "accounting",
          "systemKey": "accounting.export.mock",
          "title": "Accounting export context"
        }
      ],
      "contextKind": "role_assist",
      "dataBoundaries": [
        {
          "detail": "The preview uses normalized DriveDesk observations and does not call provider APIs.",
          "externalFetch": false,
          "externalMutation": false,
          "name": "read_only_source_context",
          "status": "preview_only"
        },
        {
          "detail": "Cards expose safe facts and payload keys, not raw provider payloads.",
          "name": "pii_redaction",
          "rawPayloadIncluded": false,
          "status": "clean"
        },
        {
          "detail": "No Bitrix, bank, accounting, Telegram, or email credentials are required for preview.",
          "name": "secret_boundary",
          "requiresSecret": false,
          "status": "clean"
        }
      ],
      "reviewPoints": [
        {
          "detail": "External facts are rendered next to the operator workflow inside DriveDesk.",
          "name": "single_work_surface",
          "status": "ready"
        },
        {
          "detail": "Suggested actions link only to DriveDesk previews and approval-gated flows.",
          "name": "next_action_boundary",
          "status": "preview_only"
        }
      ],
      "riskLevel": "attention",
      "role": "accountant",
      "sourceSystems": [
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock"
      ],
      "suggestedActions": [
        {
          "action": "reconcile_crm_payment_status",
          "endpoint": "POST /tenants/{tenant_id}/business-detections/preview",
          "evidence": "business_workbench_context.previewed",
          "externalMutation": false,
          "requiresApproval": false,
          "status": "available",
          "summary": "Compare the paid bank state with the CRM deal state before any external write."
        },
        {
          "action": "review_accounting_export",
          "endpoint": "GET /tenants/{tenant_id}/business-state/observations",
          "evidence": "business_workbench_context.previewed",
          "externalMutation": false,
          "requiresApproval": false,
          "status": "available",
          "summary": "Open the accounting export evidence and decide whether a dry-run repair is needed."
        },
        {
          "action": "open_action_plan_preview",
          "endpoint": "POST /tenants/{tenant_id}/business-action-plans/preview",
          "evidence": "business_action_plan.previewed",
          "externalMutation": false,
          "requiresApproval": false,
          "status": "ready",
          "summary": "Turn the current context into ordered operator work inside DriveDesk."
        }
      ],
      "summary": "DriveDesk turns CRM, bank, and accounting observations into safe workbench cards before the accountant decides what to do next."
    }
  },
  "businessIntakePipeline": {
    "actionPlan": {
      "approvalGates": [
        {
          "gate": "external_write_gate",
          "status": "closed"
        },
        {
          "gate": "notification_delivery_gate",
          "status": "approval_required"
        }
      ],
      "riskLevel": "attention",
      "steps": [
        {
          "evidence": "business_provider_intake.previewed",
          "externalMutation": false,
          "status": "previewed",
          "step": "normalize_provider_events"
        },
        {
          "evidence": "business_workbench_context.previewed",
          "externalMutation": false,
          "status": "ready",
          "step": "open_role_workbench"
        },
        {
          "evidence": "business_detection.previewed",
          "externalMutation": false,
          "status": "action_required",
          "step": "review_detected_exceptions"
        },
        {
          "evidence": "business_action_plan.previewed",
          "externalMutation": false,
          "status": "approval_required",
          "step": "prepare_approval_gated_repair"
        }
      ]
    },
    "api": {
      "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
      "detections": "POST /tenants/{tenant_id}/business-detections/preview",
      "notifications": "POST /tenants/{tenant_id}/business-notifications/preview",
      "preview": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
      "providerIntake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "workbenchContext": "POST /tenants/{tenant_id}/business-workbench-context/preview"
    },
    "command": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
    "dataBoundaries": [
      {
        "externalFetch": false,
        "externalMutation": false,
        "name": "no_external_calls",
        "status": "clean"
      },
      {
        "externalMutation": false,
        "name": "no_persistence",
        "status": "preview_only"
      },
      {
        "name": "secret_and_pii_boundary",
        "piiIncluded": false,
        "rawPayloadIncluded": false,
        "requiresSecret": false,
        "status": "clean"
      }
    ],
    "detections": {
      "detectedExceptions": [
        {
          "exceptionType": "crm_payment_mismatch",
          "externalMutation": false,
          "severity": "warning",
          "subject": "deal:DEAL-2026-001",
          "wouldCreate": "BusinessException"
        }
      ],
      "ruleSet": "payment_reconciliation",
      "status": "detected",
      "suggestedRepairActions": [
        {
          "actionType": "sync_status",
          "externalMutation": false,
          "requiresApproval": true,
          "status": "suggested",
          "wouldCreate": "RepairAction"
        }
      ]
    },
    "docs": [
      {
        "label": "Business Intake Pipeline",
        "path": "docs/public/BUSINESS_INTAKE_PIPELINE.md"
      },
      {
        "label": "Business Control Tower",
        "path": "docs/public/BUSINESS_CONTROL_TOWER.md"
      },
      {
        "label": "API-backed Demo",
        "path": "docs/public/API_BACKED_DEMO.md"
      }
    ],
    "intakePreviews": [
      {
        "droppedKeys": [
          "access_token",
          "full_name",
          "phone"
        ],
        "evidence": "business_provider_intake.previewed",
        "providerKey": "crm.bitrix24.mock",
        "safePayload": {
          "amount_bucket": "1000-2000",
          "owner_role": "sales",
          "source_state": "invoice_sent"
        },
        "sourceType": "crm_deal",
        "state": "invoice_sent"
      },
      {
        "droppedKeys": [
          "payer_phone"
        ],
        "evidence": "business_provider_intake.previewed",
        "providerKey": "bank.statement.mock",
        "safePayload": {
          "amount_bucket": "1000-2000",
          "matched_by": "payment_reference",
          "source_state": "captured"
        },
        "sourceType": "bank_payment",
        "state": "paid"
      },
      {
        "droppedKeys": [
          "session_secret"
        ],
        "evidence": "business_provider_intake.previewed",
        "providerKey": "accounting.export.mock",
        "safePayload": {
          "export_batch_id": "batch-001",
          "reason": "waiting_for_crm_status",
          "source_state": "not_exported"
        },
        "sourceType": "accounting_export",
        "state": "not_exported"
      }
    ],
    "notifications": {
      "channels": [
        "in_app",
        "telegram",
        "email"
      ],
      "containsPii": false,
      "evidence": "business_notification.previewed",
      "externalDelivery": false,
      "status": "draft_only"
    },
    "sourceSystems": [
      "crm.bitrix24.mock",
      "bank.statement.mock",
      "accounting.export.mock"
    ],
    "status": "previewed",
    "summary": [
      {
        "detail": "CRM, bank, and accounting signals in one preview",
        "label": "Provider events",
        "tone": "blue",
        "value": "3"
      },
      {
        "detail": "PII and credential markers are removed",
        "label": "Dropped unsafe keys",
        "tone": "green",
        "value": "5"
      },
      {
        "detail": "payment mismatch candidate",
        "label": "Detected exceptions",
        "tone": "amber",
        "value": "1"
      },
      {
        "detail": "preview-only pipeline",
        "label": "External writes",
        "tone": "violet",
        "value": "0"
      }
    ],
    "workbench": {
      "contextCards": [
        {
          "externalMutation": false,
          "piiIncluded": false,
          "rawPayloadIncluded": false,
          "state": "invoice_sent",
          "status": "needs_cross_check",
          "systemFamily": "crm",
          "title": "CRM signal"
        },
        {
          "externalMutation": false,
          "piiIncluded": false,
          "rawPayloadIncluded": false,
          "state": "paid",
          "status": "confirmed",
          "systemFamily": "bank",
          "title": "Bank signal"
        },
        {
          "externalMutation": false,
          "piiIncluded": false,
          "rawPayloadIncluded": false,
          "state": "not_exported",
          "status": "action_required",
          "systemFamily": "accounting",
          "title": "Accounting signal"
        }
      ],
      "riskLevel": "attention",
      "role": "accountant",
      "suggestedActions": [
        {
          "action": "review_pipeline_detection",
          "evidence": "business_workbench_context.previewed",
          "externalMutation": false,
          "status": "action_required"
        },
        {
          "action": "open_action_plan_preview",
          "evidence": "business_action_plan.previewed",
          "externalMutation": false,
          "status": "ready"
        }
      ]
    }
  },
  "businessNotificationChannels": {
    "api": {
      "notifications": "POST /tenants/{tenant_id}/business-notifications/preview",
      "preview": "POST /tenants/{tenant_id}/business-notification-channels/preview",
      "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview"
    },
    "approvalGates": [
      {
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "gate": "notification_content_review",
        "requiresApproval": false,
        "status": "ready"
      },
      {
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "gate": "private_channel_secret_setup",
        "requiresApproval": true,
        "status": "required"
      },
      {
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "gate": "external_delivery_gate",
        "requiresApproval": true,
        "status": "closed"
      }
    ],
    "channels": [
      {
        "channel": "in_app",
        "configured": true,
        "containsPii": false,
        "destinationProfile": "internal_user_inbox",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "externalProviderMutation": false,
        "rawPayloadIncluded": false,
        "readiness": "usable_for_internal_work",
        "recipientRole": "accountant",
        "requiresPrivateConnector": false,
        "requiresSecret": false,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "internal_preview",
        "status": "ready",
        "subject": "deal:DEAL-2026-001"
      },
      {
        "channel": "telegram",
        "configured": false,
        "containsPii": false,
        "destinationProfile": "telegram_bot_chat",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "externalProviderMutation": false,
        "rawPayloadIncluded": false,
        "readiness": "private_connector_needed",
        "recipientRole": "accountant",
        "requiresPrivateConnector": true,
        "requiresSecret": true,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "draft_only",
        "status": "requires_private_secret",
        "subject": "deal:DEAL-2026-001"
      },
      {
        "channel": "email",
        "configured": false,
        "containsPii": false,
        "destinationProfile": "smtp_or_provider_template",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "externalProviderMutation": false,
        "rawPayloadIncluded": false,
        "readiness": "private_connector_needed",
        "recipientRole": "accountant",
        "requiresPrivateConnector": true,
        "requiresSecret": true,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "draft_only",
        "status": "requires_private_secret",
        "subject": "deal:DEAL-2026-001"
      },
      {
        "channel": "sms",
        "configured": false,
        "containsPii": false,
        "destinationProfile": "sms_provider_template",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "externalProviderMutation": false,
        "rawPayloadIncluded": false,
        "readiness": "provider_contract_needed",
        "recipientRole": "accountant",
        "requiresPrivateConnector": true,
        "requiresSecret": true,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "draft_only",
        "status": "requires_private_provider",
        "subject": "deal:DEAL-2026-001"
      },
      {
        "channel": "webhook",
        "configured": false,
        "containsPii": false,
        "destinationProfile": "signed_webhook_endpoint",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "externalProviderMutation": false,
        "rawPayloadIncluded": false,
        "readiness": "endpoint_and_signing_key_needed",
        "recipientRole": "accountant",
        "requiresPrivateConnector": true,
        "requiresSecret": true,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "draft_only",
        "status": "requires_private_endpoint",
        "subject": "deal:DEAL-2026-001"
      }
    ],
    "command": "POST /tenants/{tenant_id}/business-notification-channels/preview",
    "dataBoundaries": [
      {
        "externalDelivery": false,
        "externalProviderMutation": false,
        "name": "preview_only_no_delivery",
        "status": "preview_only"
      },
      {
        "browserTokenStorage": false,
        "name": "server_secret_store_boundary",
        "requiresSecret": true,
        "status": "documented"
      },
      {
        "containsPii": false,
        "name": "safe_notification_payload",
        "rawPayloadIncluded": false,
        "status": "clean"
      }
    ],
    "deliveryDrafts": [
      {
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "channel": "in_app",
        "containsPii": false,
        "draftId": "channel_matrix.in_app.accountant",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "rawPayloadIncluded": false,
        "recipientRole": "accountant",
        "requiresSecret": false,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "internal_preview",
        "status": "ready",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "wouldEnqueueEvent": "notification.delivery.requested"
      },
      {
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "channel": "telegram",
        "containsPii": false,
        "draftId": "channel_matrix.telegram.accountant",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "rawPayloadIncluded": false,
        "recipientRole": "accountant",
        "requiresSecret": true,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "draft_only",
        "status": "draft_only",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "wouldEnqueueEvent": "notification.delivery.requested"
      },
      {
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "channel": "email",
        "containsPii": false,
        "draftId": "channel_matrix.email.accountant",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "rawPayloadIncluded": false,
        "recipientRole": "accountant",
        "requiresSecret": true,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "draft_only",
        "status": "draft_only",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "wouldEnqueueEvent": "notification.delivery.requested"
      },
      {
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "channel": "sms",
        "containsPii": false,
        "draftId": "channel_matrix.sms.accountant",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "rawPayloadIncluded": false,
        "recipientRole": "accountant",
        "requiresSecret": true,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "draft_only",
        "status": "draft_only",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "wouldEnqueueEvent": "notification.delivery.requested"
      },
      {
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "channel": "webhook",
        "containsPii": false,
        "draftId": "channel_matrix.webhook.accountant",
        "evidence": "business_notification_channel_matrix.previewed",
        "externalDelivery": false,
        "rawPayloadIncluded": false,
        "recipientRole": "accountant",
        "requiresSecret": true,
        "safePayloadProfile": "role_subject_action_reference",
        "sendMode": "draft_only",
        "status": "draft_only",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "wouldEnqueueEvent": "notification.delivery.requested"
      }
    ],
    "docs": [
      {
        "label": "Business Notification Channels",
        "path": "docs/public/BUSINESS_NOTIFICATION_CHANNELS.md"
      },
      {
        "label": "Business Task Handoff",
        "path": "docs/public/BUSINESS_TASK_HANDOFF.md"
      },
      {
        "label": "API-backed Demo",
        "path": "docs/public/API_BACKED_DEMO.md"
      }
    ],
    "role": "accountant",
    "routingRules": [
      {
        "channel": "in_app",
        "detail": "Internal work notifications can be represented without external delivery.",
        "evidence": "business_notification_channel_matrix.previewed",
        "rule": "prefer_internal_in_app",
        "status": "ready"
      },
      {
        "channelCount": 4,
        "detail": "External delivery stays behind private connector and secret setup.",
        "evidence": "business_notification_channel_matrix.previewed",
        "rule": "external_channels_require_private_connector",
        "status": "required"
      },
      {
        "detail": "Drafts use role, subject key, action reference, and evidence labels only.",
        "evidence": "business_notification_channel_matrix.previewed",
        "payloadProfile": "role_subject_action_reference",
        "rule": "safe_payload_only",
        "status": "clean"
      }
    ],
    "status": "previewed",
    "subject": "deal:DEAL-2026-001",
    "summary": [
      {
        "detail": "in-app, Telegram, email, SMS, webhook",
        "label": "Channels",
        "tone": "blue",
        "value": "5"
      },
      {
        "detail": "in-app can stay inside DriveDesk",
        "label": "Internal ready",
        "tone": "green",
        "value": "1"
      },
      {
        "detail": "private connector setup required",
        "label": "Draft-only external",
        "tone": "amber",
        "value": "4"
      },
      {
        "detail": "public preview sends nothing",
        "label": "External deliveries",
        "tone": "violet",
        "value": "0"
      }
    ]
  },
  "businessScenarioReplay": {
    "command": "bash scripts/check_public_business_scenario_replay.sh",
    "docs": [
      {
        "label": "Business Scenario Replay",
        "path": "docs/public/BUSINESS_SCENARIO_REPLAY.md"
      },
      {
        "label": "Business Control Tower",
        "path": "docs/public/BUSINESS_CONTROL_TOWER.md"
      },
      {
        "label": "API Backed Demo",
        "path": "docs/public/API_BACKED_DEMO.md"
      },
      {
        "label": "Technical Capability Map",
        "path": "docs/public/TECHNICAL_CAPABILITY_MAP.md"
      }
    ],
    "flow": [
      {
        "detail": "External systems produce signals through adapters, files, webhooks, or polling.",
        "evidence": "provider_signal.received",
        "stage": "signal",
        "step": "1"
      },
      {
        "detail": "DriveDesk maps each signal into safe business facts with provider-specific details removed.",
        "evidence": "business_state.observation.recorded",
        "stage": "normalize",
        "step": "2"
      },
      {
        "detail": "Rules compare facts across systems and create exception candidates.",
        "evidence": "business_exception.created",
        "stage": "detect",
        "step": "3"
      },
      {
        "detail": "The workbench builds role-specific context, recommended actions, and approval gates.",
        "evidence": "business_action_plan.previewed",
        "stage": "plan",
        "step": "4"
      },
      {
        "detail": "Only approved internal actions can run; external writes stay behind explicit approval.",
        "evidence": "operator_approval.required",
        "stage": "execute",
        "step": "5"
      }
    ],
    "scenarios": [
      {
        "automationCandidates": [
          {
            "boundary": "internal_record_only",
            "candidate": "create business exception",
            "safeToAutoRun": true
          },
          {
            "boundary": "requires_operator_approval",
            "candidate": "send customer notification",
            "safeToAutoRun": false
          }
        ],
        "dataBoundary": [
          "no raw provider payload",
          "no credentials",
          "no personal data",
          "synthetic sources"
        ],
        "decision": "open reconciliation workbench",
        "evidence": [
          "business_exception.created",
          "business_action_plan.previewed",
          "integration.reconciliation.recorded"
        ],
        "id": "crm-bank-payment-mismatch",
        "normalizedFacts": [
          {
            "key": "crm_stage",
            "source": "crm.bitrix24.mock",
            "value": "invoice_sent"
          },
          {
            "key": "bank_status",
            "source": "bank.statement.mock",
            "value": "payment_seen"
          },
          {
            "key": "accounting_status",
            "source": "accounting.export.mock",
            "value": "export_pending"
          }
        ],
        "operatorRole": "accountant",
        "recommendedActions": [
          {
            "action": "compare bank amount bucket with CRM deal amount",
            "evidence": "integration.reconciliation.previewed",
            "mode": "operator_review"
          },
          {
            "action": "queue accounting export after approval",
            "evidence": "business_action_plan.previewed",
            "mode": "approval_required"
          },
          {
            "action": "prepare customer payment-status note",
            "evidence": "business_notification.previewed",
            "mode": "draft_only"
          }
        ],
        "riskLevel": "warning",
        "sourceSystems": [
          "crm.bitrix24.mock",
          "bank.statement.mock",
          "accounting.export.mock"
        ],
        "status": "attention",
        "title": "CRM and bank payment mismatch",
        "trigger": "crm.deal.updated"
      },
      {
        "automationCandidates": [
          {
            "boundary": "internal_record_only",
            "candidate": "open escalation item",
            "safeToAutoRun": true
          },
          {
            "boundary": "external_channel_blocked",
            "candidate": "place callback",
            "safeToAutoRun": false
          }
        ],
        "dataBoundary": [
          "message body omitted",
          "phone number omitted",
          "no external delivery",
          "synthetic sources"
        ],
        "decision": "escalate with context before SLA breach",
        "evidence": [
          "business_escalation.previewed",
          "business_action_plan.previewed",
          "business_notification.previewed"
        ],
        "id": "support-sla-risk",
        "normalizedFacts": [
          {
            "key": "message_state",
            "source": "support.inbox.mock",
            "value": "waiting_for_reply"
          },
          {
            "key": "callback_state",
            "source": "telephony.callback.mock",
            "value": "missed"
          },
          {
            "key": "sla_window",
            "source": "sla.policy.mock",
            "value": "15m"
          }
        ],
        "operatorRole": "support_lead",
        "recommendedActions": [
          {
            "action": "assign support lead and create reply task",
            "evidence": "business_escalation.previewed",
            "mode": "operator_review"
          },
          {
            "action": "prepare apology and callback draft",
            "evidence": "business_notification.previewed",
            "mode": "draft_only"
          }
        ],
        "riskLevel": "high",
        "sourceSystems": [
          "support.inbox.mock",
          "telephony.callback.mock",
          "sla.policy.mock"
        ],
        "status": "action_required",
        "title": "Support SLA risk",
        "trigger": "support.message.received"
      },
      {
        "automationCandidates": [
          {
            "boundary": "internal_record_only",
            "candidate": "create manager task",
            "safeToAutoRun": true
          },
          {
            "boundary": "financial_write_blocked",
            "candidate": "release bank payment",
            "safeToAutoRun": false
          }
        ],
        "dataBoundary": [
          "no bank credentials",
          "no supplier raw payload",
          "payment values bucketed",
          "synthetic sources"
        ],
        "decision": "create procurement exception and check cash timing",
        "evidence": [
          "business_exception.created",
          "business_workbench_context.previewed",
          "business_action_plan.previewed"
        ],
        "id": "procurement-delay-risk",
        "normalizedFacts": [
          {
            "key": "supplier_state",
            "source": "supplier.portal.mock",
            "value": "delayed"
          },
          {
            "key": "stock_state",
            "source": "inventory.stock.mock",
            "value": "below_minimum"
          },
          {
            "key": "payment_order",
            "source": "bank.payment-order.mock",
            "value": "prepared"
          }
        ],
        "operatorRole": "operations_manager",
        "recommendedActions": [
          {
            "action": "open procurement exception",
            "evidence": "business_exception.created",
            "mode": "operator_review"
          },
          {
            "action": "compare supplier ETA with minimum stock window",
            "evidence": "business_workbench_context.previewed",
            "mode": "operator_review"
          },
          {
            "action": "hold payment order until manager approval",
            "evidence": "business_action_plan.previewed",
            "mode": "approval_required"
          }
        ],
        "riskLevel": "medium",
        "sourceSystems": [
          "supplier.portal.mock",
          "inventory.stock.mock",
          "bank.payment-order.mock"
        ],
        "status": "needs_cross_check",
        "title": "Procurement delay risk",
        "trigger": "supplier.delivery.updated"
      }
    ],
    "status": "validated",
    "summary": [
      {
        "detail": "CRM, support, and procurement replay paths",
        "label": "Scenario groups",
        "tone": "blue",
        "value": "3"
      },
      {
        "detail": "external signals normalized before action",
        "label": "Source systems",
        "tone": "green",
        "value": "7"
      },
      {
        "detail": "recommended actions stay approval-aware",
        "label": "Operator actions",
        "tone": "amber",
        "value": "8"
      },
      {
        "detail": "public replay is read-only",
        "label": "External writes",
        "tone": "violet",
        "value": "0"
      }
    ]
  },
  "businessTaskHandoff": {
    "api": {
      "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
      "preview": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
      "taskRecords": "POST /tenants/{tenant_id}/business-records",
      "workflowRules": "POST /tenants/{tenant_id}/workflow-rules"
    },
    "approvalGates": [
      {
        "externalMutation": false,
        "gate": "task_creation_review",
        "requiresApproval": false,
        "status": "required"
      },
      {
        "externalMutation": false,
        "gate": "external_write_gate",
        "requiresApproval": true,
        "status": "closed"
      },
      {
        "externalMutation": false,
        "gate": "repair_action_approval",
        "requiresApproval": true,
        "status": "required"
      }
    ],
    "command": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
    "dataBoundaries": [
      {
        "externalMutation": false,
        "name": "preview_only_no_persistence",
        "status": "preview_only"
      },
      {
        "adapterKey": "internal.noop",
        "externalMutation": false,
        "name": "internal_only_outbox",
        "status": "clean"
      },
      {
        "containsPii": false,
        "name": "safe_task_payload",
        "piiIncluded": false,
        "rawPayloadIncluded": false,
        "status": "clean"
      }
    ],
    "docs": [
      {
        "label": "Business Task Handoff",
        "path": "docs/public/BUSINESS_TASK_HANDOFF.md"
      },
      {
        "label": "Workflow Demo",
        "path": "docs/public/WORKFLOW_DEMO.md"
      },
      {
        "label": "Business Intake Pipeline",
        "path": "docs/public/BUSINESS_INTAKE_PIPELINE.md"
      }
    ],
    "notificationDrafts": [
      {
        "body": "deal:DEAL-2026-001 has internal task preview: review_detected_exceptions.",
        "channel": "in_app",
        "containsPii": false,
        "draftId": "task_handoff.in_app.accountant.001",
        "evidence": "business_task_handoff.previewed",
        "externalDelivery": false,
        "recipientRole": "accountant",
        "requiresSecret": false,
        "status": "draft_only",
        "title": "Task handoff ready"
      },
      {
        "body": "deal:DEAL-2026-001 has internal task preview: execute_repair_dry_run.",
        "channel": "in_app",
        "containsPii": false,
        "draftId": "task_handoff.in_app.accountant.002",
        "evidence": "business_task_handoff.previewed",
        "externalDelivery": false,
        "recipientRole": "accountant",
        "requiresSecret": false,
        "status": "draft_only",
        "title": "Task handoff ready"
      }
    ],
    "outboxCandidates": [
      {
        "adapterKey": "internal.noop",
        "containsPii": false,
        "eventType": "task.created",
        "evidence": "business_task_handoff.previewed",
        "externalMutation": false,
        "idempotencyKey": "business-task-handoff:deal:DEAL-2026-001:task-001",
        "payloadProfile": "safe_task_reference",
        "sourceAction": "review_detected_exceptions",
        "status": "would_enqueue"
      },
      {
        "adapterKey": "internal.noop",
        "containsPii": false,
        "eventType": "task.created",
        "evidence": "business_task_handoff.previewed",
        "externalMutation": false,
        "idempotencyKey": "business-task-handoff:deal:DEAL-2026-001:task-002",
        "payloadProfile": "safe_task_reference",
        "sourceAction": "execute_repair_dry_run",
        "status": "would_enqueue"
      }
    ],
    "role": "accountant",
    "status": "previewed",
    "subject": "deal:DEAL-2026-001",
    "summary": [
      {
        "detail": "internal work preview for accountant",
        "label": "Task cards",
        "tone": "blue",
        "value": "2"
      },
      {
        "detail": "task.created candidates only",
        "label": "Internal outbox",
        "tone": "green",
        "value": "2"
      },
      {
        "detail": "in-app drafts, no external send",
        "label": "Draft notifications",
        "tone": "amber",
        "value": "2"
      },
      {
        "detail": "public preview stays internal",
        "label": "External writes",
        "tone": "violet",
        "value": "0"
      }
    ],
    "taskCards": [
      {
        "assigneeRole": "accountant",
        "containsPii": false,
        "due": "next_business_day",
        "evidence": "business_task_handoff.previewed",
        "externalMutation": false,
        "priority": "normal",
        "rawPayloadIncluded": false,
        "requiresApproval": false,
        "sourceAction": "review_detected_exceptions",
        "status": "would_create",
        "subject": "deal:DEAL-2026-001",
        "taskKey": "task.preview.001",
        "title": "review_detected_exceptions",
        "wouldCreate": "BusinessRecord(type=task)"
      },
      {
        "assigneeRole": "accountant",
        "containsPii": false,
        "due": "same_day",
        "evidence": "business_task_handoff.previewed",
        "externalMutation": false,
        "priority": "high",
        "rawPayloadIncluded": false,
        "requiresApproval": true,
        "sourceAction": "execute_repair_dry_run",
        "status": "would_create",
        "subject": "deal:DEAL-2026-001",
        "taskKey": "task.preview.002",
        "title": "execute_repair_dry_run",
        "wouldCreate": "BusinessRecord(type=task)"
      }
    ]
  },
  "connectorFixtureReplay": {
    "boundaries": [
      {
        "detail": "raw_payload_returned=false for every fixture group",
        "evidence": "docs/public/evidence/connector-fixture-replay.sanitized.json",
        "name": "raw payload",
        "state": "not_returned"
      },
      {
        "detail": "credentials_returned=false and provider tokens are excluded",
        "evidence": "examples/connector-fixtures/replay-fixtures.sanitized.json",
        "name": "credentials",
        "state": "not_returned"
      },
      {
        "detail": "external_call_made=false keeps public replay offline",
        "evidence": "CONNECTOR_FIXTURE_REPLAY.md",
        "name": "external calls",
        "state": "disabled"
      },
      {
        "detail": "public_demo_persistence=false keeps replay read-only",
        "evidence": "bash scripts/check_public_connector_fixture_replay.sh",
        "name": "persistence",
        "state": "disabled"
      }
    ],
    "command": "bash scripts/check_public_connector_fixture_replay.sh",
    "docs": [
      {
        "check": "bash scripts/check_public_connector_fixture_replay.sh",
        "label": "Replay path",
        "path": "docs/public/CONNECTOR_FIXTURE_REPLAY.md"
      },
      {
        "check": "public-evidence-index entry",
        "label": "Sanitized evidence",
        "path": "docs/public/evidence/connector-fixture-replay.sanitized.json"
      },
      {
        "check": "fixture_set_id=drivedesk-core-connector-fixture-replay-fixtures",
        "label": "Replay fixtures",
        "path": "examples/connector-fixtures/replay-fixtures.sanitized.json"
      }
    ],
    "evidenceFile": "docs/public/evidence/connector-fixture-replay.sanitized.json",
    "fixtureFile": "examples/connector-fixtures/replay-fixtures.sanitized.json",
    "outcomes": [
      {
        "detail": "Normalizes external_reference, amount_bucket, status, and provider labels.",
        "evidence": "safe_payload_present=true",
        "group": "happy_path_preview",
        "stage": "preview",
        "status": "passed"
      },
      {
        "detail": "Drops access_token, refresh_token, full_name, phone, email, address, and raw body.",
        "evidence": "redaction_evidence_present=true",
        "group": "sensitive_payload_redaction",
        "stage": "redaction",
        "status": "passed"
      },
      {
        "detail": "Rejects malformed input without creating outbox work.",
        "evidence": "outbox_event_created=false",
        "group": "invalid_payload",
        "stage": "validation",
        "status": "blocked"
      },
      {
        "detail": "Classifies temporary provider failure as retryable.",
        "evidence": "next_state=retry_scheduled",
        "group": "retryable_provider_failure",
        "stage": "retry",
        "status": "retry_scheduled"
      },
      {
        "detail": "Routes permanent provider failure into incident-backed operator review.",
        "evidence": "integration.operator_review.created",
        "group": "dead_letter_provider_failure",
        "stage": "operator_review",
        "status": "dead_letter"
      },
      {
        "detail": "Records provider evidence mismatch for manual review.",
        "evidence": "drivedesk_integration_reconciliations",
        "group": "reconciliation_mismatch",
        "stage": "reconciliation",
        "status": "mismatch"
      }
    ],
    "status": "validated",
    "summary": [
      {
        "detail": "happy path, redaction, invalid, retry, dead-letter, reconciliation",
        "label": "Fixture groups",
        "tone": "blue",
        "value": "6"
      },
      {
        "detail": "Replay is contract-only and public-safe",
        "label": "Provider calls",
        "tone": "green",
        "value": "0"
      },
      {
        "detail": "credentials and raw payloads never return to the demo",
        "label": "Secrets",
        "tone": "green",
        "value": "redacted"
      },
      {
        "detail": "dead-letter and mismatch cases route to operator review",
        "label": "Operator path",
        "tone": "amber",
        "value": "review"
      }
    ]
  },
  "dataSource": "static.fallback",
  "domainEvents": [
    {
      "consumer": "workflow.engine",
      "event": "lead.created",
      "producer": "website.adapter",
      "status": "processed"
    },
    {
      "consumer": "audit.log",
      "event": "student.created",
      "producer": "workflow.engine",
      "status": "processed"
    },
    {
      "consumer": "document.archive",
      "event": "contract.generated",
      "producer": "contract.service",
      "status": "processed"
    },
    {
      "consumer": "integration.hub",
      "event": "student.sync.requested",
      "producer": "outbox",
      "status": "pending"
    }
  ],
  "endToEndScenario": {
    "chain": [
      {
        "evidence": "workflow.contract_approved",
        "owner": "Operations",
        "source": "workflowScenarios.scenario-contract-approval-sync",
        "state": "processed",
        "step": "approval",
        "title": "Contract approved"
      },
      {
        "evidence": "notification.manager_signature_task.created",
        "owner": "Workflow engine",
        "source": "workflowScenarios.scenario-signature-task",
        "state": "ready",
        "step": "notification",
        "title": "Manager notification queued"
      },
      {
        "evidence": "integration.accounting_export.requested",
        "owner": "Integration hub",
        "source": "workflowScenarios.scenario-accounting-export",
        "state": "retry",
        "step": "adapter",
        "title": "Accounting export requested"
      },
      {
        "evidence": "integration.incident.status_changed",
        "owner": "Operator",
        "source": "incidentResponse.incidents",
        "state": "acknowledged",
        "step": "incident",
        "title": "Dead-letter incident opened"
      },
      {
        "evidence": "postcheck.gates.passed",
        "owner": "Operator",
        "source": "incidentResponse.recoveryActions",
        "state": "resolved",
        "step": "recovery",
        "title": "Retry and postcheck completed"
      },
      {
        "evidence": "docs/public/ENGINEERING_PROOF.md",
        "owner": "Release gate",
        "source": "engineeringProof.evidence",
        "state": "validated",
        "step": "proof",
        "title": "Public evidence linked"
      }
    ],
    "currentStep": "incident_resolved",
    "id": "scenario-approval-notification-adapter-incident",
    "proof": [
      "workflow.contract_approved",
      "notification.manager_signature_task.created",
      "integration.accounting_export.requested",
      "integration.incident.status_changed",
      "postcheck.gates.passed",
      "docs/public/ENGINEERING_PROOF.md"
    ],
    "status": "reviewable",
    "summary": "Synthetic path from contract approval through notification, adapter export, dead-letter incident, recovery, and public evidence.",
    "title": "Approval to recovery proof"
  },
  "engineeringProof": {
    "evidence": [
      {
        "kind": "doc",
        "path": "docs/public/SYSTEM_REVIEW_PATH.md",
        "summary": "Compact route through public root, demo, API, SDK, operations evidence, release safety, GitOps, OpenTofu, and evidence index",
        "title": "System review path"
      },
      {
        "kind": "doc",
        "path": "docs/public/REVIEWER_QUICKSTART.md",
        "summary": "Timeboxed 5-minute, 15-minute, and 45-minute external verification path",
        "title": "Verification quickstart"
      },
      {
        "kind": "doc",
        "path": "docs/public/PLATFORM_MATURITY_70.md",
        "summary": "Seven evidence groups with executable validation gates",
        "title": "Milestone contract"
      },
      {
        "kind": "doc",
        "path": "docs/public/SANITIZED_EVIDENCE.md",
        "summary": "Runtime, recovery, release, GitOps, and boundary evidence",
        "title": "Sanitized evidence index"
      },
      {
        "kind": "doc",
        "path": "docs/public/SYSTEM_DESIGN.md",
        "summary": "Core architecture, async boundaries, adapters, and observability",
        "title": "System design"
      },
      {
        "kind": "sdk",
        "path": "sdk/generated/public-demo/",
        "summary": "OpenAPI-driven Python, JavaScript, and TypeScript client artifacts",
        "title": "Generated SDK"
      }
    ],
    "gates": [
      {
        "command": "bash scripts/ci_smoke_public.sh",
        "evidence": "API, worker, RBAC, outbox, integration, and observability checks",
        "name": "Core smoke",
        "status": "passed"
      },
      {
        "command": "bash scripts/check_public_demo_api.sh",
        "evidence": "GET /demo/public, OpenAPI, examples, generated clients",
        "name": "Public demo API",
        "status": "passed"
      },
      {
        "command": "bash scripts/check_public_backup_restore.sh",
        "evidence": "backup_sha256_recorded, restore_integrity_ok, counts_match",
        "name": "Backup and restore",
        "status": "passed"
      },
      {
        "command": "bash scripts/check_public_release_rollback.sh && bash scripts/check_public_staged_promotion.sh",
        "evidence": "rollback, canary gate, approval, and promotion history",
        "name": "Release safety",
        "status": "passed"
      },
      {
        "command": "bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_opentofu_plan.sh",
        "evidence": "Helm, Argo CD layout, OpenTofu plan, drift records",
        "name": "GitOps and IaC",
        "status": "passed"
      }
    ],
    "milestone": "engineering_70",
    "status": "validated",
    "summary": [
      {
        "detail": "smoke, release, SDK, and public export gates",
        "label": "CI/CD",
        "tone": "green",
        "value": "green"
      },
      {
        "detail": "health, readiness, metrics, logs, and SLO evidence",
        "label": "Runtime",
        "tone": "blue",
        "value": "observable"
      },
      {
        "detail": "backup, restore, rollback, and staged promotion",
        "label": "Recovery",
        "tone": "violet",
        "value": "drilled"
      },
      {
        "detail": "synthetic data, redacted evidence, no secrets",
        "label": "Boundary",
        "tone": "green",
        "value": "public-safe"
      }
    ],
    "updatedAt": "2026-06-18T10:14:36Z"
  },
  "generatedAt": "2026-06-17T10:55:00Z",
  "health": {
    "api": "ready",
    "database": "online",
    "observability": "validated",
    "worker": "processing"
  },
  "incidentResponse": {
    "incidents": [
      {
        "alert": "DriveDeskIntegrationDeadLetters",
        "evidence": "integration.incident.created",
        "id": "INC-2026-06-18-001",
        "mitigation": "retry blocked until mapping review",
        "owner": "integrations",
        "runbook": "INTEGRATION_INCIDENT_RUNBOOKS.md",
        "severity": "warning",
        "source": "outbox.dead_letter",
        "status": "acknowledged",
        "title": "Integration dead letters require review"
      },
      {
        "alert": "DriveDeskApiHighLatencyP95",
        "evidence": "release.canary_gate.blocked",
        "id": "INC-2026-06-18-002",
        "mitigation": "promotion remains blocked",
        "owner": "platform",
        "runbook": "SLO_CANARY_GATE_EVIDENCE.md",
        "severity": "warning",
        "source": "slo.canary_gate",
        "status": "open",
        "title": "API latency warning during canary"
      },
      {
        "alert": "DriveDeskScheduledValidationMissed",
        "evidence": "integration.incident.status_changed",
        "id": "INC-2026-06-18-003",
        "mitigation": "manual dispatch completed",
        "owner": "platform",
        "runbook": "PRIVATE_INFRA_SCHEDULED_ALERTING.md",
        "severity": "warning",
        "source": "scheduled.validation",
        "status": "resolved",
        "title": "Scheduled validation miss recovered"
      }
    ],
    "recoveryActions": [
      {
        "detail": "Set incident status to acknowledged and keep owner visible",
        "evidence": "integration.incident.status_changed",
        "name": "Acknowledge",
        "owner": "operator",
        "state": "ready"
      },
      {
        "detail": "Review mapping failure and retry only idempotent operation",
        "evidence": "outbox.retry.requested",
        "name": "Mitigate",
        "owner": "integrations",
        "state": "active"
      },
      {
        "detail": "Confirm metrics, logs, and postcheck evidence before resolve",
        "evidence": "postcheck.gates.passed",
        "name": "Verify",
        "owner": "platform",
        "state": "ready"
      },
      {
        "detail": "Attach public-safe evidence and close incident",
        "evidence": "incident.resolved",
        "name": "Resolve",
        "owner": "operator",
        "state": "ready"
      }
    ],
    "resolutionEvidence": [
      {
        "detail": "Status changes are audited",
        "evidence": "integration.incident.status_changed",
        "name": "Audit trail",
        "state": "success"
      },
      {
        "detail": "Incident counts stay aggregate and label-safe",
        "evidence": "drivedesk_integration_incidents",
        "name": "Metric state",
        "state": "success"
      },
      {
        "detail": "Operator has a documented first action",
        "evidence": "INTEGRATION_INCIDENT_RUNBOOKS.md",
        "name": "Runbook link",
        "state": "success"
      },
      {
        "detail": "Release promotion stays blocked while warning is open",
        "evidence": "release.canary_gate.blocked",
        "name": "Rollback path",
        "state": "success"
      },
      {
        "detail": "Resolution requires postcheck evidence",
        "evidence": "postcheck.gates.passed",
        "name": "Postcheck",
        "state": "success"
      }
    ],
    "summary": [
      {
        "detail": "runbook-backed operator queue",
        "label": "Open incidents",
        "tone": "amber",
        "value": "2"
      },
      {
        "detail": "mitigation evidence recorded",
        "label": "Resolved",
        "tone": "green",
        "value": "1"
      },
      {
        "detail": "synthetic acknowledgement target",
        "label": "MTTA",
        "tone": "blue",
        "value": "4m"
      },
      {
        "detail": "audit, metric, runbook, rollback, postcheck",
        "label": "Evidence",
        "tone": "violet",
        "value": "5"
      }
    ],
    "timeline": [
      {
        "actor": "alertmanager",
        "detail": "DriveDeskIntegrationDeadLetters routed to platform-warning-ticket",
        "event": "alert.fired",
        "state": "fired",
        "time": "10:00"
      },
      {
        "actor": "operator",
        "detail": "Owner acknowledged the integration runbook",
        "event": "integration.incident.status_changed",
        "state": "acknowledged",
        "time": "10:04"
      },
      {
        "actor": "operator",
        "detail": "Mapping review and retry boundary checked",
        "event": "runbook.mitigation.started",
        "state": "mitigating",
        "time": "10:11"
      },
      {
        "actor": "system",
        "detail": "Synthetic retry completed with no production data",
        "event": "integration.retry.completed",
        "state": "recovered",
        "time": "10:18"
      },
      {
        "actor": "operator",
        "detail": "Resolution evidence attached to public-safe record",
        "event": "incident.resolved",
        "state": "resolved",
        "time": "10:22"
      }
    ]
  },
  "integrationHealth": [
    {
      "detail": "file.import.fake",
      "label": "Processed jobs",
      "metric": "drivedesk_integration_jobs",
      "state": "processed",
      "value": "1"
    },
    {
      "detail": "temporary provider failure",
      "label": "Retry queue",
      "metric": "drivedesk_integration_job_errors",
      "state": "retry",
      "value": "1"
    },
    {
      "detail": "operator review required",
      "label": "Dead letters",
      "metric": "drivedesk_integration_jobs",
      "state": "dead_letter",
      "value": "1"
    },
    {
      "detail": "last adapter sample",
      "label": "Avg duration",
      "metric": "drivedesk_integration_adapter_duration_milliseconds",
      "state": "observed",
      "value": "12 ms"
    },
    {
      "detail": "provider evidence verified",
      "label": "Reconciliation",
      "metric": "drivedesk_integration_reconciliations",
      "state": "matched",
      "value": "1 match"
    },
    {
      "detail": "runbook-backed operator cards",
      "label": "Open incidents",
      "metric": "drivedesk_integration_incidents",
      "state": "open",
      "value": "2"
    }
  ],
  "integrationJobs": [
    {
      "adapter": "file.import.fake",
      "attempts": 1,
      "event": "integration.file_import.requested",
      "status": "processed",
      "summary": "2 accepted, 1 rejected"
    },
    {
      "adapter": "file.import.fake",
      "attempts": 1,
      "event": "integration.file_import.requested",
      "status": "retry",
      "summary": "temporary provider failure, next retry scheduled"
    },
    {
      "adapter": "file.import.fake",
      "attempts": 1,
      "event": "integration.file_import.requested",
      "status": "dead_letter",
      "summary": "permanent contract failure, operator review required"
    }
  ],
  "integrationReadiness": [
    {
      "name": "File import adapter",
      "progress": 75,
      "state": "active"
    },
    {
      "name": "Payment sandbox adapter",
      "progress": 20,
      "state": "waiting"
    },
    {
      "name": "Accounting export adapter",
      "progress": 55,
      "state": "active"
    },
    {
      "name": "Connection diagnostics",
      "progress": 45,
      "state": "active"
    },
    {
      "name": "Reconciliation evidence",
      "progress": 40,
      "state": "active"
    },
    {
      "name": "Incident runbooks",
      "progress": 35,
      "state": "active"
    },
    {
      "name": "Public demo runtime",
      "progress": 35,
      "state": "active"
    },
    {
      "name": "Alert routing",
      "progress": 45,
      "state": "active"
    }
  ],
  "members": [
    {
      "email": "owner@example.test",
      "name": "Demo Owner",
      "role": "owner",
      "status": "active"
    },
    {
      "email": "ops@example.test",
      "name": "Ops Manager",
      "role": "manager",
      "status": "active"
    },
    {
      "email": "instructor@example.test",
      "name": "Instructor Lead",
      "role": "viewer",
      "status": "active"
    }
  ],
  "metrics": [
    {
      "detail": "private smoke tests",
      "label": "API checks",
      "tone": "blue",
      "value": "48"
    },
    {
      "detail": "GitHub Actions",
      "label": "Public CI",
      "tone": "green",
      "value": "green"
    },
    {
      "detail": "generated contract",
      "label": "OpenAPI paths",
      "tone": "violet",
      "value": "48"
    },
    {
      "detail": "lead to sync",
      "label": "Workflow stages",
      "tone": "green",
      "value": "5"
    },
    {
      "detail": "retry queue",
      "label": "Pending events",
      "tone": "amber",
      "value": "1"
    }
  ],
  "outbox": [
    {
      "attempts": 1,
      "event": "tenant.created",
      "status": "processed"
    },
    {
      "attempts": 1,
      "event": "membership.created",
      "status": "processed"
    },
    {
      "attempts": 1,
      "event": "integration.file_import.requested",
      "status": "processed"
    },
    {
      "attempts": 0,
      "event": "integration.provider.sync",
      "status": "pending"
    },
    {
      "attempts": 0,
      "event": "student.sync.requested",
      "status": "pending"
    }
  ],
  "recoveryEvidence": [
    {
      "detail": "temporary SQLite backup artifact created",
      "evidence": "backup_sha256_recorded",
      "name": "Synthetic backup",
      "state": "success"
    },
    {
      "detail": "restored into a separate temporary database",
      "evidence": "restore_integrity_ok",
      "name": "Restore drill",
      "state": "success"
    },
    {
      "detail": "core tables and row counts matched after restore",
      "evidence": "counts_match",
      "name": "Schema contract",
      "state": "success"
    },
    {
      "detail": "synthetic demo data only",
      "evidence": "production_data_touched_false",
      "name": "Data boundary",
      "state": "success"
    },
    {
      "detail": "bad candidate release rolled back to stable",
      "evidence": "release.rollback.executed",
      "name": "Release rollback",
      "state": "success"
    },
    {
      "detail": "stable release healthy after rollback",
      "evidence": "stable_release_healthy_after_rollback",
      "name": "Stable after rollback",
      "state": "success"
    },
    {
      "detail": "candidate release blocked before promotion",
      "evidence": "release.canary_gate.blocked",
      "name": "SLO canary gate",
      "state": "success"
    },
    {
      "detail": "availability, latency, and burn-rate violations detected",
      "evidence": "promotion_blocked",
      "name": "Promotion blocked",
      "state": "success"
    },
    {
      "detail": "synthetic candidate exceeded the burn-rate threshold",
      "evidence": "burn_rate_violation_detected",
      "name": "Error budget burn",
      "state": "success"
    },
    {
      "detail": "safe release promoted through build, staging, canary, and production",
      "evidence": "release.staged_promotion.completed",
      "name": "Staged promotion",
      "state": "success"
    },
    {
      "detail": "synthetic production approval recorded before promotion",
      "evidence": "production_approval_recorded",
      "name": "Production approval",
      "state": "success"
    },
    {
      "detail": "promotion history hash recorded for auditability",
      "evidence": "promotion_history_hash_recorded",
      "name": "Promotion history",
      "state": "success"
    },
    {
      "detail": "private staging runtime evidence is collected through public-safe contracts",
      "evidence": "runtime.rollout.evidence_collected",
      "name": "Runtime rollout",
      "state": "success"
    },
    {
      "detail": "private staging checks stay behind a loopback-only public boundary",
      "evidence": "loopback_boundary_recorded",
      "name": "Loopback boundary",
      "state": "success"
    },
    {
      "detail": "read-only private infra validation evidence is recorded",
      "evidence": "infra.private_state.validated",
      "name": "Private state validation",
      "state": "success"
    },
    {
      "detail": "validation records that no runtime mutation was performed",
      "evidence": "no_runtime_mutation_recorded",
      "name": "No runtime mutation",
      "state": "success"
    },
    {
      "detail": "drift remediation is planned with operator review before apply",
      "evidence": "infra.remediation.plan.ready",
      "name": "Remediation plan",
      "state": "success"
    },
    {
      "detail": "remediation plan includes rollback context",
      "evidence": "rollback_attached",
      "name": "Rollback attached",
      "state": "success"
    },
    {
      "detail": "reviewed private staging remediation execution is recorded",
      "evidence": "infra.remediation.execution.completed",
      "name": "Remediation execution",
      "state": "success"
    },
    {
      "detail": "postcheck validation is recorded after remediation execution",
      "evidence": "post_remediation_validation_recorded",
      "name": "Post-remediation validation",
      "state": "success"
    },
    {
      "detail": "read-only drift refresh shows clean state after remediation",
      "evidence": "infra.post_remediation_drift.clean",
      "name": "Post-remediation drift",
      "state": "success"
    },
    {
      "detail": "post-remediation refresh records no residual drift",
      "evidence": "no_residual_drift_recorded",
      "name": "No residual drift",
      "state": "success"
    },
    {
      "detail": "daily public-safe validation workflow is recorded",
      "evidence": "infra.scheduled_validation.healthy",
      "name": "Scheduled validation",
      "state": "success"
    },
    {
      "detail": "missed scheduled checks require operator review",
      "evidence": "missed_run_guard_recorded",
      "name": "Missed-run guard",
      "state": "success"
    },
    {
      "detail": "failed or missed scheduled checks produce runbook-backed alert evidence",
      "evidence": "infra.scheduled_validation.alerting.ready",
      "name": "Scheduled alerting",
      "state": "success"
    },
    {
      "detail": "workflow failures upload a public-safe alert artifact",
      "evidence": "public-scheduled-validation-alert",
      "name": "Failure artifact",
      "state": "success"
    }
  ],
  "schemaVersion": 1,
  "tenant": {
    "name": "DriveDesk Demo Academy",
    "plan": "Core Preview",
    "slug": "demo-academy",
    "status": "active"
  },
  "timeline": [
    {
      "actor": "website.adapter",
      "detail": "Synthetic website form normalized into a DriveDesk lead.",
      "event": "lead.created",
      "time": "09:16",
      "title": "Lead captured"
    },
    {
      "actor": "front_desk",
      "detail": "Front desk accepted the lead and opened a student record.",
      "event": "student.created",
      "time": "09:18",
      "title": "Lead converted"
    },
    {
      "actor": "contract.service",
      "detail": "Contract draft attached to the synthetic student workflow.",
      "event": "contract.generated",
      "time": "09:21",
      "title": "Contract generated"
    },
    {
      "actor": "audit",
      "detail": "Workflow state change recorded for review.",
      "event": "audit.recorded",
      "time": "09:22",
      "title": "Audit trail written"
    },
    {
      "actor": "outbox",
      "detail": "Integration event queued for a future external system adapter.",
      "event": "student.sync.requested",
      "time": "09:22",
      "title": "Sync queued"
    }
  ],
  "workQueue": [
    {
      "id": "DD-TASK-101",
      "owner": "Front desk",
      "priority": "high",
      "status": "in review",
      "title": "Review new learner intake"
    },
    {
      "id": "DD-TASK-102",
      "owner": "Ops manager",
      "priority": "medium",
      "status": "planned",
      "title": "Prepare instructor schedule sync"
    },
    {
      "id": "DD-TASK-103",
      "owner": "Finance",
      "priority": "medium",
      "status": "blocked",
      "title": "Check payment adapter sandbox"
    },
    {
      "id": "DD-TASK-104",
      "owner": "Platform",
      "priority": "low",
      "status": "done",
      "title": "Publish demo evidence package"
    }
  ],
  "workflow": {
    "currentStage": "student_sync",
    "id": "wf-demo-lead-to-student",
    "owner": "Front desk",
    "stages": [
      {
        "evidence": "lead.created",
        "key": "lead_created",
        "label": "Lead captured",
        "owner": "Website adapter",
        "state": "done"
      },
      {
        "evidence": "student.created",
        "key": "student_created",
        "label": "Student record",
        "owner": "Front desk",
        "state": "done"
      },
      {
        "evidence": "contract.generated",
        "key": "contract_ready",
        "label": "Contract prepared",
        "owner": "Operations",
        "state": "done"
      },
      {
        "evidence": "audit.recorded",
        "key": "audit_recorded",
        "label": "Audit recorded",
        "owner": "Core API",
        "state": "done"
      },
      {
        "evidence": "student.sync.requested",
        "key": "student_sync",
        "label": "External sync queued",
        "owner": "Outbox worker",
        "state": "current"
      }
    ],
    "summary": "Synthetic intake flow that turns a lead into a student record, contract, audit trail, and integration event.",
    "title": "Lead to enrolled student"
  },
  "workflowScenarios": [
    {
      "actionType": "emit_outbox_event",
      "detail": "Approved contract emits an outbox event for downstream document and accounting adapters.",
      "evidence": "workflow.contract_approved",
      "id": "scenario-contract-approval-sync",
      "outputs": [
        "audit_event",
        "outbox_event",
        "action_run"
      ],
      "owner": "Operations",
      "status": "processed",
      "title": "Contract approval sync",
      "trigger": "business_record.status_changed contract:draft->approved"
    },
    {
      "actionType": "create_task_record",
      "detail": "A staff task is created so the contract cannot silently wait for a manual signature step.",
      "evidence": "workflow.task_record.created",
      "id": "scenario-signature-task",
      "outputs": [
        "audit_event",
        "task_record",
        "action_run"
      ],
      "owner": "Front desk",
      "status": "ready",
      "title": "Signature task creation",
      "trigger": "business_record.status_changed contract:approved->signature_required"
    },
    {
      "actionType": "request_adapter_sync",
      "detail": "Billing-ready contracts request an adapter operation with retry, idempotency, and review evidence.",
      "evidence": "workflow.contract_sync.requested",
      "id": "scenario-accounting-export",
      "outputs": [
        "outbox_event",
        "integration_job",
        "action_run"
      ],
      "owner": "Finance",
      "status": "pending",
      "title": "Accounting export request",
      "trigger": "business_record.status_changed contract:approved->ready_for_billing"
    }
  ]
};
