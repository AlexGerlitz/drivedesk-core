window.DRIVEDESK_DEMO_DATA = {
  "schemaVersion": 1,
  "generatedAt": "2026-06-17T10:55:00Z",
  "dataSource": "static.fallback",
  "apiContract": {
    "path": "/demo/public",
    "mode": "read_only",
    "data_profile": "synthetic_demo_data",
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
      "value": "48",
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
      "value": "48",
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
      "key": "accounting.export.mock",
      "name": "Mock Accounting Export",
      "status": "active",
      "direction": "outbound",
      "connectionProfileSupported": true,
      "requiredMappingKeys": [],
      "supportedConnectionScopes": [
        "accounting:export"
      ],
      "defaultConnectionScopes": [
        "accounting:export"
      ],
      "operationContracts": [
        {
          "key": "accounting_export_execute",
          "title": "Export accounting documents",
          "trigger": "api.outbox.enqueue",
          "eventType": "accounting.export.requested",
          "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
          "requiredConnectionScope": "accounting:export",
          "idempotencyKeys": [
            "tenant_id",
            "export_batch_id",
            "documents_hash"
          ],
          "retryable": true,
          "deadLetter": true,
          "operatorReview": true
        }
      ],
      "authProfile": {
        "mode": "mock_outbound_boundary",
        "publicDemoRequiresSecret": false,
        "realProviderRequiresSecret": true,
        "secretRefs": [
          "ACCOUNTING_PROVIDER_API_KEY",
          "ACCOUNTING_PROVIDER_ENDPOINT"
        ],
        "credentialPlacement": "server_secret_store",
        "tokenExchange": "private_connector_only",
        "externalTokenExchange": false,
        "dataBoundaries": [
          "no_public_secrets",
          "server_side_provider_calls_only"
        ]
      },
      "contract": "Export synthetic accounting documents through the shared outbox adapter boundary."
    },
    {
      "key": "crm.bitrix24.mock",
      "name": "Mock Bitrix24 CRM Intake",
      "status": "active",
      "direction": "inbound",
      "connectionProfileSupported": true,
      "requiredMappingKeys": [
        "deal_id",
        "source_state"
      ],
      "supportedConnectionScopes": [
        "crm:deal.ingest",
        "crm:deal.preview"
      ],
      "defaultConnectionScopes": [
        "crm:deal.ingest",
        "crm:deal.preview"
      ],
      "operationContracts": [
        {
          "key": "crm_deal_intake_preview",
          "title": "Preview CRM deal intake",
          "trigger": "api.request",
          "eventType": "business_provider_intake.previewed",
          "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
          "requiredConnectionScope": "crm:deal.preview",
          "idempotencyKeys": [
            "tenant_id",
            "provider_key",
            "subject_ref",
            "payload_hash"
          ],
          "retryable": false,
          "deadLetter": false,
          "operatorReview": false
        },
        {
          "key": "crm_deal_ingest_execute",
          "title": "Queue CRM deal intake",
          "trigger": "api.outbox.enqueue",
          "eventType": "integration.crm_deal.ingest.requested",
          "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
          "requiredConnectionScope": "crm:deal.ingest",
          "idempotencyKeys": [
            "tenant_id",
            "batch_id",
            "deals_hash"
          ],
          "retryable": true,
          "deadLetter": true,
          "operatorReview": true
        }
      ],
      "authProfile": {
        "mode": "oauth2_or_webhook_boundary",
        "publicDemoRequiresSecret": false,
        "realProviderRequiresSecret": true,
        "secretRefs": [
          "BITRIX24_WEBHOOK_URL",
          "BITRIX24_CLIENT_SECRET"
        ],
        "credentialPlacement": "server_secret_store",
        "tokenExchange": "private_connector_only",
        "externalTokenExchange": false,
        "dataBoundaries": [
          "no_public_secrets",
          "no_browser_token_storage",
          "server_side_provider_calls_only"
        ]
      },
      "contract": "Normalize synthetic CRM deal facts into safe DriveDesk observations without calling a real CRM provider."
    },
    {
      "key": "file.import.fake",
      "name": "Synthetic File Import",
      "status": "active",
      "direction": "inbound",
      "connectionProfileSupported": true,
      "requiredMappingKeys": [
        "external_id",
        "display_name"
      ],
      "supportedConnectionScopes": [
        "file_import:execute",
        "file_import:preview"
      ],
      "defaultConnectionScopes": [
        "file_import:execute",
        "file_import:preview"
      ],
      "operationContracts": [
        {
          "key": "file_import_preview",
          "title": "Preview mapped import rows",
          "trigger": "api.request",
          "eventType": "integration.mapping_preview.requested",
          "endpoint": "POST /tenants/{tenant_id}/integration-mapping-preview",
          "requiredConnectionScope": "file_import:preview",
          "idempotencyKeys": [
            "tenant_id",
            "integration_connection_id",
            "records_hash"
          ],
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
          "idempotencyKeys": [
            "tenant_id",
            "source_name",
            "source_format",
            "records_hash"
          ],
          "retryable": true,
          "deadLetter": true,
          "operatorReview": true
        }
      ],
      "authProfile": {
        "mode": "local_file_boundary",
        "publicDemoRequiresSecret": false,
        "realProviderRequiresSecret": false,
        "secretRefs": [],
        "credentialPlacement": "none",
        "tokenExchange": "none",
        "externalTokenExchange": false,
        "dataBoundaries": [
          "no_public_secrets",
          "tenant_owned_mapping_only"
        ]
      },
      "contract": "Normalize synthetic imported rows and report accepted or rejected records."
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
          "idempotencyKeys": [
            "outbox_event.id"
          ],
          "retryable": false,
          "deadLetter": false,
          "operatorReview": false
        }
      ],
      "authProfile": {
        "mode": "none",
        "publicDemoRequiresSecret": false,
        "realProviderRequiresSecret": false,
        "secretRefs": [],
        "credentialPlacement": "none",
        "tokenExchange": "none",
        "externalTokenExchange": false,
        "dataBoundaries": [
          "internal_event_only"
        ]
      },
      "contract": "Acknowledge internal domain events without calling an external provider."
    }
  ],
  "adapterScenarios": [
    {
      "id": "adapter-file-import-preview",
      "title": "File import mapping preview",
      "adapter": "file.import.fake",
      "operation": "file_import_preview",
      "phase": "preview",
      "endpoint": "POST /tenants/{tenant_id}/integration-mapping-preview",
      "requiredScope": "file_import:preview",
      "status": "processed",
      "detail": "Tenant mapping is validated against sample records before any outbox event is created.",
      "inputs": [
        "connection_profile",
        "mapping",
        "records"
      ],
      "outputs": [
        "mapping_preview",
        "validation_errors",
        "no_outbox_event"
      ],
      "evidence": "integration.mapping_preview.completed"
    },
    {
      "id": "adapter-file-import-execute",
      "title": "File import execution",
      "adapter": "file.import.fake",
      "operation": "file_import_execute",
      "phase": "execute",
      "endpoint": "POST /tenants/{tenant_id}/integration-imports/file",
      "requiredScope": "file_import:execute",
      "status": "processed",
      "detail": "Accepted records are queued through the outbox with idempotency keys and an audit event.",
      "inputs": [
        "source_name",
        "source_format",
        "records_hash"
      ],
      "outputs": [
        "outbox_event",
        "adapter_job",
        "audit_event"
      ],
      "evidence": "integration.file_import.requested"
    },
    {
      "id": "adapter-crm-deal-preview",
      "title": "CRM deal intake preview",
      "adapter": "crm.bitrix24.mock",
      "operation": "crm_deal_intake_preview",
      "phase": "preview",
      "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "requiredScope": "crm:deal.preview",
      "status": "mapped",
      "detail": "Bitrix-style CRM deal data is mapped into a safe provider intake preview before DriveDesk records any business state.",
      "inputs": [
        "provider_key",
        "subject_ref",
        "payload_hash"
      ],
      "outputs": [
        "safe_payload",
        "normalized_observation",
        "no_provider_call"
      ],
      "evidence": "business_provider_intake.previewed"
    },
    {
      "id": "adapter-crm-deal-ingest",
      "title": "CRM deal intake queue",
      "adapter": "crm.bitrix24.mock",
      "operation": "crm_deal_ingest_execute",
      "phase": "execute",
      "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
      "requiredScope": "crm:deal.ingest",
      "status": "pending",
      "detail": "Accepted CRM facts are queued through the outbox for retryable worker execution.",
      "inputs": [
        "batch_id",
        "deals_hash",
        "idempotency_key"
      ],
      "outputs": [
        "outbox_event",
        "adapter_job",
        "redaction_evidence"
      ],
      "evidence": "integration.crm_deal.ingest.requested"
    },
    {
      "id": "adapter-accounting-export-retry",
      "title": "Accounting export retry",
      "adapter": "accounting.export.mock",
      "operation": "accounting_export_execute",
      "phase": "retry",
      "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
      "requiredScope": "accounting:export",
      "status": "retry",
      "detail": "Temporary provider failure keeps the job retryable and visible to operations.",
      "inputs": [
        "export_batch_id",
        "documents_hash",
        "idempotency_key"
      ],
      "outputs": [
        "retry_scheduled",
        "attempt_count",
        "operator_visible_status"
      ],
      "evidence": "integration.export.retry_scheduled"
    },
    {
      "id": "adapter-dead-letter-review",
      "title": "Dead-letter operator review",
      "adapter": "file.import.fake",
      "operation": "file_import_execute",
      "phase": "operator_review",
      "endpoint": "GET /tenants/{tenant_id}/integration-operator-review",
      "requiredScope": "file_import:execute",
      "status": "dead_letter",
      "detail": "Permanent contract failure creates a review card with runbook context and a manual retry endpoint.",
      "inputs": [
        "outbox_event",
        "last_error",
        "payload_summary"
      ],
      "outputs": [
        "review_card",
        "runbook",
        "manual_retry_endpoint"
      ],
      "evidence": "integration.operator_review.created"
    }
  ],
  "adapterStudio": {
    "summary": [
      {
        "label": "SDK plans",
        "value": "6",
        "detail": "Contract-only adapter operations",
        "tone": "blue"
      },
      {
        "label": "CRM preview",
        "value": "safe",
        "detail": "Redacted Bitrix-style provider intake",
        "tone": "green"
      },
      {
        "label": "Worker ingest",
        "value": "outbox",
        "detail": "Server-side retry boundary",
        "tone": "violet"
      },
      {
        "label": "Secrets",
        "value": "server",
        "detail": "No browser token storage",
        "tone": "amber"
      }
    ],
    "flow": [
      {
        "step": "1",
        "name": "Runtime catalog",
        "state": "ready",
        "detail": "GET /integration-adapters exposes crm.bitrix24.mock descriptors, auth_profile, scopes, and operation contracts.",
        "evidence": "GET /integration-adapters"
      },
      {
        "step": "2",
        "name": "SDK operation plan",
        "state": "contract_only",
        "detail": "Generated Python and JavaScript SDK builds adapter-crm-deal-preview and adapter-crm-deal-ingest request plans without live provider writes.",
        "evidence": "sdk/generated/public-demo/"
      },
      {
        "step": "3",
        "name": "Preview boundary",
        "state": "preview_only",
        "detail": "CRM payload is normalized through business-provider-intake preview; raw payload, phone, full_name, and access_token are dropped.",
        "evidence": "business_provider_intake.previewed"
      },
      {
        "step": "4",
        "name": "Worker ingest",
        "state": "queued",
        "detail": "Accepted CRM facts become integration.crm_deal.ingest.requested and are handled by worker:drivedesk_worker.main.process_pending_outbox.",
        "evidence": "integration.crm_deal.ingest.requested"
      },
      {
        "step": "5",
        "name": "Diagnostics and review",
        "state": "observable",
        "detail": "Connection checks, reconciliations, incident cards, retry, dead-letter, and operator_review make failures recoverable.",
        "evidence": "drivedesk_integration_incidents"
      }
    ],
    "operationPlans": [
      {
        "scenarioId": "adapter-crm-deal-preview",
        "adapter": "crm.bitrix24.mock",
        "operation": "crm_deal_intake_preview",
        "method": "POST",
        "endpoint": "POST /tenants/{tenant_id}/business-provider-intake/preview",
        "scope": "crm:deal.preview",
        "executionMode": "contract_only",
        "safeToRunAgainstPublicDemo": false,
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
        "evidence": "business_provider_intake.previewed"
      },
      {
        "scenarioId": "adapter-crm-deal-ingest",
        "adapter": "crm.bitrix24.mock",
        "operation": "crm_deal_ingest_execute",
        "method": "WORKER",
        "endpoint": "worker:drivedesk_worker.main.process_pending_outbox",
        "scope": "crm:deal.ingest",
        "executionMode": "contract_only",
        "safeToRunAgainstPublicDemo": false,
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
        "evidence": "integration.crm_deal.ingest.requested"
      }
    ],
    "boundaries": [
      {
        "name": "auth_profile",
        "state": "server_only",
        "detail": "oauth2_or_webhook_boundary keeps token exchange in private connector code.",
        "evidence": "server_secret_store"
      },
      {
        "name": "browser token boundary",
        "state": "clean",
        "detail": "no_browser_token_storage and server_side_provider_calls_only prevent provider tokens from entering the public UI.",
        "evidence": "private_connector_only"
      },
      {
        "name": "redaction",
        "state": "clean",
        "detail": "safe_payload excludes access_token, full_name, phone, raw provider payload, and tenant secrets.",
        "evidence": "redaction_evidence"
      },
      {
        "name": "public run mode",
        "state": "contract_only",
        "detail": "Public demo never calls Bitrix, bank, accounting, Telegram, email, or provider APIs.",
        "evidence": "safeToRunAgainstPublicDemo=false"
      }
    ],
    "diagnostics": [
      {
        "name": "Connection checks",
        "state": "passed",
        "metric": "drivedesk_integration_connection_checks",
        "detail": "Provider readiness without raw payloads"
      },
      {
        "name": "Reconciliation",
        "state": "matched",
        "metric": "drivedesk_integration_reconciliations",
        "detail": "Provider evidence comparison"
      },
      {
        "name": "Incident cards",
        "state": "open",
        "metric": "drivedesk_integration_incidents",
        "detail": "Runbook-backed operator flow"
      },
      {
        "name": "Dead-letter review",
        "state": "ready",
        "metric": "integration.operator_review.created",
        "detail": "Manual review for failed jobs"
      }
    ],
    "docs": [
      {
        "label": "Adapter developer guide",
        "path": "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
        "check": "bash scripts/check_public_adapter_developer_guide.sh"
      },
      {
        "label": "Generated SDK",
        "path": "docs/public/CLIENT_SDK.md",
        "check": "bash scripts/check_public_demo_sdk.sh"
      },
      {
        "label": "Provider connector guide",
        "path": "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
        "check": "bash scripts/check_public_provider_connector_guide.sh"
      }
    ]
  },
  "connectorFixtureReplay": {
    "status": "validated",
    "command": "bash scripts/check_public_connector_fixture_replay.sh",
    "fixtureFile": "examples/connector-fixtures/replay-fixtures.sanitized.json",
    "evidenceFile": "docs/public/evidence/connector-fixture-replay.sanitized.json",
    "summary": [
      {
        "label": "Fixture groups",
        "value": "6",
        "detail": "happy path, redaction, invalid, retry, dead-letter, reconciliation",
        "tone": "blue"
      },
      {
        "label": "Provider calls",
        "value": "0",
        "detail": "Replay is contract-only and public-safe",
        "tone": "green"
      },
      {
        "label": "Secrets",
        "value": "redacted",
        "detail": "credentials and raw payloads never return to the demo",
        "tone": "green"
      },
      {
        "label": "Operator path",
        "value": "review",
        "detail": "dead-letter and mismatch cases route to operator review",
        "tone": "amber"
      }
    ],
    "outcomes": [
      {
        "group": "happy_path_preview",
        "stage": "preview",
        "status": "passed",
        "detail": "Normalizes external_reference, amount_bucket, status, and provider labels.",
        "evidence": "safe_payload_present=true"
      },
      {
        "group": "sensitive_payload_redaction",
        "stage": "redaction",
        "status": "passed",
        "detail": "Drops access_token, refresh_token, full_name, phone, email, address, and raw body.",
        "evidence": "redaction_evidence_present=true"
      },
      {
        "group": "invalid_payload",
        "stage": "validation",
        "status": "blocked",
        "detail": "Rejects malformed input without creating outbox work.",
        "evidence": "outbox_event_created=false"
      },
      {
        "group": "retryable_provider_failure",
        "stage": "retry",
        "status": "retry_scheduled",
        "detail": "Classifies temporary provider failure as retryable.",
        "evidence": "next_state=retry_scheduled"
      },
      {
        "group": "dead_letter_provider_failure",
        "stage": "operator_review",
        "status": "dead_letter",
        "detail": "Routes permanent provider failure into incident-backed operator review.",
        "evidence": "integration.operator_review.created"
      },
      {
        "group": "reconciliation_mismatch",
        "stage": "reconciliation",
        "status": "mismatch",
        "detail": "Records provider evidence mismatch for manual review.",
        "evidence": "drivedesk_integration_reconciliations"
      }
    ],
    "boundaries": [
      {
        "name": "raw payload",
        "state": "not_returned",
        "detail": "raw_payload_returned=false for every fixture group",
        "evidence": "docs/public/evidence/connector-fixture-replay.sanitized.json"
      },
      {
        "name": "credentials",
        "state": "not_returned",
        "detail": "credentials_returned=false and provider tokens are excluded",
        "evidence": "examples/connector-fixtures/replay-fixtures.sanitized.json"
      },
      {
        "name": "external calls",
        "state": "disabled",
        "detail": "external_call_made=false keeps public replay offline",
        "evidence": "CONNECTOR_FIXTURE_REPLAY.md"
      },
      {
        "name": "persistence",
        "state": "disabled",
        "detail": "public_demo_persistence=false keeps replay read-only",
        "evidence": "bash scripts/check_public_connector_fixture_replay.sh"
      }
    ],
    "docs": [
      {
        "label": "Replay path",
        "path": "docs/public/CONNECTOR_FIXTURE_REPLAY.md",
        "check": "bash scripts/check_public_connector_fixture_replay.sh"
      },
      {
        "label": "Sanitized evidence",
        "path": "docs/public/evidence/connector-fixture-replay.sanitized.json",
        "check": "public-evidence-index entry"
      },
      {
        "label": "Replay fixtures",
        "path": "examples/connector-fixtures/replay-fixtures.sanitized.json",
        "check": "fixture_set_id=drivedesk-core-connector-fixture-replay-fixtures"
      }
    ]
  },
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
    },
    {
      "name": "Alert routing",
      "state": "active",
      "progress": 45
    }
  ],
  "alertRouting": {
    "summary": [
      {
        "label": "Routes",
        "value": "3",
        "detail": "critical, warning, scheduled validation",
        "tone": "blue"
      },
      {
        "label": "Receivers",
        "value": "3",
        "detail": "page, chat, ticket queue",
        "tone": "green"
      },
      {
        "label": "Bound alerts",
        "value": "5",
        "detail": "runbook-backed signals",
        "tone": "violet"
      },
      {
        "label": "Escalation",
        "value": "15m",
        "detail": "critical route to ticket queue",
        "tone": "amber"
      }
    ],
    "routes": [
      {
        "name": "platform-critical-page",
        "match": "severity=critical",
        "receiver": "public-oncall-page",
        "repeat": "30m",
        "escalation": "15m",
        "artifact": "public-alert-routing-artifact",
        "state": "active"
      },
      {
        "name": "platform-warning-ticket",
        "match": "severity=warning",
        "receiver": "public-ticket-queue",
        "repeat": "240m",
        "escalation": "60m",
        "artifact": "public-alert-routing-artifact",
        "state": "active"
      },
      {
        "name": "scheduled-validation-notice",
        "match": "service=scheduled-validation",
        "receiver": "public-chat-notice",
        "repeat": "180m",
        "escalation": "45m",
        "artifact": "public-scheduled-validation-alert",
        "state": "active"
      }
    ],
    "bindings": [
      {
        "alert": "DriveDeskApiTargetDown",
        "severity": "critical",
        "service": "api",
        "route": "platform-critical-page",
        "owner": "platform",
        "runbook": "RUNTIME_ROLLOUT_EVIDENCE.md",
        "dedupe": "alertname:service:stage",
        "state": "routed"
      },
      {
        "alert": "DriveDeskApiHighLatencyP95",
        "severity": "warning",
        "service": "api",
        "route": "platform-warning-ticket",
        "owner": "platform",
        "runbook": "SLO_CANARY_GATE_EVIDENCE.md",
        "dedupe": "alertname:service:stage",
        "state": "routed"
      },
      {
        "alert": "DriveDeskIntegrationDeadLetters",
        "severity": "warning",
        "service": "integrations",
        "route": "platform-warning-ticket",
        "owner": "integrations",
        "runbook": "INTEGRATION_INCIDENT_RUNBOOKS.md",
        "dedupe": "alertname:service:stage",
        "state": "routed"
      },
      {
        "alert": "DriveDeskAuthFailureSpike",
        "severity": "critical",
        "service": "auth",
        "route": "platform-critical-page",
        "owner": "security",
        "runbook": "AUTH_OBSERVABILITY.md",
        "dedupe": "alertname:service:stage",
        "state": "routed"
      },
      {
        "alert": "DriveDeskScheduledValidationMissed",
        "severity": "warning",
        "service": "scheduled-validation",
        "route": "scheduled-validation-notice",
        "owner": "platform",
        "runbook": "PRIVATE_INFRA_SCHEDULED_ALERTING.md",
        "dedupe": "alertname:service",
        "state": "routed"
      }
    ],
    "runbookActions": [
      {
        "name": "First response",
        "detail": "Open the public runbook and inspect the sanitized evidence artifact.",
        "state": "ready",
        "evidence": "ALERT_ROUTING_EVIDENCE.md"
      },
      {
        "name": "Escalation path",
        "detail": "Critical alerts escalate to the ticket queue after 15 minutes.",
        "state": "ready",
        "evidence": "public-ticket-queue"
      },
      {
        "name": "Silence contract",
        "detail": "Maintenance silences require alertname, service, stage, and an expiry.",
        "state": "ready",
        "evidence": "alert.silence.created"
      }
    ]
  },
  "incidentResponse": {
    "summary": [
      {
        "label": "Open incidents",
        "value": "2",
        "detail": "runbook-backed operator queue",
        "tone": "amber"
      },
      {
        "label": "Resolved",
        "value": "1",
        "detail": "mitigation evidence recorded",
        "tone": "green"
      },
      {
        "label": "MTTA",
        "value": "4m",
        "detail": "synthetic acknowledgement target",
        "tone": "blue"
      },
      {
        "label": "Evidence",
        "value": "5",
        "detail": "audit, metric, runbook, rollback, postcheck",
        "tone": "violet"
      }
    ],
    "incidents": [
      {
        "id": "INC-2026-06-18-001",
        "title": "Integration dead letters require review",
        "status": "acknowledged",
        "severity": "warning",
        "owner": "integrations",
        "alert": "DriveDeskIntegrationDeadLetters",
        "runbook": "INTEGRATION_INCIDENT_RUNBOOKS.md",
        "source": "outbox.dead_letter",
        "mitigation": "retry blocked until mapping review",
        "evidence": "integration.incident.created"
      },
      {
        "id": "INC-2026-06-18-002",
        "title": "API latency warning during canary",
        "status": "open",
        "severity": "warning",
        "owner": "platform",
        "alert": "DriveDeskApiHighLatencyP95",
        "runbook": "SLO_CANARY_GATE_EVIDENCE.md",
        "source": "slo.canary_gate",
        "mitigation": "promotion remains blocked",
        "evidence": "release.canary_gate.blocked"
      },
      {
        "id": "INC-2026-06-18-003",
        "title": "Scheduled validation miss recovered",
        "status": "resolved",
        "severity": "warning",
        "owner": "platform",
        "alert": "DriveDeskScheduledValidationMissed",
        "runbook": "PRIVATE_INFRA_SCHEDULED_ALERTING.md",
        "source": "scheduled.validation",
        "mitigation": "manual dispatch completed",
        "evidence": "integration.incident.status_changed"
      }
    ],
    "timeline": [
      {
        "time": "10:00",
        "actor": "alertmanager",
        "state": "fired",
        "event": "alert.fired",
        "detail": "DriveDeskIntegrationDeadLetters routed to platform-warning-ticket"
      },
      {
        "time": "10:04",
        "actor": "operator",
        "state": "acknowledged",
        "event": "integration.incident.status_changed",
        "detail": "Owner acknowledged the integration runbook"
      },
      {
        "time": "10:11",
        "actor": "operator",
        "state": "mitigating",
        "event": "runbook.mitigation.started",
        "detail": "Mapping review and retry boundary checked"
      },
      {
        "time": "10:18",
        "actor": "system",
        "state": "recovered",
        "event": "integration.retry.completed",
        "detail": "Synthetic retry completed with no production data"
      },
      {
        "time": "10:22",
        "actor": "operator",
        "state": "resolved",
        "event": "incident.resolved",
        "detail": "Resolution evidence attached to public-safe record"
      }
    ],
    "recoveryActions": [
      {
        "name": "Acknowledge",
        "state": "ready",
        "owner": "operator",
        "detail": "Set incident status to acknowledged and keep owner visible",
        "evidence": "integration.incident.status_changed"
      },
      {
        "name": "Mitigate",
        "state": "active",
        "owner": "integrations",
        "detail": "Review mapping failure and retry only idempotent operation",
        "evidence": "outbox.retry.requested"
      },
      {
        "name": "Verify",
        "state": "ready",
        "owner": "platform",
        "detail": "Confirm metrics, logs, and postcheck evidence before resolve",
        "evidence": "postcheck.gates.passed"
      },
      {
        "name": "Resolve",
        "state": "ready",
        "owner": "operator",
        "detail": "Attach public-safe evidence and close incident",
        "evidence": "incident.resolved"
      }
    ],
    "resolutionEvidence": [
      {
        "name": "Audit trail",
        "state": "success",
        "detail": "Status changes are audited",
        "evidence": "integration.incident.status_changed"
      },
      {
        "name": "Metric state",
        "state": "success",
        "detail": "Incident counts stay aggregate and label-safe",
        "evidence": "drivedesk_integration_incidents"
      },
      {
        "name": "Runbook link",
        "state": "success",
        "detail": "Operator has a documented first action",
        "evidence": "INTEGRATION_INCIDENT_RUNBOOKS.md"
      },
      {
        "name": "Rollback path",
        "state": "success",
        "detail": "Release promotion stays blocked while warning is open",
        "evidence": "release.canary_gate.blocked"
      },
      {
        "name": "Postcheck",
        "state": "success",
        "detail": "Resolution requires postcheck evidence",
        "evidence": "postcheck.gates.passed"
      }
    ]
  },
  "businessControlTower": {
    "summary": [
      {
        "label": "Observed systems",
        "value": "3",
        "detail": "crm, bank, accounting",
        "tone": "blue"
      },
      {
        "label": "Open exceptions",
        "value": "1",
        "detail": "payment state mismatch",
        "tone": "amber"
      },
      {
        "label": "Repair actions",
        "value": "1",
        "detail": "approval-gated dry-run",
        "tone": "green"
      },
      {
        "label": "External writes",
        "value": "0",
        "detail": "public-safe execution",
        "tone": "violet"
      },
      {
        "label": "Context cards",
        "value": "3",
        "detail": "role workbench preview",
        "tone": "blue"
      },
      {
        "label": "Provider intake",
        "value": "1",
        "detail": "safe CRM payload preview",
        "tone": "green"
      }
    ],
    "providerIntake": {
      "providerKey": "crm.bitrix24.mock",
      "sourceType": "crm_deal",
      "subject": "deal:DEAL-2026-001",
      "status": "mapped",
      "summary": "Bitrix-style deal payload is mapped into a normalized observation before DriveDesk builds workbench context.",
      "safePayload": {
        "amount_bucket": "1000-2000",
        "owner_role": "sales",
        "source_state": "invoice_sent"
      },
      "payloadKeys": [
        "access_token",
        "amount",
        "full_name",
        "owner_role",
        "phone",
        "stage"
      ],
      "droppedKeys": [
        "access_token",
        "full_name",
        "phone"
      ],
      "normalizedObservation": {
        "systemKey": "crm.bitrix24.mock",
        "systemFamily": "crm",
        "subject": "deal:DEAL-2026-001",
        "externalRef": "crm-deal-001",
        "state": "invoice_sent",
        "wouldCreate": "BusinessStateObservation",
        "wouldRecordEvent": "business_state.observation.recorded",
        "rawPayloadIncluded": false,
        "piiIncluded": false,
        "externalFetch": false,
        "externalMutation": false,
        "requiresSecret": false
      },
      "dataBoundaries": [
        {
          "name": "preview_only_no_persist",
          "status": "preview_only",
          "detail": "Provider intake preview does not create observations or call provider APIs."
        },
        {
          "name": "raw_provider_payload_not_returned",
          "status": "clean",
          "detail": "Only safe fields and dropped key names are returned to the workbench."
        },
        {
          "name": "secret_boundary",
          "status": "clean",
          "detail": "No Bitrix, bank, accounting, Telegram, or email credentials are required."
        }
      ],
      "nextSteps": [
        {
          "step": "record_normalized_observation",
          "status": "available",
          "endpoint": "POST /tenants/{tenant_id}/business-state/observations",
          "externalMutation": false,
          "evidence": "business_state.observation.recorded"
        },
        {
          "step": "open_workbench_context",
          "status": "available",
          "endpoint": "POST /tenants/{tenant_id}/business-workbench-context/preview",
          "externalMutation": false,
          "evidence": "business_workbench_context.previewed"
        },
        {
          "step": "run_detection_preview",
          "status": "available",
          "endpoint": "POST /tenants/{tenant_id}/business-detections/preview",
          "externalMutation": false,
          "evidence": "business_detection.previewed"
        }
      ],
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-provider-intake/preview"
      }
    },
    "workbenchContext": {
      "contextKind": "role_assist",
      "role": "accountant",
      "riskLevel": "attention",
      "summary": "DriveDesk turns CRM, bank, and accounting observations into safe workbench cards before the accountant decides what to do next.",
      "sourceSystems": [
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock"
      ],
      "contextCards": [
        {
          "cardId": "crm.deal.DEAL-2026-001.invoice_sent",
          "title": "CRM deal context",
          "systemKey": "crm.bitrix24.mock",
          "systemFamily": "crm",
          "subject": "deal:DEAL-2026-001",
          "state": "invoice_sent",
          "status": "needs_cross_check",
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
          "payloadKeys": [
            "amount_bucket",
            "owner_role"
          ],
          "rawPayloadIncluded": false,
          "piiIncluded": false,
          "externalFetch": false,
          "externalMutation": false,
          "evidence": "business_workbench_context.previewed"
        },
        {
          "cardId": "bank.deal.DEAL-2026-001.paid",
          "title": "Payment evidence",
          "systemKey": "bank.statement.mock",
          "systemFamily": "bank",
          "subject": "deal:DEAL-2026-001",
          "state": "paid",
          "status": "confirmed",
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
          "payloadKeys": [
            "amount_bucket",
            "matched_by"
          ],
          "rawPayloadIncluded": false,
          "piiIncluded": false,
          "externalFetch": false,
          "externalMutation": false,
          "evidence": "business_workbench_context.previewed"
        },
        {
          "cardId": "accounting.deal.DEAL-2026-001.not_exported",
          "title": "Accounting export context",
          "systemKey": "accounting.export.mock",
          "systemFamily": "accounting",
          "subject": "deal:DEAL-2026-001",
          "state": "not_exported",
          "status": "action_required",
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
          "payloadKeys": [
            "export_batch_id",
            "reason"
          ],
          "rawPayloadIncluded": false,
          "piiIncluded": false,
          "externalFetch": false,
          "externalMutation": false,
          "evidence": "business_workbench_context.previewed"
        }
      ],
      "suggestedActions": [
        {
          "action": "reconcile_crm_payment_status",
          "status": "available",
          "summary": "Compare the paid bank state with the CRM deal state before any external write.",
          "endpoint": "POST /tenants/{tenant_id}/business-detections/preview",
          "externalMutation": false,
          "requiresApproval": false,
          "evidence": "business_workbench_context.previewed"
        },
        {
          "action": "review_accounting_export",
          "status": "available",
          "summary": "Open the accounting export evidence and decide whether a dry-run repair is needed.",
          "endpoint": "GET /tenants/{tenant_id}/business-state/observations",
          "externalMutation": false,
          "requiresApproval": false,
          "evidence": "business_workbench_context.previewed"
        },
        {
          "action": "open_action_plan_preview",
          "status": "ready",
          "summary": "Turn the current context into ordered operator work inside DriveDesk.",
          "endpoint": "POST /tenants/{tenant_id}/business-action-plans/preview",
          "externalMutation": false,
          "requiresApproval": false,
          "evidence": "business_action_plan.previewed"
        }
      ],
      "dataBoundaries": [
        {
          "name": "read_only_source_context",
          "status": "preview_only",
          "externalFetch": false,
          "externalMutation": false,
          "detail": "The preview uses normalized DriveDesk observations and does not call provider APIs."
        },
        {
          "name": "pii_redaction",
          "status": "clean",
          "rawPayloadIncluded": false,
          "detail": "Cards expose safe facts and payload keys, not raw provider payloads."
        },
        {
          "name": "secret_boundary",
          "status": "clean",
          "requiresSecret": false,
          "detail": "No Bitrix, bank, accounting, Telegram, or email credentials are required for preview."
        }
      ],
      "reviewPoints": [
        {
          "name": "single_work_surface",
          "status": "ready",
          "detail": "External facts are rendered next to the operator workflow inside DriveDesk."
        },
        {
          "name": "next_action_boundary",
          "status": "preview_only",
          "detail": "Suggested actions link only to DriveDesk previews and approval-gated flows."
        }
      ],
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-workbench-context/preview"
      }
    },
    "detection": {
      "ruleSet": "payment_reconciliation",
      "status": "detected",
      "summary": "Detector reviewed CRM, bank, and accounting observations and found one payment reconciliation exception candidate.",
      "rules": [
        {
          "key": "payment_reconciliation.crm_bank_accounting_mismatch",
          "status": "active",
          "if": [
            "crm.state=invoice_sent",
            "bank.state=paid",
            "accounting.state=not_exported"
          ],
          "then": [
            "detect crm_payment_mismatch",
            "suggest sync_status repair"
          ]
        }
      ],
      "detectedExceptions": [
        {
          "type": "crm_payment_mismatch",
          "severity": "warning",
          "confidence": "high",
          "subject": "deal:DEAL-2026-001",
          "wouldCreate": "BusinessException",
          "evidence": "business_detection.previewed"
        }
      ],
      "suggestedRepairActions": [
        {
          "action": "sync_status",
          "status": "suggested",
          "requiresApproval": true,
          "externalMutation": false,
          "wouldCreate": "RepairAction",
          "evidence": "business_detection.previewed"
        }
      ],
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-detections/preview"
      }
    },
    "escalation": {
      "policy": "exception_triage",
      "riskLevel": "attention",
      "summary": "One warning exception is routed to the finance reconciliation queue with a dry-run repair next step.",
      "queues": [
        {
          "queue": "finance_reconciliation",
          "ownerRole": "accountant",
          "openItems": 1,
          "highestSeverity": "warning",
          "minSlaMinutes": 120,
          "status": "active"
        }
      ],
      "items": [
        {
          "exceptionType": "crm_payment_mismatch",
          "severity": "warning",
          "status": "open",
          "subject": "deal:DEAL-2026-001",
          "ownerRole": "accountant",
          "queue": "finance_reconciliation",
          "escalationLevel": "L2",
          "slaMinutes": 120,
          "nextAction": "execute_repair_dry_run",
          "nextActionStatus": "ready",
          "externalMutation": false,
          "evidence": "business_escalation.previewed"
        }
      ],
      "suggestedActions": [
        {
          "action": "execute_repair_dry_run",
          "status": "ready",
          "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "externalMutation": false,
          "evidence": "repair_action.approved"
        }
      ],
      "reviewPoints": [
        {
          "name": "write_boundary",
          "status": "preview_only",
          "detail": "Escalation does not create tasks, approve repairs, or mutate external systems."
        },
        {
          "name": "owner_routing",
          "status": "ready",
          "detail": "Exception type and severity map to role, queue, and SLA."
        }
      ],
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-escalations/preview"
      }
    },
    "actionPlan": {
      "planKind": "exception_resolution",
      "role": "accountant",
      "riskLevel": "attention",
      "summary": "The accountant gets one ordered work plan from CRM, bank, accounting, exception, and repair evidence.",
      "lanes": [
        {
          "lane": "finance_reconciliation",
          "ownerRole": "accountant",
          "slaMinutes": 120,
          "workItems": 1,
          "status": "active"
        }
      ],
      "steps": [
        {
          "sequence": 1,
          "step": "verify_source_evidence",
          "lane": "finance_reconciliation",
          "ownerRole": "accountant",
          "status": "ready",
          "summary": "Review CRM, bank, and accounting state before any repair.",
          "sourceSystems": [
            "crm.bitrix24.mock",
            "bank.statement.mock",
            "accounting.export.mock"
          ],
          "endpoint": "GET /tenants/{tenant_id}/business-state/observations",
          "requiresApproval": false,
          "externalMutation": false,
          "evidence": "business_state.observation.recorded"
        },
        {
          "sequence": 2,
          "step": "execute_repair_dry_run",
          "lane": "finance_reconciliation",
          "ownerRole": "accountant",
          "status": "ready",
          "summary": "Queue the approved sync_status repair in dry-run mode.",
          "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "requiresApproval": false,
          "externalMutation": false,
          "evidence": "repair_action.approved"
        },
        {
          "sequence": 3,
          "step": "close_or_acknowledge_exception",
          "lane": "finance_reconciliation",
          "ownerRole": "accountant",
          "status": "waiting_for_repair",
          "summary": "Record the accountant decision after dry-run evidence is reviewed.",
          "endpoint": "POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/status",
          "requiresApproval": false,
          "externalMutation": false,
          "evidence": "business_exception.status_changed"
        }
      ],
      "automationCandidates": [
        {
          "name": "queue_repair_execution",
          "status": "ready",
          "action": "execute_repair_dry_run",
          "adapterKey": "internal.noop",
          "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "externalMutation": false,
          "evidence": "repair_action.approved"
        },
        {
          "name": "recheck_accounting_export",
          "status": "available",
          "action": "run_read_only_connection_check",
          "adapterKey": "accounting.export.mock",
          "endpoint": "POST /tenants/{tenant_id}/integration-connections/{connection_id}/checks",
          "externalMutation": false,
          "evidence": "integration_connection.check.requested"
        }
      ],
      "approvalGates": [
        {
          "name": "repair_action_approval",
          "status": "satisfied",
          "requiresApproval": true,
          "externalMutation": false,
          "evidence": "repair_action.approved"
        }
      ],
      "reviewPoints": [
        {
          "name": "single_work_surface",
          "status": "ready",
          "detail": "Cross-system facts become ordered work inside DriveDesk."
        },
        {
          "name": "approval_boundary",
          "status": "satisfied",
          "detail": "External-facing repair remains behind approval and dry-run evidence."
        },
        {
          "name": "automation_boundary",
          "status": "preview_only",
          "detail": "The action plan preview does not create tasks, notify users, or mutate external systems."
        }
      ],
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-action-plans/preview"
      }
    },
    "notifications": {
      "notificationKind": "action_plan_updates",
      "role": "accountant",
      "riskLevel": "attention",
      "summary": "DriveDesk prepares safe in-app and Telegram notification drafts from the current action plan.",
      "channels": [
        {
          "channel": "in_app",
          "status": "ready",
          "configured": true,
          "externalDelivery": false,
          "requiresSecret": false,
          "evidence": "business_notification.previewed"
        },
        {
          "channel": "telegram",
          "status": "requires_channel_config",
          "configured": false,
          "externalDelivery": false,
          "requiresSecret": true,
          "evidence": "business_notification.previewed"
        }
      ],
      "drafts": [
        {
          "draftId": "action_plan_updates.in_app.accountant",
          "channel": "in_app",
          "recipientRole": "accountant",
          "title": "Payment mismatch action plan is ready",
          "body": "deal:DEAL-2026-001 has a ready action plan step: execute_repair_dry_run.",
          "actionEndpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "piiIncluded": false,
          "externalDelivery": false,
          "status": "ready",
          "evidence": "business_notification.previewed"
        },
        {
          "draftId": "action_plan_updates.telegram.accountant",
          "channel": "telegram",
          "recipientRole": "accountant",
          "title": "Payment mismatch action plan is ready",
          "body": "deal:DEAL-2026-001 has a ready action plan step: execute_repair_dry_run.",
          "actionEndpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "piiIncluded": false,
          "externalDelivery": false,
          "status": "preview_only",
          "evidence": "business_notification.previewed"
        }
      ],
      "deliveryPlan": [
        {
          "channel": "in_app",
          "status": "ready",
          "recipientRole": "accountant",
          "sendMode": "preview_only",
          "externalDelivery": false,
          "requiresSecret": false,
          "wouldEnqueueEvent": "notification.delivery.requested",
          "evidence": "business_notification.previewed"
        },
        {
          "channel": "telegram",
          "status": "requires_channel_config",
          "recipientRole": "accountant",
          "sendMode": "preview_only",
          "externalDelivery": false,
          "requiresSecret": true,
          "wouldEnqueueEvent": "notification.delivery.requested",
          "evidence": "business_notification.previewed"
        }
      ],
      "approvalGates": [
        {
          "name": "notification_content_review",
          "status": "ready",
          "requiresApproval": false,
          "externalDelivery": false,
          "evidence": "business_notification.previewed"
        },
        {
          "name": "repair_action_approval",
          "status": "satisfied",
          "requiresApproval": true,
          "externalDelivery": false,
          "evidence": "repair_action.approved"
        }
      ],
      "reviewPoints": [
        {
          "name": "no_external_send",
          "status": "preview_only",
          "detail": "Notification preview does not call Telegram, email, CRM, or any other provider."
        },
        {
          "name": "pii_boundary",
          "status": "clean",
          "detail": "Drafts avoid raw personal data and use role, subject key, endpoint, and evidence labels."
        }
      ],
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-notifications/preview"
      }
    },
    "briefing": {
      "role": "accountant",
      "riskLevel": "attention",
      "summary": "Payment is visible in bank evidence, but CRM still shows invoice_sent and accounting export is waiting.",
      "sourceSystems": [
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock"
      ],
      "highlights": [
        {
          "type": "business_exception",
          "title": "Payment received but CRM and accounting lag behind",
          "detail": "One open crm_payment_mismatch affects deal:DEAL-2026-001.",
          "evidence": "business_exception.created"
        },
        {
          "type": "state_observation",
          "title": "Bank state",
          "detail": "bank.statement.mock reports paid with matched payment reference.",
          "evidence": "business_state.observation.recorded"
        },
        {
          "type": "repair_context",
          "title": "Approved dry-run repair",
          "detail": "sync_status can queue a dry-run repair event without external mutation.",
          "evidence": "repair_action.approved"
        }
      ],
      "recommendedActions": [
        {
          "action": "execute_repair_dry_run",
          "status": "ready",
          "endpoint": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
          "evidence": "repair_action.approved"
        },
        {
          "action": "review_accounting_export",
          "status": "available",
          "endpoint": "GET /tenants/{tenant_id}/business-exceptions",
          "evidence": "accounting.export.mock:not_exported"
        }
      ],
      "reviewPoints": [
        {
          "name": "source_evidence",
          "status": "ready",
          "detail": "CRM, bank, and accounting states are visible in one briefing."
        },
        {
          "name": "external_mutation",
          "status": "review_required",
          "detail": "External writes stay behind approval and outbox evidence."
        }
      ],
      "api": {
        "preview": "POST /tenants/{tenant_id}/business-briefings/preview"
      }
    },
    "observations": [
      {
        "id": "obs-crm-deal",
        "system": "crm.bitrix24.mock",
        "subject": "deal:DEAL-2026-001",
        "state": "invoice_sent",
        "observedAt": "2026-06-19T06:05:00Z",
        "evidence": "business_state.observation.recorded"
      },
      {
        "id": "obs-bank-payment",
        "system": "bank.statement.mock",
        "subject": "deal:DEAL-2026-001",
        "state": "paid",
        "observedAt": "2026-06-19T06:06:00Z",
        "evidence": "business_state.observation.recorded"
      },
      {
        "id": "obs-accounting-export",
        "system": "accounting.export.mock",
        "subject": "deal:DEAL-2026-001",
        "state": "not_exported",
        "observedAt": "2026-06-19T06:07:00Z",
        "evidence": "business_state.observation.recorded"
      }
    ],
    "exceptions": [
      {
        "id": "bex-payment-crm-mismatch",
        "type": "crm_payment_mismatch",
        "severity": "warning",
        "status": "open",
        "subject": "deal:DEAL-2026-001",
        "impact": "cash received but CRM and accounting are not aligned",
        "evidence": "business_exception.created"
      }
    ],
    "repairActions": [
      {
        "id": "repair-sync-crm-payment",
        "action": "sync_status",
        "status": "approved",
        "safety": "medium",
        "mode": "dry_run",
        "requiresApproval": true,
        "externalMutation": false,
        "evidence": "repair_action.executed"
      }
    ],
    "flow": [
      {
        "step": "intake",
        "owner": "adapter",
        "state": "preview_only",
        "detail": "Provider payload is reduced to safe normalized observation fields.",
        "evidence": "business_provider_intake.previewed"
      },
      {
        "step": "observe",
        "owner": "adapter",
        "state": "done",
        "detail": "CRM, bank, and accounting states are normalized into one subject.",
        "evidence": "business_state.observation.recorded"
      },
      {
        "step": "context",
        "owner": "workbench",
        "state": "preview_only",
        "detail": "Role-specific cards summarize external state without provider reads, secrets, or PII.",
        "evidence": "business_workbench_context.previewed"
      },
      {
        "step": "detect",
        "owner": "control_tower",
        "state": "done",
        "detail": "Payment state mismatch becomes a business exception with impact.",
        "evidence": "business_exception.created"
      },
      {
        "step": "propose",
        "owner": "repair_engine",
        "state": "done",
        "detail": "Repair action is proposed without direct external mutation.",
        "evidence": "repair_action.proposed"
      },
      {
        "step": "approve",
        "owner": "operator",
        "state": "done",
        "detail": "Human approval is recorded before execution.",
        "evidence": "repair_action.approved"
      },
      {
        "step": "plan",
        "owner": "workbench",
        "state": "ready",
        "detail": "The operator receives an ordered action plan with approval and automation boundaries.",
        "evidence": "business_action_plan.previewed"
      },
      {
        "step": "notify",
        "owner": "workbench",
        "state": "preview_only",
        "detail": "DriveDesk prepares notification drafts without external delivery.",
        "evidence": "business_notification.previewed"
      },
      {
        "step": "execute",
        "owner": "outbox",
        "state": "done",
        "detail": "Dry-run execution queues a repair event and records result evidence.",
        "evidence": "repair_action.execution_requested"
      }
    ],
    "api": {
      "intake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "observe": "POST /tenants/{tenant_id}/business-state/observations",
      "exceptions": "POST /tenants/{tenant_id}/business-exceptions",
      "repair": "POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/repair-actions",
      "approve": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/approve",
      "execute": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute"
    },
    "metrics": [
      "drivedesk_business_state_observations",
      "drivedesk_business_exceptions",
      "drivedesk_repair_actions"
    ]
  },
  "businessScenarioReplay": {
    "status": "validated",
    "command": "bash scripts/check_public_business_scenario_replay.sh",
    "summary": [
      {
        "label": "Scenario groups",
        "value": "3",
        "detail": "CRM, support, and procurement replay paths",
        "tone": "blue"
      },
      {
        "label": "Source systems",
        "value": "7",
        "detail": "external signals normalized before action",
        "tone": "green"
      },
      {
        "label": "Operator actions",
        "value": "8",
        "detail": "recommended actions stay approval-aware",
        "tone": "amber"
      },
      {
        "label": "External writes",
        "value": "0",
        "detail": "public replay is read-only",
        "tone": "violet"
      }
    ],
    "scenarios": [
      {
        "id": "crm-bank-payment-mismatch",
        "title": "CRM and bank payment mismatch",
        "status": "attention",
        "riskLevel": "warning",
        "operatorRole": "accountant",
        "trigger": "crm.deal.updated",
        "decision": "open reconciliation workbench",
        "sourceSystems": [
          "crm.bitrix24.mock",
          "bank.statement.mock",
          "accounting.export.mock"
        ],
        "normalizedFacts": [
          {
            "key": "crm_stage",
            "value": "invoice_sent",
            "source": "crm.bitrix24.mock"
          },
          {
            "key": "bank_status",
            "value": "payment_seen",
            "source": "bank.statement.mock"
          },
          {
            "key": "accounting_status",
            "value": "export_pending",
            "source": "accounting.export.mock"
          }
        ],
        "recommendedActions": [
          {
            "action": "compare bank amount bucket with CRM deal amount",
            "mode": "operator_review",
            "evidence": "integration.reconciliation.previewed"
          },
          {
            "action": "queue accounting export after approval",
            "mode": "approval_required",
            "evidence": "business_action_plan.previewed"
          },
          {
            "action": "prepare customer payment-status note",
            "mode": "draft_only",
            "evidence": "business_notification.previewed"
          }
        ],
        "automationCandidates": [
          {
            "candidate": "create business exception",
            "safeToAutoRun": true,
            "boundary": "internal_record_only"
          },
          {
            "candidate": "send customer notification",
            "safeToAutoRun": false,
            "boundary": "requires_operator_approval"
          }
        ],
        "evidence": [
          "business_exception.created",
          "business_action_plan.previewed",
          "integration.reconciliation.recorded"
        ],
        "dataBoundary": [
          "no raw provider payload",
          "no credentials",
          "no personal data",
          "synthetic sources"
        ]
      },
      {
        "id": "support-sla-risk",
        "title": "Support SLA risk",
        "status": "action_required",
        "riskLevel": "high",
        "operatorRole": "support_lead",
        "trigger": "support.message.received",
        "decision": "escalate with context before SLA breach",
        "sourceSystems": [
          "support.inbox.mock",
          "telephony.callback.mock",
          "sla.policy.mock"
        ],
        "normalizedFacts": [
          {
            "key": "message_state",
            "value": "waiting_for_reply",
            "source": "support.inbox.mock"
          },
          {
            "key": "callback_state",
            "value": "missed",
            "source": "telephony.callback.mock"
          },
          {
            "key": "sla_window",
            "value": "15m",
            "source": "sla.policy.mock"
          }
        ],
        "recommendedActions": [
          {
            "action": "assign support lead and create reply task",
            "mode": "operator_review",
            "evidence": "business_escalation.previewed"
          },
          {
            "action": "prepare apology and callback draft",
            "mode": "draft_only",
            "evidence": "business_notification.previewed"
          }
        ],
        "automationCandidates": [
          {
            "candidate": "open escalation item",
            "safeToAutoRun": true,
            "boundary": "internal_record_only"
          },
          {
            "candidate": "place callback",
            "safeToAutoRun": false,
            "boundary": "external_channel_blocked"
          }
        ],
        "evidence": [
          "business_escalation.previewed",
          "business_action_plan.previewed",
          "business_notification.previewed"
        ],
        "dataBoundary": [
          "message body omitted",
          "phone number omitted",
          "no external delivery",
          "synthetic sources"
        ]
      },
      {
        "id": "procurement-delay-risk",
        "title": "Procurement delay risk",
        "status": "needs_cross_check",
        "riskLevel": "medium",
        "operatorRole": "operations_manager",
        "trigger": "supplier.delivery.updated",
        "decision": "create procurement exception and check cash timing",
        "sourceSystems": [
          "supplier.portal.mock",
          "inventory.stock.mock",
          "bank.payment-order.mock"
        ],
        "normalizedFacts": [
          {
            "key": "supplier_state",
            "value": "delayed",
            "source": "supplier.portal.mock"
          },
          {
            "key": "stock_state",
            "value": "below_minimum",
            "source": "inventory.stock.mock"
          },
          {
            "key": "payment_order",
            "value": "prepared",
            "source": "bank.payment-order.mock"
          }
        ],
        "recommendedActions": [
          {
            "action": "open procurement exception",
            "mode": "operator_review",
            "evidence": "business_exception.created"
          },
          {
            "action": "compare supplier ETA with minimum stock window",
            "mode": "operator_review",
            "evidence": "business_workbench_context.previewed"
          },
          {
            "action": "hold payment order until manager approval",
            "mode": "approval_required",
            "evidence": "business_action_plan.previewed"
          }
        ],
        "automationCandidates": [
          {
            "candidate": "create manager task",
            "safeToAutoRun": true,
            "boundary": "internal_record_only"
          },
          {
            "candidate": "release bank payment",
            "safeToAutoRun": false,
            "boundary": "financial_write_blocked"
          }
        ],
        "evidence": [
          "business_exception.created",
          "business_workbench_context.previewed",
          "business_action_plan.previewed"
        ],
        "dataBoundary": [
          "no bank credentials",
          "no supplier raw payload",
          "payment values bucketed",
          "synthetic sources"
        ]
      }
    ],
    "flow": [
      {
        "step": "1",
        "stage": "signal",
        "detail": "External systems produce signals through adapters, files, webhooks, or polling.",
        "evidence": "provider_signal.received"
      },
      {
        "step": "2",
        "stage": "normalize",
        "detail": "DriveDesk maps each signal into safe business facts with provider-specific details removed.",
        "evidence": "business_state.observation.recorded"
      },
      {
        "step": "3",
        "stage": "detect",
        "detail": "Rules compare facts across systems and create exception candidates.",
        "evidence": "business_exception.created"
      },
      {
        "step": "4",
        "stage": "plan",
        "detail": "The workbench builds role-specific context, recommended actions, and approval gates.",
        "evidence": "business_action_plan.previewed"
      },
      {
        "step": "5",
        "stage": "execute",
        "detail": "Only approved internal actions can run; external writes stay behind explicit approval.",
        "evidence": "operator_approval.required"
      }
    ],
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
    ]
  },
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
      "detail": "synthetic demo data only",
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
      "detail": "private staging runtime evidence is collected through public-safe contracts",
      "evidence": "runtime.rollout.evidence_collected"
    },
    {
      "name": "Loopback boundary",
      "state": "success",
      "detail": "private staging checks stay behind a loopback-only public boundary",
      "evidence": "loopback_boundary_recorded"
    },
    {
      "name": "Private state validation",
      "state": "success",
      "detail": "read-only private infra validation evidence is recorded",
      "evidence": "infra.private_state.validated"
    },
    {
      "name": "No runtime mutation",
      "state": "success",
      "detail": "validation records that no runtime mutation was performed",
      "evidence": "no_runtime_mutation_recorded"
    },
    {
      "name": "Remediation plan",
      "state": "success",
      "detail": "drift remediation is planned with operator review before apply",
      "evidence": "infra.remediation.plan.ready"
    },
    {
      "name": "Rollback attached",
      "state": "success",
      "detail": "remediation plan includes rollback context",
      "evidence": "rollback_attached"
    },
    {
      "name": "Remediation execution",
      "state": "success",
      "detail": "reviewed private staging remediation execution is recorded",
      "evidence": "infra.remediation.execution.completed"
    },
    {
      "name": "Post-remediation validation",
      "state": "success",
      "detail": "postcheck validation is recorded after remediation execution",
      "evidence": "post_remediation_validation_recorded"
    },
    {
      "name": "Post-remediation drift",
      "state": "success",
      "detail": "read-only drift refresh shows clean state after remediation",
      "evidence": "infra.post_remediation_drift.clean"
    },
    {
      "name": "No residual drift",
      "state": "success",
      "detail": "post-remediation refresh records no residual drift",
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
  "engineeringProof": {
    "milestone": "engineering_70",
    "status": "validated",
    "updatedAt": "2026-06-18T10:14:36Z",
    "summary": [
      {
        "label": "CI/CD",
        "value": "green",
        "detail": "smoke, release, SDK, and public export gates",
        "tone": "green"
      },
      {
        "label": "Runtime",
        "value": "observable",
        "detail": "health, readiness, metrics, logs, and SLO evidence",
        "tone": "blue"
      },
      {
        "label": "Recovery",
        "value": "drilled",
        "detail": "backup, restore, rollback, and staged promotion",
        "tone": "violet"
      },
      {
        "label": "Boundary",
        "value": "public-safe",
        "detail": "synthetic data, redacted evidence, no secrets",
        "tone": "green"
      }
    ],
    "gates": [
      {
        "name": "Core smoke",
        "status": "passed",
        "command": "bash scripts/ci_smoke_public.sh",
        "evidence": "API, worker, RBAC, outbox, integration, and observability checks"
      },
      {
        "name": "Public demo API",
        "status": "passed",
        "command": "bash scripts/check_public_demo_api.sh",
        "evidence": "GET /demo/public, OpenAPI, examples, generated clients"
      },
      {
        "name": "Backup and restore",
        "status": "passed",
        "command": "bash scripts/check_public_backup_restore.sh",
        "evidence": "backup_sha256_recorded, restore_integrity_ok, counts_match"
      },
      {
        "name": "Release safety",
        "status": "passed",
        "command": "bash scripts/check_public_release_rollback.sh && bash scripts/check_public_staged_promotion.sh",
        "evidence": "rollback, canary gate, approval, and promotion history"
      },
      {
        "name": "GitOps and IaC",
        "status": "passed",
        "command": "bash scripts/check_public_gitops_layout.sh && bash scripts/check_public_opentofu_plan.sh",
        "evidence": "Helm, Argo CD layout, OpenTofu plan, drift records"
      }
    ],
    "evidence": [
      {
        "title": "System review path",
        "kind": "doc",
        "path": "docs/public/SYSTEM_REVIEW_PATH.md",
        "summary": "Compact route through public root, demo, API, SDK, operations evidence, release safety, GitOps, OpenTofu, and evidence index"
      },
      {
        "title": "Verification quickstart",
        "kind": "doc",
        "path": "docs/public/REVIEWER_QUICKSTART.md",
        "summary": "Timeboxed 5-minute, 15-minute, and 45-minute external verification path"
      },
      {
        "title": "Milestone contract",
        "kind": "doc",
        "path": "docs/public/PLATFORM_MATURITY_70.md",
        "summary": "Seven evidence groups with executable validation gates"
      },
      {
        "title": "Sanitized evidence index",
        "kind": "doc",
        "path": "docs/public/SANITIZED_EVIDENCE.md",
        "summary": "Runtime, recovery, release, GitOps, and boundary evidence"
      },
      {
        "title": "System design",
        "kind": "doc",
        "path": "docs/public/SYSTEM_DESIGN.md",
        "summary": "Core architecture, async boundaries, adapters, and observability"
      },
      {
        "title": "Generated SDK",
        "kind": "sdk",
        "path": "sdk/generated/public-demo/",
        "summary": "OpenAPI-driven Python, JavaScript, and TypeScript client artifacts"
      }
    ]
  },
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
  "workflowScenarios": [
    {
      "id": "scenario-contract-approval-sync",
      "title": "Contract approval sync",
      "trigger": "business_record.status_changed contract:draft->approved",
      "actionType": "emit_outbox_event",
      "owner": "Operations",
      "status": "processed",
      "detail": "Approved contract emits an outbox event for downstream document and accounting adapters.",
      "outputs": [
        "audit_event",
        "outbox_event",
        "action_run"
      ],
      "evidence": "workflow.contract_approved"
    },
    {
      "id": "scenario-signature-task",
      "title": "Signature task creation",
      "trigger": "business_record.status_changed contract:approved->signature_required",
      "actionType": "create_task_record",
      "owner": "Front desk",
      "status": "ready",
      "detail": "A staff task is created so the contract cannot silently wait for a manual signature step.",
      "outputs": [
        "audit_event",
        "task_record",
        "action_run"
      ],
      "evidence": "workflow.task_record.created"
    },
    {
      "id": "scenario-accounting-export",
      "title": "Accounting export request",
      "trigger": "business_record.status_changed contract:approved->ready_for_billing",
      "actionType": "request_adapter_sync",
      "owner": "Finance",
      "status": "pending",
      "detail": "Billing-ready contracts request an adapter operation with retry, idempotency, and review evidence.",
      "outputs": [
        "outbox_event",
        "integration_job",
        "action_run"
      ],
      "evidence": "workflow.contract_sync.requested"
    }
  ],
  "endToEndScenario": {
    "id": "scenario-approval-notification-adapter-incident",
    "title": "Approval to recovery proof",
    "summary": "Synthetic path from contract approval through notification, adapter export, dead-letter incident, recovery, and public evidence.",
    "status": "reviewable",
    "currentStep": "incident_resolved",
    "chain": [
      {
        "step": "approval",
        "title": "Contract approved",
        "owner": "Operations",
        "state": "processed",
        "source": "workflowScenarios.scenario-contract-approval-sync",
        "evidence": "workflow.contract_approved"
      },
      {
        "step": "notification",
        "title": "Manager notification queued",
        "owner": "Workflow engine",
        "state": "ready",
        "source": "workflowScenarios.scenario-signature-task",
        "evidence": "notification.manager_signature_task.created"
      },
      {
        "step": "adapter",
        "title": "Accounting export requested",
        "owner": "Integration hub",
        "state": "retry",
        "source": "workflowScenarios.scenario-accounting-export",
        "evidence": "integration.accounting_export.requested"
      },
      {
        "step": "incident",
        "title": "Dead-letter incident opened",
        "owner": "Operator",
        "state": "acknowledged",
        "source": "incidentResponse.incidents",
        "evidence": "integration.incident.status_changed"
      },
      {
        "step": "recovery",
        "title": "Retry and postcheck completed",
        "owner": "Operator",
        "state": "resolved",
        "source": "incidentResponse.recoveryActions",
        "evidence": "postcheck.gates.passed"
      },
      {
        "step": "proof",
        "title": "Public evidence linked",
        "owner": "Release gate",
        "state": "validated",
        "source": "engineeringProof.evidence",
        "evidence": "docs/public/ENGINEERING_PROOF.md"
      }
    ],
    "proof": [
      "workflow.contract_approved",
      "notification.manager_signature_task.created",
      "integration.accounting_export.requested",
      "integration.incident.status_changed",
      "postcheck.gates.passed",
      "docs/public/ENGINEERING_PROOF.md"
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
