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
  "connectorCertification": {
    "status": "validated",
    "command": "GET /demo/connector-certification",
    "certificationLevel": "public_contract_certified",
    "adapterCount": 4,
    "privateReadyCount": 2,
    "summary": [
      {
        "label": "Adapters checked",
        "value": "4",
        "detail": "runtime catalog providers",
        "tone": "blue"
      },
      {
        "label": "Private-ready",
        "value": "2",
        "detail": "profile, scope, secret boundary, idempotency",
        "tone": "green"
      },
      {
        "label": "Provider calls",
        "value": "0",
        "detail": "certification is public-safe and offline",
        "tone": "amber"
      },
      {
        "label": "Evidence",
        "value": "linked",
        "detail": "docs, fixtures, runtime, execution",
        "tone": "violet"
      }
    ],
    "providerProfiles": [
      {
        "adapterKey": "accounting.export.mock",
        "name": "Mock Accounting Export",
        "category": "accounting_export",
        "direction": "outbound",
        "status": "private_ready",
        "operationCount": 1,
        "capabilityCount": 5,
        "connectionProfileSupported": true,
        "serverSecretBoundary": true,
        "requiresRealProviderSecret": true,
        "publicDemoRequiresSecret": false,
        "scopeBoundary": true,
        "idempotencyBoundary": true,
        "recoveryBoundary": true,
        "publicSafe": true,
        "readyForPrivateConnector": true,
        "evidence": "connector_certification.provider_profile_checked"
      },
      {
        "adapterKey": "crm.bitrix24.mock",
        "name": "Mock Bitrix24 CRM Intake",
        "category": "crm",
        "direction": "inbound",
        "status": "private_ready",
        "operationCount": 2,
        "capabilityCount": 8,
        "connectionProfileSupported": true,
        "serverSecretBoundary": true,
        "requiresRealProviderSecret": true,
        "publicDemoRequiresSecret": false,
        "scopeBoundary": true,
        "idempotencyBoundary": true,
        "recoveryBoundary": true,
        "publicSafe": true,
        "readyForPrivateConnector": true,
        "evidence": "connector_certification.provider_profile_checked"
      },
      {
        "adapterKey": "file.import.fake",
        "name": "Synthetic File Import",
        "category": "file_import",
        "direction": "inbound",
        "status": "contract_ready",
        "operationCount": 2,
        "capabilityCount": 7,
        "connectionProfileSupported": true,
        "serverSecretBoundary": false,
        "requiresRealProviderSecret": false,
        "publicDemoRequiresSecret": false,
        "scopeBoundary": true,
        "idempotencyBoundary": true,
        "recoveryBoundary": true,
        "publicSafe": true,
        "readyForPrivateConnector": false,
        "evidence": "connector_certification.provider_profile_checked"
      },
      {
        "adapterKey": "internal.noop",
        "name": "Internal Noop",
        "category": "internal",
        "direction": "internal",
        "status": "contract_ready",
        "operationCount": 1,
        "capabilityCount": 2,
        "connectionProfileSupported": false,
        "serverSecretBoundary": false,
        "requiresRealProviderSecret": false,
        "publicDemoRequiresSecret": false,
        "scopeBoundary": false,
        "idempotencyBoundary": true,
        "recoveryBoundary": false,
        "publicSafe": true,
        "readyForPrivateConnector": false,
        "evidence": "connector_certification.provider_profile_checked"
      }
    ],
    "certificationStages": [
      {
        "stage": "provider_profile",
        "status": "passed",
        "detail": "Adapter identity, category, direction, connection profile, and auth mode are declared.",
        "evidence": "connector_certification.provider_profile_checked"
      },
      {
        "stage": "capability_manifest",
        "status": "passed",
        "detail": "Capabilities, failure modes, mapping requirements, and operation contracts are visible.",
        "evidence": "connector_certification.capability_manifest_checked"
      },
      {
        "stage": "auth_boundary",
        "status": "clean",
        "detail": "Public demo returns secret reference names and boundary metadata, never secret values.",
        "evidence": "server_secret_store"
      },
      {
        "stage": "fixture_replay",
        "status": "validated",
        "detail": "Synthetic fixtures cover happy path, redaction, validation, retry, dead-letter, and reconciliation.",
        "evidence": "bash scripts/check_public_connector_fixture_replay.sh"
      },
      {
        "stage": "runtime_preview",
        "status": "validated",
        "detail": "Operation contracts resolve into scope preflight, outbox, worker, reconciliation, and incidents.",
        "evidence": "adapter_runtime.previewed"
      },
      {
        "stage": "execution_timeline",
        "status": "validated",
        "detail": "Run ledger, provider-call block, retry policy, and operator closure are represented.",
        "evidence": "integration_execution.run_ledger_prepared"
      },
      {
        "stage": "release_gate",
        "status": "enforced",
        "detail": "Public export, smoke, OpenAPI, SDK, and Pages checks must include this contract.",
        "evidence": "bash scripts/public_repo_release_gate.sh"
      }
    ],
    "certificationGates": [
      {
        "gate": "no_real_provider_call",
        "status": "closed",
        "detail": "Public certification does not call Bitrix, bank, accounting, email, Telegram, or payment APIs.",
        "externalMutation": false,
        "evidence": "provider_call_enabled=false"
      },
      {
        "gate": "no_secret_value",
        "status": "clean",
        "detail": "Only secret reference names are exposed in generated contracts.",
        "externalMutation": false,
        "evidence": "server_secret_store"
      },
      {
        "gate": "no_raw_payload",
        "status": "clean",
        "detail": "Raw provider payloads and request bodies stay outside the public payload.",
        "externalMutation": false,
        "evidence": "raw_payload_returned=false"
      },
      {
        "gate": "idempotent_execution",
        "status": "required",
        "detail": "Provider-changing operations must declare idempotency keys before private rollout.",
        "externalMutation": false,
        "evidence": "operation_contracts.idempotency_keys"
      },
      {
        "gate": "operator_review",
        "status": "armed",
        "detail": "Retry, dead-letter, and reconciliation mismatches route to operator review.",
        "externalMutation": false,
        "evidence": "integration.operator_review.created"
      }
    ],
    "implementationPath": [
      {
        "step": "add_private_provider_client",
        "status": "next_private_step",
        "detail": "Implement the real provider client behind server-side secrets and the existing adapter interface.",
        "evidence": "private_connector_only"
      },
      {
        "step": "bind_connection_profile",
        "status": "next_private_step",
        "detail": "Attach tenant-scoped connection profile, scopes, mappings, rate limits, and retry policy.",
        "evidence": "IntegrationConnection"
      },
      {
        "step": "run_fixture_replay",
        "status": "required",
        "detail": "Replay public-safe fixtures plus private sandbox fixtures before enabling provider writes.",
        "evidence": "connector_fixture_replay"
      },
      {
        "step": "enable_dry_run",
        "status": "required",
        "detail": "Run provider API calls in dry-run or read-only mode with audit and redaction evidence.",
        "evidence": "adapter_runtime.previewed"
      },
      {
        "step": "unlock_commit_request",
        "status": "requires_approval",
        "detail": "Allow write-mode execution only after approval, idempotency, observability, and rollback review.",
        "evidence": "business_approval_gateway.previewed"
      }
    ],
    "dataBoundaries": [
      {
        "name": "public_demo_data",
        "status": "synthetic_only",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "detail": "Workbench payload is generated from adapter metadata and synthetic evidence."
      },
      {
        "name": "browser_boundary",
        "status": "clean",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "detail": "Browser receives certification state, not provider tokens or raw provider responses."
      },
      {
        "name": "private_connector_boundary",
        "status": "separate",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "detail": "Real provider clients and secrets belong only in the private connector runtime."
      }
    ],
    "api": {
      "standalone": "GET /demo/connector-certification",
      "catalog": "GET /integration-adapters",
      "publicDemo": "GET /demo/public",
      "fixtureReplay": "GET /demo/connector-fixture-replay",
      "runtime": "GET /demo/integration-runtime",
      "execution": "GET /demo/integration-execution"
    },
    "docs": [
      {
        "label": "Connector certification",
        "path": "docs/public/CONNECTOR_CERTIFICATION.md",
        "check": "bash scripts/check_public_connector_certification.sh"
      },
      {
        "label": "Connector fixture replay",
        "path": "docs/public/CONNECTOR_FIXTURE_REPLAY.md",
        "check": "bash scripts/check_public_connector_fixture_replay.sh"
      },
      {
        "label": "Integration runtime",
        "path": "docs/public/INTEGRATION_RUNTIME.md",
        "check": "bash scripts/check_public_integration_runtime.sh"
      },
      {
        "label": "Integration execution",
        "path": "docs/public/INTEGRATION_EXECUTION.md",
        "check": "bash scripts/check_public_integration_execution.sh"
      }
    ]
  },
  "providerOnboarding": {
    "status": "previewed",
    "onboardingLevel": "sandbox_onboarding_ready",
    "providerKey": "crm.bitrix24.mock",
    "providerName": "Mock Bitrix24 CRM Intake",
    "providerCategory": "crm",
    "summary": [
      {
        "label": "Provider",
        "value": "CRM",
        "detail": "crm.bitrix24.mock",
        "tone": "blue"
      },
      {
        "label": "Records",
        "value": "2",
        "detail": "synthetic records accepted in mapping preview",
        "tone": "green"
      },
      {
        "label": "External calls",
        "value": "0",
        "detail": "public onboarding is dry-run only",
        "tone": "amber"
      },
      {
        "label": "Rollout",
        "value": "gated",
        "detail": "private connector requires approval evidence",
        "tone": "violet"
      }
    ],
    "providerProfile": {
      "adapterKey": "crm.bitrix24.mock",
      "adapterName": "Mock Bitrix24 CRM Intake",
      "category": "crm",
      "direction": "inbound",
      "authMode": "oauth2_or_webhook_boundary",
      "credentialPlacement": "server_secret_store",
      "secretRefs": [
        "BITRIX24_CLIENT_SECRET",
        "BITRIX24_WEBHOOK_URL"
      ],
      "publicDemoRequiresSecret": false,
      "realProviderRequiresSecret": true,
      "supportedScopes": [
        "crm:deal.ingest",
        "crm:deal.preview"
      ],
      "operationKeys": [
        "crm_deal_intake_preview",
        "crm_deal_ingest_execute"
      ],
      "executableOperationKeys": [
        "crm_deal_intake_preview",
        "crm_deal_ingest_execute"
      ],
      "evidence": "provider_onboarding.provider_profile_selected"
    },
    "onboardingStages": [
      {
        "stage": "select_provider_profile",
        "status": "selected",
        "detail": "crm.bitrix24.mock selected from the adapter catalog.",
        "evidence": "GET /integration-adapters"
      },
      {
        "stage": "bind_connection_profile",
        "status": "prepared",
        "detail": "Tenant mapping, scopes, and server-side secret references are ready.",
        "evidence": "IntegrationConnection"
      },
      {
        "stage": "mapping_preview",
        "status": "previewed",
        "detail": "2 accepted, 0 rejected.",
        "evidence": "adapter_mapping.previewed"
      },
      {
        "stage": "sandbox_dry_run",
        "status": "previewed",
        "detail": "Runtime and execution plans are computed without provider mutation.",
        "evidence": "adapter_runtime.previewed"
      },
      {
        "stage": "approval_review",
        "status": "approval_required",
        "detail": "Provider writes stay behind approval, idempotency, and rollback review.",
        "evidence": "business_approval_gateway.previewed"
      },
      {
        "stage": "private_rollout",
        "status": "next_private_step",
        "detail": "Private connector can swap the mock client for a real provider client.",
        "evidence": "private_connector_only"
      }
    ],
    "mappingPreview": {
      "adapterKey": "crm.bitrix24.mock",
      "recordsReceived": 2,
      "recordsAccepted": 2,
      "recordsRejected": 0,
      "requiredMappingKeys": [
        "deal_id",
        "source_state"
      ],
      "mappingKeys": [
        "amount",
        "deal_id",
        "owner_role",
        "source_state"
      ],
      "droppedSensitiveKeys": [
        "ACCESS_TOKEN",
        "CLIENT_NAME",
        "EMAIL",
        "PHONE",
        "SECRET"
      ],
      "rawPayloadIncluded": false,
      "containsPii": false,
      "evidence": "adapter_mapping.previewed"
    },
    "preflightChecks": [
      {
        "check": "adapter_registered",
        "status": "passed",
        "detail": "crm.bitrix24.mock",
        "externalMutation": false,
        "evidence": "provider_onboarding.preflight_passed"
      },
      {
        "check": "connection_scopes_available",
        "status": "passed",
        "detail": "crm:deal.ingest, crm:deal.preview",
        "externalMutation": false,
        "evidence": "adapter_runtime.scope_checked"
      },
      {
        "check": "mapping_profile_valid",
        "status": "passed",
        "detail": "amount, deal_id, owner_role, source_state",
        "externalMutation": false,
        "evidence": "adapter_mapping.previewed"
      },
      {
        "check": "secret_refs_server_side",
        "status": "clean",
        "detail": "server_secret_store",
        "externalMutation": false,
        "evidence": "server_secret_store"
      },
      {
        "check": "provider_call_disabled",
        "status": "closed",
        "detail": "Public onboarding never calls the external provider.",
        "externalMutation": false,
        "evidence": "provider_call_enabled=false"
      }
    ],
    "sandboxContract": {
      "previewOperation": "crm_deal_intake_preview",
      "executeOperation": "crm_deal_ingest_execute",
      "runtimeSteps": 7,
      "executionTimelineSteps": 8,
      "providerCallEnabled": false,
      "externalMutation": false,
      "rawPayloadIncluded": false,
      "containsPii": false,
      "evidence": "provider_onboarding.sandbox_contract_ready"
    },
    "rolloutPlan": [
      {
        "step": "create_tenant_connection",
        "status": "ready",
        "detail": "Create tenant-scoped connection metadata with mapping and scopes.",
        "evidence": "IntegrationConnection"
      },
      {
        "step": "run_mapping_preview",
        "status": "ready",
        "detail": "Validate provider field mapping against synthetic and sandbox fixtures.",
        "evidence": "adapter_mapping.previewed"
      },
      {
        "step": "run_fixture_replay",
        "status": "ready",
        "detail": "Replay success, redaction, invalid payload, retry, dead-letter, and reconciliation cases.",
        "evidence": "connector_fixture_replay"
      },
      {
        "step": "enable_private_dry_run",
        "status": "next_private_step",
        "detail": "Use real provider sandbox credentials only inside the private connector runtime.",
        "evidence": "private_connector_only"
      },
      {
        "step": "request_write_unlock",
        "status": "approval_required",
        "detail": "Enable write-mode only after approval, idempotency, SLO, and rollback evidence are attached.",
        "evidence": "business_approval_gateway.previewed"
      },
      {
        "step": "monitor_and_reconcile",
        "status": "scheduled",
        "detail": "Track outbox, reconciliation, incidents, and scheduled validation after rollout.",
        "evidence": "drivedesk_integration_reconciliations"
      }
    ],
    "dataBoundaries": [
      {
        "name": "public_onboarding_payload",
        "status": "synthetic_only",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "detail": "Public payload contains adapter metadata, counts, and redaction evidence only."
      },
      {
        "name": "server_secret_store",
        "status": "server_side",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "detail": "Secret reference names are visible, values stay in the private secret store."
      },
      {
        "name": "browser_session",
        "status": "metadata_only",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "detail": "Browser sees onboarding evidence, never provider tokens or raw responses."
      },
      {
        "name": "private_provider_runtime",
        "status": "separate",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "detail": "Real provider API calls belong only in the private connector runtime."
      }
    ],
    "api": {
      "standalone": "GET /demo/provider-onboarding",
      "publicDemo": "GET /demo/public",
      "catalog": "GET /integration-adapters",
      "mappingPreview": "POST /tenants/{tenant_id}/integration-mapping/preview",
      "runtimePreview": "POST /tenants/{tenant_id}/integration-runtime/preview",
      "approvalGateway": "POST /tenants/{tenant_id}/business-approval-gateway/preview"
    },
    "docs": [
      {
        "label": "Provider onboarding",
        "path": "docs/public/PROVIDER_ONBOARDING.md",
        "check": "bash scripts/check_public_provider_onboarding.sh"
      },
      {
        "label": "Provider onboarding evidence",
        "path": "docs/public/evidence/provider-onboarding.sanitized.json",
        "check": "bash scripts/check_public_provider_onboarding.sh"
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
      },
      {
        "label": "Connector certification",
        "path": "docs/public/CONNECTOR_CERTIFICATION.md",
        "check": "bash scripts/check_public_connector_certification.sh"
      }
    ],
    "command": "GET /demo/provider-onboarding"
  },
  "integrationRuntime": {
    "status": "previewed",
    "command": "POST /tenants/{tenant_id}/integration-runtime/preview",
    "summary": [
      {
        "label": "Runtime steps",
        "value": "7",
        "detail": "contract to reconciliation",
        "tone": "blue"
      },
      {
        "label": "Adapter",
        "value": "accounting",
        "detail": "accounting.export.mock",
        "tone": "green"
      },
      {
        "label": "Outbox",
        "value": "ready",
        "detail": "accounting.export.requested",
        "tone": "violet"
      },
      {
        "label": "Provider calls",
        "value": "0",
        "detail": "contract-only public preview",
        "tone": "amber"
      }
    ],
    "adapterKey": "accounting.export.mock",
    "operationKey": "accounting_export_execute",
    "executionMode": "contract_only",
    "operationContract": {
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
    },
    "runtimeSteps": [
      {
        "step": "contract_selected",
        "status": "ready",
        "detail": "accounting.export.mock.accounting_export_execute selected from runtime adapter catalog.",
        "evidence": "adapter_runtime.contract_selected"
      },
      {
        "step": "scope_preflight",
        "status": "available",
        "detail": "accounting:export",
        "evidence": "adapter_runtime.scope_checked"
      },
      {
        "step": "idempotency_prepared",
        "status": "ready",
        "detail": "tenant_id, export_batch_id, documents_hash",
        "evidence": "adapter_runtime.idempotency_prepared"
      },
      {
        "step": "approval_dependency",
        "status": "required",
        "detail": "Provider-changing or operator-review operations remain behind approval gates.",
        "evidence": "adapter_runtime.approval_dependency_attached"
      },
      {
        "step": "outbox_handoff",
        "status": "ready",
        "detail": "accounting.export.requested",
        "evidence": "adapter_runtime.outbox_handoff_prepared"
      },
      {
        "step": "worker_boundary",
        "status": "ready",
        "detail": "POST /tenants/{tenant_id}/integration-exports/accounting",
        "evidence": "adapter_runtime.worker_boundary_selected"
      },
      {
        "step": "reconciliation_plan",
        "status": "ready",
        "detail": "Provider evidence is compared after execution before the operator closes the loop.",
        "evidence": "adapter_runtime.reconciliation_planned"
      }
    ],
    "preflightChecks": [
      {
        "check": "adapter_registered",
        "status": "passed",
        "detail": "accounting.export.mock",
        "externalMutation": false,
        "providerCallEnabled": false,
        "secretRefsVisible": false,
        "evidence": "adapter_runtime.previewed"
      },
      {
        "check": "operation_contract_present",
        "status": "passed",
        "detail": "accounting_export_execute",
        "externalMutation": false,
        "providerCallEnabled": false,
        "secretRefsVisible": false,
        "evidence": "adapter_runtime.previewed"
      },
      {
        "check": "required_scope_available",
        "status": "passed",
        "detail": "accounting:export",
        "externalMutation": false,
        "providerCallEnabled": false,
        "secretRefsVisible": false,
        "evidence": "adapter_runtime.previewed"
      },
      {
        "check": "idempotency_keys_declared",
        "status": "passed",
        "detail": "tenant_id, export_batch_id, documents_hash",
        "externalMutation": false,
        "providerCallEnabled": false,
        "secretRefsVisible": false,
        "evidence": "adapter_runtime.previewed"
      },
      {
        "check": "secret_boundary_server_side",
        "status": "clean",
        "detail": "server_secret_store",
        "externalMutation": false,
        "providerCallEnabled": false,
        "secretRefsVisible": true,
        "evidence": "adapter_runtime.previewed"
      },
      {
        "check": "provider_write_disabled_in_preview",
        "status": "closed",
        "detail": "Runtime preview never calls the external provider.",
        "externalMutation": false,
        "providerCallEnabled": false,
        "secretRefsVisible": false,
        "evidence": "adapter_runtime.previewed"
      }
    ],
    "outboxHandoff": {
      "status": "ready",
      "wouldEnqueueEvent": "accounting.export.requested",
      "adapterKey": "accounting.export.mock",
      "operationKey": "accounting_export_execute",
      "requiredConnectionScope": "accounting:export",
      "idempotencyKeys": [
        "tenant_id",
        "export_batch_id",
        "documents_hash"
      ],
      "retryable": true,
      "deadLetter": true,
      "operatorReview": true,
      "externalMutation": false,
      "providerCallEnabled": false,
      "evidence": "adapter_runtime.outbox_handoff_prepared"
    },
    "workerBoundary": {
      "status": "ready",
      "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
      "workerFunction": "drivedesk_worker.main.process_pending_outbox",
      "executionMode": "contract_only",
      "publicRunMode": "contract_only",
      "externalMutation": false,
      "providerCallEnabled": false,
      "rawPayloadIncluded": false,
      "containsPii": false,
      "evidence": "adapter_runtime.worker_boundary_selected"
    },
    "reconciliationPlan": [
      {
        "step": "capture_expected_result",
        "status": "ready",
        "detail": "Expected adapter result is derived from the operation contract and idempotency key.",
        "externalMutation": false,
        "evidence": "adapter_runtime.reconciliation_planned"
      },
      {
        "step": "compare_provider_evidence",
        "status": "ready",
        "detail": "Provider status, accepted/rejected counts, and external reference are compared after execution.",
        "externalMutation": false,
        "evidence": "adapter_runtime.reconciliation_planned"
      },
      {
        "step": "route_mismatch_to_operator",
        "status": "armed",
        "detail": "Mismatched or blocked evidence becomes an operator review card.",
        "externalMutation": false,
        "evidence": "adapter_runtime.reconciliation_planned"
      }
    ],
    "incidentRoutes": [
      {
        "route": "retry_queue",
        "status": "armed",
        "source": "outbox.retry",
        "runbook": "integration.retry_backlog",
        "externalMutation": false,
        "evidence": "adapter_runtime.incident_route_selected"
      },
      {
        "route": "dead_letter_review",
        "status": "armed",
        "source": "outbox.dead_letter",
        "runbook": "integration.dead_letter",
        "externalMutation": false,
        "evidence": "adapter_runtime.incident_route_selected"
      },
      {
        "route": "reconciliation_mismatch",
        "status": "armed",
        "source": "integration.reconciliation",
        "runbook": "integration.reconciliation_mismatch",
        "externalMutation": false,
        "evidence": "adapter_runtime.incident_route_selected"
      }
    ],
    "dataBoundaries": [
      {
        "name": "contract_only_preview",
        "status": "preview_only",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "secretRefs": [],
        "detail": "The runtime plan is computed without queueing or executing provider work."
      },
      {
        "name": "server_side_secret_boundary",
        "status": "clean",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "secretRefs": [
          "ACCOUNTING_PROVIDER_API_KEY",
          "ACCOUNTING_PROVIDER_ENDPOINT"
        ],
        "detail": "Secret names may be referenced, but secret values are never returned."
      },
      {
        "name": "safe_payload_boundary",
        "status": "clean",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "secretRefs": [],
        "detail": "Runtime preview uses contract metadata and safe references only."
      },
      {
        "name": "approval_before_provider_write",
        "status": "closed",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "secretRefs": [],
        "detail": "Provider mutation remains unavailable until approval and outbox commit exist."
      }
    ],
    "api": {
      "standalone": "GET /demo/integration-runtime",
      "preview": "POST /tenants/{tenant_id}/integration-runtime/preview",
      "adapters": "GET /integration-adapters",
      "runbooks": "GET /integration-runbooks",
      "operatorReview": "GET /tenants/{tenant_id}/integration-operator-review"
    },
    "docs": [
      {
        "label": "Integration runtime",
        "path": "docs/public/INTEGRATION_RUNTIME.md",
        "check": "bash scripts/check_public_integration_runtime.sh"
      },
      {
        "label": "Operation contracts",
        "path": "docs/public/INTEGRATION_OPERATION_CONTRACTS.md",
        "check": "bash scripts/check_public_demo_api.sh"
      },
      {
        "label": "Adapter developer guide",
        "path": "docs/public/ADAPTER_DEVELOPER_GUIDE.md",
        "check": "bash scripts/check_public_adapter_developer_guide.sh"
      }
    ]
  },
  "integrationExecution": {
    "status": "previewed",
    "command": "POST /tenants/{tenant_id}/integration-executions/preview",
    "summary": [
      {
        "label": "Timeline",
        "value": "8",
        "detail": "request to closure",
        "tone": "blue"
      },
      {
        "label": "Run ledger",
        "value": "planned",
        "detail": "run_accounting_export_mock_accounting_export_execute",
        "tone": "green"
      },
      {
        "label": "Provider calls",
        "value": "0",
        "detail": "blocked in public preview",
        "tone": "amber"
      },
      {
        "label": "Recovery",
        "value": "armed",
        "detail": "retry, dead-letter, reconciliation",
        "tone": "violet"
      }
    ],
    "adapterKey": "accounting.export.mock",
    "operationKey": "accounting_export_execute",
    "executionMode": "contract_only",
    "runLedger": {
      "runId": "run_accounting_export_mock_accounting_export_execute",
      "requestId": "public-demo-accounting-export-001",
      "adapterKey": "accounting.export.mock",
      "operationKey": "accounting_export_execute",
      "eventType": "accounting.export.requested",
      "status": "previewed",
      "executionMode": "contract_only",
      "idempotencyFingerprint": "accounting.export.mock:accounting_export_execute:public-demo-accounting-export-001",
      "wouldCreateWorkflowActionRun": true,
      "wouldCreateOutboxEvent": true,
      "wouldCallProvider": false,
      "externalMutation": false,
      "rawPayloadIncluded": false,
      "containsPii": false,
      "evidence": "integration_execution.run_ledger_prepared"
    },
    "timeline": [
      {
        "stage": "request_accepted",
        "status": "ready",
        "detail": "accounting.export.mock.accounting_export_execute execution request accepted.",
        "wouldRecord": "WorkflowActionRun",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_execution.requested"
      },
      {
        "stage": "runtime_preflight",
        "status": "passed",
        "detail": "6 runtime preflight checks evaluated.",
        "wouldRecord": "adapter_runtime.previewed",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_execution.preflight_passed"
      },
      {
        "stage": "approval_gate",
        "status": "locked",
        "detail": "Provider mutation remains locked until approval and idempotent outbox commit.",
        "wouldRecord": "business_approval.requested",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_execution.approval_gate_evaluated"
      },
      {
        "stage": "outbox_enqueue",
        "status": "ready",
        "detail": "accounting.export.requested",
        "wouldRecord": "OutboxEvent",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_execution.outbox_planned"
      },
      {
        "stage": "worker_dispatch",
        "status": "ready",
        "detail": "drivedesk_worker.main.process_pending_outbox",
        "wouldRecord": "worker.outbox.pending",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_execution.worker_dispatch_planned"
      },
      {
        "stage": "provider_call",
        "status": "blocked_in_public_preview",
        "detail": "External provider calls are represented as contract evidence only.",
        "wouldRecord": null,
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_execution.provider_call_blocked"
      },
      {
        "stage": "reconciliation",
        "status": "planned",
        "detail": "Expected internal result is compared with provider evidence after worker completion.",
        "wouldRecord": "IntegrationReconciliation",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_execution.reconciliation_planned"
      },
      {
        "stage": "operator_closure",
        "status": "ready",
        "detail": "Operator receives retry, dead-letter, or reconciliation evidence before closure.",
        "wouldRecord": "IntegrationIncident",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_execution.operator_closure_ready"
      }
    ],
    "stateTransitions": [
      {
        "from": "none",
        "to": "requested",
        "trigger": "POST /tenants/{tenant_id}/integration-executions/preview",
        "evidence": "integration_execution.requested"
      },
      {
        "from": "requested",
        "to": "preflight_passed",
        "trigger": "adapter_runtime.previewed",
        "evidence": "integration_execution.preflight_passed"
      },
      {
        "from": "preflight_passed",
        "to": "queued",
        "trigger": "accounting.export.requested",
        "evidence": "integration_execution.outbox_planned"
      },
      {
        "from": "queued",
        "to": "awaiting_reconciliation",
        "trigger": "worker.outbox.pending",
        "evidence": "integration_execution.worker_dispatch_planned"
      },
      {
        "from": "awaiting_reconciliation",
        "to": "operator_review_ready",
        "trigger": "integration.reconciliation.recorded",
        "evidence": "integration_execution.operator_closure_ready"
      }
    ],
    "retryPolicy": [
      {
        "name": "retry_queue",
        "status": "armed",
        "trigger": "outbox_event.retry_requested",
        "maxAttempts": 3,
        "externalMutation": false,
        "evidence": "integration_execution.retry_policy_attached"
      },
      {
        "name": "dead_letter_review",
        "status": "armed",
        "trigger": "outbox.dead_letter",
        "maxAttempts": 3,
        "externalMutation": false,
        "evidence": "integration_execution.dead_letter_policy_attached"
      }
    ],
    "reconciliationLinks": [
      {
        "name": "expected_result",
        "status": "prepared",
        "source": "operation_contract",
        "wouldRecord": "IntegrationReconciliation.expected_json",
        "evidence": "integration_execution.reconciliation_planned"
      },
      {
        "name": "provider_evidence",
        "status": "redacted",
        "source": "worker_result",
        "wouldRecord": "IntegrationReconciliation.actual_json",
        "evidence": "integration_execution.reconciliation_planned"
      },
      {
        "name": "mismatch_route",
        "status": "armed",
        "source": "integration.reconciliation",
        "wouldRecord": "IntegrationIncident",
        "evidence": "integration_execution.incident_route_armed"
      }
    ],
    "observability": [
      {
        "metric": "drivedesk_workflow_action_runs",
        "status": "planned",
        "labels": [
          "action_type",
          "status"
        ],
        "evidence": "integration_execution.metric_attached"
      },
      {
        "metric": "drivedesk_outbox_events",
        "status": "planned",
        "labels": [
          "adapter_key",
          "status"
        ],
        "evidence": "integration_execution.metric_attached"
      },
      {
        "metric": "drivedesk_integration_reconciliations",
        "status": "planned",
        "labels": [
          "adapter_key",
          "status"
        ],
        "evidence": "integration_execution.metric_attached"
      },
      {
        "metric": "drivedesk_integration_incidents",
        "status": "planned",
        "labels": [
          "adapter_key",
          "severity",
          "status"
        ],
        "evidence": "integration_execution.metric_attached"
      }
    ],
    "dataBoundaries": [
      {
        "name": "preview_only_execution",
        "status": "clean",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "idempotencyKeys": [],
        "detail": "Execution timeline is computed without creating run rows or queueing provider work."
      },
      {
        "name": "idempotency_without_payload",
        "status": "clean",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "idempotencyKeys": [
          "tenant_id",
          "export_batch_id",
          "documents_hash"
        ],
        "detail": "Only idempotency key names and a synthetic fingerprint are shown."
      },
      {
        "name": "provider_result_redaction",
        "status": "clean",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "idempotencyKeys": [],
        "detail": "Provider result payloads are represented by status and evidence references only."
      },
      {
        "name": "operator_review_before_mutation",
        "status": "closed",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "idempotencyKeys": [],
        "detail": "Provider-changing work stays behind approval, outbox, and audit boundaries."
      }
    ],
    "api": {
      "standalone": "GET /demo/integration-execution",
      "preview": "POST /tenants/{tenant_id}/integration-executions/preview",
      "runtimePreview": "POST /tenants/{tenant_id}/integration-runtime/preview",
      "workflowActionRuns": "GET /tenants/{tenant_id}/workflow-action-runs",
      "outbox": "GET /tenants/{tenant_id}/outbox-events",
      "reconciliations": "GET /tenants/{tenant_id}/integration-reconciliations",
      "incidents": "GET /tenants/{tenant_id}/integration-incidents"
    },
    "docs": [
      {
        "label": "Integration execution",
        "path": "docs/public/INTEGRATION_EXECUTION.md",
        "check": "bash scripts/check_public_integration_execution.sh"
      },
      {
        "label": "Integration runtime",
        "path": "docs/public/INTEGRATION_RUNTIME.md",
        "check": "bash scripts/check_public_integration_runtime.sh"
      },
      {
        "label": "Outbox recovery",
        "path": "docs/public/OUTBOX_RECOVERY.md",
        "check": "bash scripts/check_public_demo_api.sh"
      }
    ]
  },
  "integrationRepair": {
    "status": "previewed",
    "repairLevel": "operator_repair_ready",
    "incidentCount": 3,
    "criticalCount": 2,
    "safeActionCount": 1,
    "summary": [
      {
        "label": "Incidents",
        "value": "3",
        "detail": "retry, dead-letter, reconciliation",
        "tone": "amber"
      },
      {
        "label": "Critical",
        "value": "2",
        "detail": "operator review required",
        "tone": "red"
      },
      {
        "label": "Safe actions",
        "value": "1",
        "detail": "diagnostics can run first",
        "tone": "green"
      },
      {
        "label": "Provider writes",
        "value": "0",
        "detail": "blocked in public preview",
        "tone": "violet"
      }
    ],
    "incidentMatrix": [
      {
        "incidentId": "IR-001",
        "sourceType": "outbox_event",
        "sourceStatus": "retry",
        "adapterKey": "accounting.export.mock",
        "operationKey": "accounting_export_execute",
        "status": "retryable",
        "severity": "warning",
        "businessImpact": "Accounting export is delayed but the workflow remains recoverable.",
        "safePayloadSummary": {
          "records": 2,
          "amountBucket": "2001-5000",
          "payloadHashRecorded": true
        },
        "attempts": 2,
        "nextAction": "run_connection_diagnostics",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_repair.retry_backlog_classified"
      },
      {
        "incidentId": "IR-002",
        "sourceType": "outbox_event",
        "sourceStatus": "dead_letter",
        "adapterKey": "crm.bitrix24.mock",
        "operationKey": "crm_deal_ingest_execute",
        "status": "operator_review",
        "severity": "critical",
        "businessImpact": "CRM deal facts are blocked until mapping or scope is corrected.",
        "safePayloadSummary": {
          "records": 1,
          "missingMapping": [
            "deal_id"
          ],
          "payloadHashRecorded": true
        },
        "attempts": 3,
        "nextAction": "fix_mapping_profile",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_repair.dead_letter_classified"
      },
      {
        "incidentId": "IR-003",
        "sourceType": "reconciliation",
        "sourceStatus": "mismatched",
        "adapterKey": "accounting.export.mock",
        "operationKey": "accounting_export_execute",
        "status": "needs_review",
        "severity": "critical",
        "businessImpact": "Provider evidence does not match DriveDesk expected result.",
        "safePayloadSummary": {
          "diffKeys": [
            "records_accepted",
            "provider_status"
          ],
          "providerStatus": "partial_success"
        },
        "attempts": 1,
        "nextAction": "open_reconciliation_review",
        "externalMutation": false,
        "providerCallEnabled": false,
        "evidence": "integration_repair.reconciliation_mismatch_classified"
      }
    ],
    "repairRunbooks": [
      {
        "incidentId": "IR-001",
        "runbookKey": "integration.retry_backlog",
        "title": "Retryable integration backlog",
        "severity": "warning",
        "alertName": "DriveDeskIntegrationRetries",
        "recommendedActions": [
          "Check connection diagnostics for the affected adapter.",
          "Review retryable operator-review items and provider status.",
          "Wait for provider recovery or retry after confirming the failure cleared."
        ],
        "evidenceFields": [
          "adapter_key",
          "operation_key",
          "attempts",
          "last_error",
          "payload_summary"
        ],
        "evidence": "integration_repair.runbook_attached"
      },
      {
        "incidentId": "IR-002",
        "runbookKey": "integration.dead_letter",
        "title": "Dead-lettered integration job",
        "severity": "critical",
        "alertName": "DriveDeskIntegrationDeadLetters",
        "recommendedActions": [
          "Inspect the safe payload summary and required operation scope.",
          "Fix mapping, connection scope, provider contract, or input data.",
          "Requeue the outbox event with an audited operator reason after the fix."
        ],
        "evidenceFields": [
          "adapter_key",
          "operation_key",
          "attempts",
          "last_error",
          "payload_summary"
        ],
        "evidence": "integration_repair.runbook_attached"
      },
      {
        "incidentId": "IR-003",
        "runbookKey": "integration.reconciliation_mismatch",
        "title": "Provider evidence mismatch",
        "severity": "critical",
        "alertName": "DriveDeskIntegrationReconciliationMismatch",
        "recommendedActions": [
          "Review reconciliation diff keys and provider status.",
          "Verify provider dashboard, batch status, and adapter mapping.",
          "Create a corrective task before marking the incident resolved."
        ],
        "evidenceFields": [
          "adapter_key",
          "operation_key",
          "diff_keys",
          "provider_status"
        ],
        "evidence": "integration_repair.runbook_attached"
      }
    ],
    "impactAnalysis": [
      {
        "area": "workflow_delivery",
        "status": "degraded",
        "affectedItems": 2,
        "detail": "Two downstream workflow steps wait for adapter recovery evidence.",
        "externalMutation": false,
        "evidence": "integration_repair.impact.workflow_delivery"
      },
      {
        "area": "financial_reconciliation",
        "status": "at_risk",
        "affectedItems": 1,
        "detail": "One export needs reconciliation review before finance closure.",
        "externalMutation": false,
        "evidence": "integration_repair.impact.financial_reconciliation"
      },
      {
        "area": "operator_queue",
        "status": "actionable",
        "affectedItems": 3,
        "detail": "All incidents have a runbook, owner path, and safe next action.",
        "externalMutation": false,
        "evidence": "integration_repair.impact.operator_queue"
      }
    ],
    "repairActions": [
      {
        "action": "run_connection_diagnostics",
        "target": "accounting.export.mock",
        "status": "safe_dry_run",
        "sourceIncident": "IR-001",
        "requiresApproval": false,
        "safeToAutoRun": true,
        "externalMutation": false,
        "providerCallEnabled": false,
        "rollback": "no_state_change",
        "evidence": "integration_repair.action.diagnostics"
      },
      {
        "action": "retry_after_diagnostics",
        "target": "accounting.export.mock",
        "status": "approval_required",
        "sourceIncident": "IR-001",
        "requiresApproval": true,
        "safeToAutoRun": false,
        "externalMutation": false,
        "providerCallEnabled": false,
        "rollback": "keep_previous_outbox_attempt",
        "evidence": "integration_repair.action.retry"
      },
      {
        "action": "fix_mapping_profile",
        "target": "crm.bitrix24.mock",
        "status": "operator_review",
        "sourceIncident": "IR-002",
        "requiresApproval": true,
        "safeToAutoRun": false,
        "externalMutation": false,
        "providerCallEnabled": false,
        "rollback": "restore_previous_mapping_profile",
        "evidence": "integration_repair.action.mapping_fix"
      },
      {
        "action": "open_reconciliation_review",
        "target": "accounting.export.mock",
        "status": "operator_review",
        "sourceIncident": "IR-003",
        "requiresApproval": false,
        "safeToAutoRun": false,
        "externalMutation": false,
        "providerCallEnabled": false,
        "rollback": "review_only",
        "evidence": "integration_repair.action.reconciliation_review"
      }
    ],
    "safeExecutionPlan": [
      {
        "step": "classify_failure",
        "status": "ready",
        "detail": "Source status selects retry, dead-letter, or reconciliation runbook.",
        "externalMutation": false,
        "evidence": "integration_repair.failure_classified"
      },
      {
        "step": "attach_business_impact",
        "status": "ready",
        "detail": "Operator sees workflow, finance, and queue impact before touching the job.",
        "externalMutation": false,
        "evidence": "integration_repair.impact_attached"
      },
      {
        "step": "prepare_safe_actions",
        "status": "ready",
        "detail": "Diagnostics, mapping fix, retry, and reconciliation review are separated.",
        "externalMutation": false,
        "evidence": "integration_repair.actions_prepared"
      },
      {
        "step": "dry_run_first",
        "status": "enforced",
        "detail": "Public contract exposes only dry-run and review actions.",
        "externalMutation": false,
        "evidence": "integration_repair.dry_run_enforced"
      },
      {
        "step": "approval_before_commit",
        "status": "locked",
        "detail": "Retry or provider-changing repair requires approval and idempotency evidence.",
        "externalMutation": false,
        "evidence": "integration_repair.approval_required"
      },
      {
        "step": "observe_after_repair",
        "status": "planned",
        "detail": "Repair closure requires updated reconciliation, metrics, and incident evidence.",
        "externalMutation": false,
        "evidence": "integration_repair.postcheck_planned"
      }
    ],
    "dataBoundaries": [
      {
        "name": "repair_preview_only",
        "status": "clean",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "providerCallEnabled": false,
        "detail": "The workbench computes repair guidance from synthetic status and evidence references."
      },
      {
        "name": "safe_payload_summary",
        "status": "clean",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "providerCallEnabled": false,
        "detail": "Operators see counts, buckets, diff keys, and hashes instead of raw provider payloads."
      },
      {
        "name": "approval_before_retry",
        "status": "locked",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "providerCallEnabled": false,
        "detail": "State-changing repair remains locked behind approval, idempotency, and audit evidence."
      },
      {
        "name": "private_provider_boundary",
        "status": "closed",
        "containsPii": false,
        "rawPayloadIncluded": false,
        "externalMutation": false,
        "providerCallEnabled": false,
        "detail": "Real provider calls belong only to the private connector runtime."
      }
    ],
    "api": {
      "standalone": "GET /demo/integration-repair",
      "preview": "POST /tenants/{tenant_id}/integration-repairs/preview",
      "operatorReview": "GET /tenants/{tenant_id}/integration-operator-review",
      "retry": "POST /tenants/{tenant_id}/outbox-events/{event_id}/retry",
      "incidents": "GET /tenants/{tenant_id}/integration-incidents",
      "reconciliations": "GET /tenants/{tenant_id}/integration-reconciliations"
    },
    "docs": [
      {
        "label": "Integration repair",
        "path": "docs/public/INTEGRATION_REPAIR.md",
        "check": "bash scripts/check_public_integration_repair.sh"
      },
      {
        "label": "Incident runbooks",
        "path": "docs/public/INTEGRATION_INCIDENT_RUNBOOKS.md",
        "check": "bash scripts/check_public_demo_api.sh"
      },
      {
        "label": "Integration execution",
        "path": "docs/public/INTEGRATION_EXECUTION.md",
        "check": "bash scripts/check_public_integration_execution.sh"
      },
      {
        "label": "Provider onboarding",
        "path": "docs/public/PROVIDER_ONBOARDING.md",
        "check": "bash scripts/check_public_provider_onboarding.sh"
      }
    ],
    "command": "GET /demo/integration-repair"
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
  "businessIntakePipeline": {
    "status": "previewed",
    "command": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
    "summary": [
      {
        "label": "Provider events",
        "value": "3",
        "detail": "CRM, bank, and accounting signals in one preview",
        "tone": "blue"
      },
      {
        "label": "Dropped unsafe keys",
        "value": "5",
        "detail": "PII and credential markers are removed",
        "tone": "green"
      },
      {
        "label": "Detected exceptions",
        "value": "1",
        "detail": "payment mismatch candidate",
        "tone": "amber"
      },
      {
        "label": "External writes",
        "value": "0",
        "detail": "preview-only pipeline",
        "tone": "violet"
      }
    ],
    "sourceSystems": [
      "crm.bitrix24.mock",
      "bank.statement.mock",
      "accounting.export.mock"
    ],
    "intakePreviews": [
      {
        "providerKey": "crm.bitrix24.mock",
        "sourceType": "crm_deal",
        "state": "invoice_sent",
        "safePayload": {
          "amount_bucket": "1000-2000",
          "owner_role": "sales",
          "source_state": "invoice_sent"
        },
        "droppedKeys": [
          "access_token",
          "full_name",
          "phone"
        ],
        "evidence": "business_provider_intake.previewed"
      },
      {
        "providerKey": "bank.statement.mock",
        "sourceType": "bank_payment",
        "state": "paid",
        "safePayload": {
          "amount_bucket": "1000-2000",
          "matched_by": "payment_reference",
          "source_state": "captured"
        },
        "droppedKeys": [
          "payer_phone"
        ],
        "evidence": "business_provider_intake.previewed"
      },
      {
        "providerKey": "accounting.export.mock",
        "sourceType": "accounting_export",
        "state": "not_exported",
        "safePayload": {
          "export_batch_id": "batch-001",
          "reason": "waiting_for_crm_status",
          "source_state": "not_exported"
        },
        "droppedKeys": [
          "session_secret"
        ],
        "evidence": "business_provider_intake.previewed"
      }
    ],
    "workbench": {
      "role": "accountant",
      "riskLevel": "attention",
      "contextCards": [
        {
          "title": "CRM signal",
          "systemFamily": "crm",
          "state": "invoice_sent",
          "status": "needs_cross_check",
          "rawPayloadIncluded": false,
          "piiIncluded": false,
          "externalMutation": false
        },
        {
          "title": "Bank signal",
          "systemFamily": "bank",
          "state": "paid",
          "status": "confirmed",
          "rawPayloadIncluded": false,
          "piiIncluded": false,
          "externalMutation": false
        },
        {
          "title": "Accounting signal",
          "systemFamily": "accounting",
          "state": "not_exported",
          "status": "action_required",
          "rawPayloadIncluded": false,
          "piiIncluded": false,
          "externalMutation": false
        }
      ],
      "suggestedActions": [
        {
          "action": "review_pipeline_detection",
          "status": "action_required",
          "externalMutation": false,
          "evidence": "business_workbench_context.previewed"
        },
        {
          "action": "open_action_plan_preview",
          "status": "ready",
          "externalMutation": false,
          "evidence": "business_action_plan.previewed"
        }
      ]
    },
    "detections": {
      "status": "detected",
      "ruleSet": "payment_reconciliation",
      "detectedExceptions": [
        {
          "exceptionType": "crm_payment_mismatch",
          "severity": "warning",
          "subject": "deal:DEAL-2026-001",
          "wouldCreate": "BusinessException",
          "externalMutation": false
        }
      ],
      "suggestedRepairActions": [
        {
          "actionType": "sync_status",
          "status": "suggested",
          "requiresApproval": true,
          "externalMutation": false,
          "wouldCreate": "RepairAction"
        }
      ]
    },
    "actionPlan": {
      "riskLevel": "attention",
      "steps": [
        {
          "step": "normalize_provider_events",
          "status": "previewed",
          "externalMutation": false,
          "evidence": "business_provider_intake.previewed"
        },
        {
          "step": "open_role_workbench",
          "status": "ready",
          "externalMutation": false,
          "evidence": "business_workbench_context.previewed"
        },
        {
          "step": "review_detected_exceptions",
          "status": "action_required",
          "externalMutation": false,
          "evidence": "business_detection.previewed"
        },
        {
          "step": "prepare_approval_gated_repair",
          "status": "approval_required",
          "externalMutation": false,
          "evidence": "business_action_plan.previewed"
        }
      ],
      "approvalGates": [
        {
          "gate": "external_write_gate",
          "status": "closed"
        },
        {
          "gate": "notification_delivery_gate",
          "status": "approval_required"
        }
      ]
    },
    "notifications": {
      "status": "draft_only",
      "channels": [
        "in_app",
        "telegram",
        "email"
      ],
      "externalDelivery": false,
      "containsPii": false,
      "evidence": "business_notification.previewed"
    },
    "dataBoundaries": [
      {
        "name": "no_external_calls",
        "status": "clean",
        "externalFetch": false,
        "externalMutation": false
      },
      {
        "name": "no_persistence",
        "status": "preview_only",
        "externalMutation": false
      },
      {
        "name": "secret_and_pii_boundary",
        "status": "clean",
        "rawPayloadIncluded": false,
        "piiIncluded": false,
        "requiresSecret": false
      }
    ],
    "api": {
      "preview": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
      "providerIntake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "workbenchContext": "POST /tenants/{tenant_id}/business-workbench-context/preview",
      "detections": "POST /tenants/{tenant_id}/business-detections/preview",
      "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
      "notifications": "POST /tenants/{tenant_id}/business-notifications/preview"
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
    ]
  },
  "businessTaskHandoff": {
    "status": "previewed",
    "command": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
    "summary": [
      {
        "label": "Task cards",
        "value": "2",
        "detail": "internal work preview for accountant",
        "tone": "blue"
      },
      {
        "label": "Internal outbox",
        "value": "2",
        "detail": "task.created candidates only",
        "tone": "green"
      },
      {
        "label": "Draft notifications",
        "value": "2",
        "detail": "in-app drafts, no external send",
        "tone": "amber"
      },
      {
        "label": "External writes",
        "value": "0",
        "detail": "public preview stays internal",
        "tone": "violet"
      }
    ],
    "role": "accountant",
    "subject": "deal:DEAL-2026-001",
    "taskCards": [
      {
        "taskKey": "task.preview.001",
        "title": "review_detected_exceptions",
        "assigneeRole": "accountant",
        "status": "would_create",
        "priority": "normal",
        "sourceAction": "review_detected_exceptions",
        "subject": "deal:DEAL-2026-001",
        "due": "next_business_day",
        "wouldCreate": "BusinessRecord(type=task)",
        "requiresApproval": false,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_task_handoff.previewed"
      },
      {
        "taskKey": "task.preview.002",
        "title": "execute_repair_dry_run",
        "assigneeRole": "accountant",
        "status": "would_create",
        "priority": "high",
        "sourceAction": "execute_repair_dry_run",
        "subject": "deal:DEAL-2026-001",
        "due": "same_day",
        "wouldCreate": "BusinessRecord(type=task)",
        "requiresApproval": true,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_task_handoff.previewed"
      }
    ],
    "outboxCandidates": [
      {
        "eventType": "task.created",
        "adapterKey": "internal.noop",
        "status": "would_enqueue",
        "idempotencyKey": "business-task-handoff:deal:DEAL-2026-001:task-001",
        "payloadProfile": "safe_task_reference",
        "sourceAction": "review_detected_exceptions",
        "containsPii": false,
        "externalMutation": false,
        "evidence": "business_task_handoff.previewed"
      },
      {
        "eventType": "task.created",
        "adapterKey": "internal.noop",
        "status": "would_enqueue",
        "idempotencyKey": "business-task-handoff:deal:DEAL-2026-001:task-002",
        "payloadProfile": "safe_task_reference",
        "sourceAction": "execute_repair_dry_run",
        "containsPii": false,
        "externalMutation": false,
        "evidence": "business_task_handoff.previewed"
      }
    ],
    "notificationDrafts": [
      {
        "draftId": "task_handoff.in_app.accountant.001",
        "channel": "in_app",
        "recipientRole": "accountant",
        "title": "Task handoff ready",
        "body": "deal:DEAL-2026-001 has internal task preview: review_detected_exceptions.",
        "status": "draft_only",
        "externalDelivery": false,
        "containsPii": false,
        "requiresSecret": false,
        "evidence": "business_task_handoff.previewed"
      },
      {
        "draftId": "task_handoff.in_app.accountant.002",
        "channel": "in_app",
        "recipientRole": "accountant",
        "title": "Task handoff ready",
        "body": "deal:DEAL-2026-001 has internal task preview: execute_repair_dry_run.",
        "status": "draft_only",
        "externalDelivery": false,
        "containsPii": false,
        "requiresSecret": false,
        "evidence": "business_task_handoff.previewed"
      }
    ],
    "approvalGates": [
      {
        "gate": "task_creation_review",
        "status": "required",
        "requiresApproval": false,
        "externalMutation": false
      },
      {
        "gate": "external_write_gate",
        "status": "closed",
        "requiresApproval": true,
        "externalMutation": false
      },
      {
        "gate": "repair_action_approval",
        "status": "required",
        "requiresApproval": true,
        "externalMutation": false
      }
    ],
    "dataBoundaries": [
      {
        "name": "preview_only_no_persistence",
        "status": "preview_only",
        "externalMutation": false
      },
      {
        "name": "internal_only_outbox",
        "status": "clean",
        "adapterKey": "internal.noop",
        "externalMutation": false
      },
      {
        "name": "safe_task_payload",
        "status": "clean",
        "rawPayloadIncluded": false,
        "piiIncluded": false,
        "containsPii": false
      }
    ],
    "api": {
      "preview": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
      "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
      "workflowRules": "POST /tenants/{tenant_id}/workflow-rules",
      "taskRecords": "POST /tenants/{tenant_id}/business-records"
    },
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
    ]
  },
  "businessNotificationChannels": {
    "status": "previewed",
    "command": "POST /tenants/{tenant_id}/business-notification-channels/preview",
    "summary": [
      {
        "label": "Channels",
        "value": "5",
        "detail": "in-app, Telegram, email, SMS, webhook",
        "tone": "blue"
      },
      {
        "label": "Internal ready",
        "value": "1",
        "detail": "in-app can stay inside DriveDesk",
        "tone": "green"
      },
      {
        "label": "Draft-only external",
        "value": "4",
        "detail": "private connector setup required",
        "tone": "amber"
      },
      {
        "label": "External deliveries",
        "value": "0",
        "detail": "public preview sends nothing",
        "tone": "violet"
      }
    ],
    "role": "accountant",
    "subject": "deal:DEAL-2026-001",
    "channels": [
      {
        "channel": "in_app",
        "status": "ready",
        "configured": true,
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "destinationProfile": "internal_user_inbox",
        "sendMode": "internal_preview",
        "readiness": "usable_for_internal_work",
        "externalDelivery": false,
        "requiresSecret": false,
        "requiresPrivateConnector": false,
        "externalProviderMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "safePayloadProfile": "role_subject_action_reference",
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "channel": "telegram",
        "status": "requires_private_secret",
        "configured": false,
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "destinationProfile": "telegram_bot_chat",
        "sendMode": "draft_only",
        "readiness": "private_connector_needed",
        "externalDelivery": false,
        "requiresSecret": true,
        "requiresPrivateConnector": true,
        "externalProviderMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "safePayloadProfile": "role_subject_action_reference",
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "channel": "email",
        "status": "requires_private_secret",
        "configured": false,
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "destinationProfile": "smtp_or_provider_template",
        "sendMode": "draft_only",
        "readiness": "private_connector_needed",
        "externalDelivery": false,
        "requiresSecret": true,
        "requiresPrivateConnector": true,
        "externalProviderMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "safePayloadProfile": "role_subject_action_reference",
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "channel": "sms",
        "status": "requires_private_provider",
        "configured": false,
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "destinationProfile": "sms_provider_template",
        "sendMode": "draft_only",
        "readiness": "provider_contract_needed",
        "externalDelivery": false,
        "requiresSecret": true,
        "requiresPrivateConnector": true,
        "externalProviderMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "safePayloadProfile": "role_subject_action_reference",
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "channel": "webhook",
        "status": "requires_private_endpoint",
        "configured": false,
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "destinationProfile": "signed_webhook_endpoint",
        "sendMode": "draft_only",
        "readiness": "endpoint_and_signing_key_needed",
        "externalDelivery": false,
        "requiresSecret": true,
        "requiresPrivateConnector": true,
        "externalProviderMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "safePayloadProfile": "role_subject_action_reference",
        "evidence": "business_notification_channel_matrix.previewed"
      }
    ],
    "routingRules": [
      {
        "rule": "prefer_internal_in_app",
        "status": "ready",
        "channel": "in_app",
        "detail": "Internal work notifications can be represented without external delivery.",
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "rule": "external_channels_require_private_connector",
        "status": "required",
        "channelCount": 4,
        "detail": "External delivery stays behind private connector and secret setup.",
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "rule": "safe_payload_only",
        "status": "clean",
        "payloadProfile": "role_subject_action_reference",
        "detail": "Drafts use role, subject key, action reference, and evidence labels only.",
        "evidence": "business_notification_channel_matrix.previewed"
      }
    ],
    "deliveryDrafts": [
      {
        "draftId": "channel_matrix.in_app.accountant",
        "channel": "in_app",
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "status": "ready",
        "sendMode": "internal_preview",
        "wouldEnqueueEvent": "notification.delivery.requested",
        "safePayloadProfile": "role_subject_action_reference",
        "externalDelivery": false,
        "requiresSecret": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "draftId": "channel_matrix.telegram.accountant",
        "channel": "telegram",
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "status": "draft_only",
        "sendMode": "draft_only",
        "wouldEnqueueEvent": "notification.delivery.requested",
        "safePayloadProfile": "role_subject_action_reference",
        "externalDelivery": false,
        "requiresSecret": true,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "draftId": "channel_matrix.email.accountant",
        "channel": "email",
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "status": "draft_only",
        "sendMode": "draft_only",
        "wouldEnqueueEvent": "notification.delivery.requested",
        "safePayloadProfile": "role_subject_action_reference",
        "externalDelivery": false,
        "requiresSecret": true,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "draftId": "channel_matrix.sms.accountant",
        "channel": "sms",
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "status": "draft_only",
        "sendMode": "draft_only",
        "wouldEnqueueEvent": "notification.delivery.requested",
        "safePayloadProfile": "role_subject_action_reference",
        "externalDelivery": false,
        "requiresSecret": true,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "draftId": "channel_matrix.webhook.accountant",
        "channel": "webhook",
        "recipientRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "title": "DriveDesk action update",
        "body": "deal:DEAL-2026-001 has an operator action ready for accountant.",
        "status": "draft_only",
        "sendMode": "draft_only",
        "wouldEnqueueEvent": "notification.delivery.requested",
        "safePayloadProfile": "role_subject_action_reference",
        "externalDelivery": false,
        "requiresSecret": true,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_notification_channel_matrix.previewed"
      }
    ],
    "approvalGates": [
      {
        "gate": "notification_content_review",
        "status": "ready",
        "requiresApproval": false,
        "externalDelivery": false,
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "gate": "private_channel_secret_setup",
        "status": "required",
        "requiresApproval": true,
        "externalDelivery": false,
        "evidence": "business_notification_channel_matrix.previewed"
      },
      {
        "gate": "external_delivery_gate",
        "status": "closed",
        "requiresApproval": true,
        "externalDelivery": false,
        "evidence": "business_notification_channel_matrix.previewed"
      }
    ],
    "dataBoundaries": [
      {
        "name": "preview_only_no_delivery",
        "status": "preview_only",
        "externalDelivery": false,
        "externalProviderMutation": false
      },
      {
        "name": "server_secret_store_boundary",
        "status": "documented",
        "requiresSecret": true,
        "browserTokenStorage": false
      },
      {
        "name": "safe_notification_payload",
        "status": "clean",
        "containsPii": false,
        "rawPayloadIncluded": false
      }
    ],
    "api": {
      "preview": "POST /tenants/{tenant_id}/business-notification-channels/preview",
      "notifications": "POST /tenants/{tenant_id}/business-notifications/preview",
      "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview"
    },
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
    ]
  },
  "businessContextAssistant": {
    "status": "previewed",
    "command": "POST /tenants/{tenant_id}/business-workbench-context/preview",
    "summary": [
      {
        "label": "Context cards",
        "value": "4",
        "detail": "CRM, bank, accounting, legal reference",
        "tone": "blue"
      },
      {
        "label": "Source systems",
        "value": "4",
        "detail": "safe facts normalized into one work surface",
        "tone": "green"
      },
      {
        "label": "Suggested actions",
        "value": "4",
        "detail": "operator-review and draft-only next steps",
        "tone": "amber"
      },
      {
        "label": "External writes",
        "value": "0",
        "detail": "context preview never mutates providers",
        "tone": "violet"
      }
    ],
    "role": "accountant",
    "subject": "deal:DEAL-2026-001",
    "sourceSystems": [
      "crm.bitrix24.mock",
      "bank.statement.mock",
      "accounting.export.mock",
      "legal.reference.mock"
    ],
    "contextCards": [
      {
        "id": "context.crm.deal-state",
        "title": "CRM deal state",
        "sourceSystem": "crm.bitrix24.mock",
        "systemFamily": "crm",
        "status": "attention",
        "safeFact": "invoice_sent",
        "reason": "CRM stage expects payment confirmation before accounting export.",
        "externalFetch": false,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_workbench_context.previewed"
      },
      {
        "id": "context.bank.payment-evidence",
        "title": "Bank payment evidence",
        "sourceSystem": "bank.statement.mock",
        "systemFamily": "bank",
        "status": "ready",
        "safeFact": "amount_bucket:1000-2000",
        "reason": "Bank statement has a matching amount bucket but no raw payer details are exposed.",
        "externalFetch": false,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_workbench_context.previewed"
      },
      {
        "id": "context.accounting.export-gap",
        "title": "Accounting export gap",
        "sourceSystem": "accounting.export.mock",
        "systemFamily": "accounting",
        "status": "action_required",
        "safeFact": "export_pending",
        "reason": "Payment can be reconciled before the accounting export is queued.",
        "externalFetch": false,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_workbench_context.previewed"
      },
      {
        "id": "context.legal.policy-reference",
        "title": "Policy reference",
        "sourceSystem": "legal.reference.mock",
        "systemFamily": "legal",
        "status": "documented",
        "safeFact": "payment_status_note_template",
        "reason": "The operator gets a template reference, not copied legal text or external account data.",
        "externalFetch": false,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "fullTextIncluded": false,
        "evidence": "business_workbench_context.previewed"
      }
    ],
    "insightRules": [
      {
        "rule": "correlate_payment_evidence",
        "status": "ready",
        "sources": [
          "crm.bitrix24.mock",
          "bank.statement.mock"
        ],
        "result": "bank amount bucket can support CRM payment review",
        "externalMutation": false,
        "evidence": "business_workbench_context.previewed"
      },
      {
        "rule": "detect_accounting_export_gap",
        "status": "attention",
        "sources": [
          "accounting.export.mock"
        ],
        "result": "accounting export remains pending until operator review",
        "externalMutation": false,
        "evidence": "business_workbench_context.previewed"
      },
      {
        "rule": "attach_policy_reference",
        "status": "documented",
        "sources": [
          "legal.reference.mock"
        ],
        "result": "operator sees a policy/template reference without copied external content",
        "externalMutation": false,
        "fullTextIncluded": false,
        "evidence": "business_workbench_context.previewed"
      }
    ],
    "suggestedActions": [
      {
        "action": "open_reconciliation_plan",
        "status": "recommended",
        "mode": "operator_review",
        "endpoint": "POST /tenants/{tenant_id}/business-action-plans/preview",
        "externalMutation": false,
        "requiresApproval": false,
        "evidence": "business_action_plan.previewed"
      },
      {
        "action": "queue_accounting_export_after_review",
        "status": "approval_required",
        "mode": "approval_required",
        "endpoint": "POST /tenants/{tenant_id}/integration-exports/accounting",
        "externalMutation": false,
        "requiresApproval": true,
        "evidence": "accounting.export.requested"
      },
      {
        "action": "attach_policy_reference",
        "status": "ready",
        "mode": "internal_reference",
        "endpoint": "docs/public/BUSINESS_CONTEXT_ASSISTANT.md",
        "externalMutation": false,
        "requiresApproval": false,
        "evidence": "business_workbench_context.previewed"
      },
      {
        "action": "prepare_internal_notification",
        "status": "draft_only",
        "mode": "draft_only",
        "endpoint": "POST /tenants/{tenant_id}/business-notification-channels/preview",
        "externalMutation": false,
        "requiresApproval": false,
        "evidence": "business_notification_channel_matrix.previewed"
      }
    ],
    "dataBoundaries": [
      {
        "name": "read_only_context_preview",
        "status": "preview_only",
        "externalFetch": false,
        "externalMutation": false
      },
      {
        "name": "no_raw_provider_payload",
        "status": "clean",
        "rawPayloadIncluded": false,
        "containsPii": false
      },
      {
        "name": "secret_boundary",
        "status": "clean",
        "requiresSecret": false,
        "browserTokenStorage": false
      },
      {
        "name": "legal_reference_link_only",
        "status": "documented",
        "fullTextIncluded": false,
        "externalAccountDataIncluded": false
      }
    ],
    "api": {
      "standalone": "GET /demo/business-context-assistant",
      "preview": "POST /tenants/{tenant_id}/business-workbench-context/preview",
      "providerIntake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
      "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview"
    },
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
    ]
  },
  "businessActionExecution": {
    "status": "previewed",
    "command": "POST /tenants/{tenant_id}/business-action-executions/preview",
    "summary": [
      {
        "label": "Execution plans",
        "value": "3",
        "detail": "review, accounting export, notification",
        "tone": "blue"
      },
      {
        "label": "Preflight checks",
        "value": "4",
        "detail": "payload, idempotency, approval, secrets",
        "tone": "green"
      },
      {
        "label": "Approval gates",
        "value": "3",
        "detail": "operator review and provider write boundaries",
        "tone": "amber"
      },
      {
        "label": "External writes",
        "value": "0",
        "detail": "dry-run preview sends nothing",
        "tone": "violet"
      }
    ],
    "role": "accountant",
    "subject": "deal:DEAL-2026-001",
    "executionPlan": [
      {
        "executionKey": "execution.preview.001",
        "action": "open_reconciliation_plan",
        "status": "dry_run_ready",
        "mode": "dry_run",
        "adapterKey": "internal.noop",
        "wouldEnqueueEvent": "business.action.review_requested",
        "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:open_reconciliation_plan:001",
        "safePayloadProfile": "role_subject_action_reference",
        "dryRun": true,
        "safeToAutoRun": true,
        "requiresApproval": false,
        "commitWouldMutateProvider": false,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "executionKey": "execution.preview.002",
        "action": "queue_accounting_export_after_review",
        "status": "approval_required",
        "mode": "dry_run",
        "adapterKey": "accounting.export.mock",
        "wouldEnqueueEvent": "accounting.export.requested",
        "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:queue_accounting_export_after_review:002",
        "safePayloadProfile": "role_subject_action_reference",
        "dryRun": true,
        "safeToAutoRun": false,
        "requiresApproval": true,
        "commitWouldMutateProvider": true,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "executionKey": "execution.preview.003",
        "action": "prepare_internal_notification",
        "status": "dry_run_ready",
        "mode": "dry_run",
        "adapterKey": "internal.notification",
        "wouldEnqueueEvent": "notification.delivery.requested",
        "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:prepare_internal_notification:003",
        "safePayloadProfile": "role_subject_action_reference",
        "dryRun": true,
        "safeToAutoRun": true,
        "requiresApproval": false,
        "commitWouldMutateProvider": false,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_action_execution.previewed"
      }
    ],
    "preflightChecks": [
      {
        "check": "safe_payload_profile",
        "status": "passed",
        "detail": "Only role, subject key, action key, and evidence references are included.",
        "externalMutation": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "check": "idempotency_key_ready",
        "status": "passed",
        "detail": "Every execution candidate has a deterministic idempotency key.",
        "externalMutation": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "check": "approval_gate_attached",
        "status": "required",
        "detail": "Provider-changing commits stay behind operator approval.",
        "externalMutation": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "check": "connector_secret_boundary",
        "status": "clean",
        "detail": "Preview does not require credentials or browser token storage.",
        "externalMutation": false,
        "requiresSecret": false,
        "browserTokenStorage": false,
        "evidence": "business_action_execution.previewed"
      }
    ],
    "dryRunResults": [
      {
        "resultKey": "dry_run.001",
        "action": "open_reconciliation_plan",
        "status": "would_enqueue",
        "wouldRecord": "WorkflowActionRun",
        "wouldEnqueueEvent": "business.action.review_requested",
        "adapterKey": "internal.noop",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "resultKey": "dry_run.002",
        "action": "queue_accounting_export_after_review",
        "status": "would_enqueue",
        "wouldRecord": "WorkflowActionRun",
        "wouldEnqueueEvent": "accounting.export.requested",
        "adapterKey": "accounting.export.mock",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "resultKey": "dry_run.003",
        "action": "prepare_internal_notification",
        "status": "would_enqueue",
        "wouldRecord": "WorkflowActionRun",
        "wouldEnqueueEvent": "notification.delivery.requested",
        "adapterKey": "internal.notification",
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_action_execution.previewed"
      }
    ],
    "approvalGates": [
      {
        "gate": "operator_review_gate",
        "status": "required",
        "requiresApproval": true,
        "externalMutation": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "gate": "external_write_gate",
        "status": "closed",
        "requiresApproval": true,
        "externalMutation": false,
        "evidence": "business_action_execution.previewed"
      },
      {
        "gate": "idempotent_outbox_gate",
        "status": "ready",
        "requiresApproval": false,
        "externalMutation": false,
        "evidence": "business_action_execution.previewed"
      }
    ],
    "rollbackPlan": [
      {
        "step": "preview_has_no_rollback",
        "status": "not_needed",
        "detail": "Dry-run preview writes nothing and has no external state to roll back.",
        "externalMutation": false
      },
      {
        "step": "commit_uses_outbox_recovery",
        "status": "documented",
        "detail": "Future commit execution uses outbox retry, dead-letter review, and audit evidence.",
        "externalMutation": false
      }
    ],
    "dataBoundaries": [
      {
        "name": "dry_run_only",
        "status": "preview_only",
        "externalMutation": false
      },
      {
        "name": "no_provider_write",
        "status": "closed",
        "externalMutation": false
      },
      {
        "name": "safe_execution_payload",
        "status": "clean",
        "containsPii": false,
        "rawPayloadIncluded": false
      },
      {
        "name": "audit_and_outbox_contract",
        "status": "documented",
        "externalMutation": false
      }
    ],
    "api": {
      "standalone": "GET /demo/business-action-execution",
      "preview": "POST /tenants/{tenant_id}/business-action-executions/preview",
      "actionPlan": "POST /tenants/{tenant_id}/business-action-plans/preview",
      "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
      "repairExecute": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute"
    },
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
    ]
  },
  "businessApprovalGateway": {
    "status": "previewed",
    "command": "POST /tenants/{tenant_id}/business-approval-gateway/preview",
    "summary": [
      {
        "label": "Approval requests",
        "value": "1",
        "detail": "provider-changing commit candidate",
        "tone": "amber"
      },
      {
        "label": "Policy checks",
        "value": "4",
        "detail": "RBAC, dual control, idempotency, write lock",
        "tone": "green"
      },
      {
        "label": "Commit unlocks",
        "value": "1",
        "detail": "blocked until approved",
        "tone": "blue"
      },
      {
        "label": "Provider writes",
        "value": "0",
        "detail": "approval preview unlocks nothing",
        "tone": "violet"
      }
    ],
    "role": "accountant",
    "subject": "deal:DEAL-2026-001",
    "approvalRequests": [
      {
        "approvalKey": "approval.preview.001",
        "action": "queue_accounting_export_after_review",
        "status": "approval_required",
        "requesterRole": "accountant",
        "approverRole": "owner",
        "subject": "deal:DEAL-2026-001",
        "idempotencyKey": "business-approval-gateway:deal:DEAL-2026-001:queue_accounting_export_after_review:001",
        "sourceIdempotencyKey": "business-action-execution:deal:DEAL-2026-001:queue_accounting_export_after_review:002",
        "requiresDualControl": true,
        "commitWouldMutateProvider": true,
        "externalMutation": false,
        "containsPii": false,
        "rawPayloadIncluded": false,
        "evidence": "business_approval_gateway.previewed"
      }
    ],
    "policyChecks": [
      {
        "check": "rbac_approver_role",
        "status": "passed",
        "detail": "Approver role is allowed to review provider-changing commits.",
        "externalMutation": false,
        "evidence": "business_approval_gateway.previewed"
      },
      {
        "check": "dual_control_required",
        "status": "required",
        "detail": "Requester and approver stay separated before commit unlock.",
        "externalMutation": false,
        "evidence": "business_approval_gateway.previewed"
      },
      {
        "check": "idempotency_preserved",
        "status": "passed",
        "detail": "Approval request keeps source and approval idempotency keys.",
        "externalMutation": false,
        "evidence": "business_approval_gateway.previewed"
      },
      {
        "check": "provider_write_closed_until_approval",
        "status": "closed",
        "detail": "Provider write stays locked until approval is recorded.",
        "externalMutation": false,
        "evidence": "business_approval_gateway.previewed"
      }
    ],
    "approverRouting": [
      {
        "route": "owner_or_accountant_review",
        "status": "ready",
        "queue": "approval.review",
        "ownerRole": "owner",
        "slaMinutes": 120,
        "notificationChannel": "in_app",
        "externalDelivery": false,
        "evidence": "business_approval_gateway.previewed"
      },
      {
        "route": "escalate_if_sla_missed",
        "status": "armed",
        "queue": "approval.escalation",
        "ownerRole": "owner",
        "slaMinutes": 240,
        "notificationChannel": "in_app",
        "externalDelivery": false,
        "evidence": "business_approval_gateway.previewed"
      }
    ],
    "commitUnlocks": [
      {
        "unlockKey": "commit.unlock.001",
        "action": "queue_accounting_export_after_review",
        "status": "blocked_until_approved",
        "wouldRecord": "WorkflowActionRun",
        "wouldEnqueueEvent": "business.action.approval_granted",
        "outboxReady": true,
        "providerWriteUnlocked": false,
        "externalMutation": false,
        "rollbackAttached": true,
        "evidence": "business_approval_gateway.previewed"
      }
    ],
    "auditTrail": [
      {
        "event": "business_approval.requested",
        "status": "would_record",
        "actorRole": "accountant",
        "subject": "deal:DEAL-2026-001",
        "externalMutation": false,
        "evidence": "business_approval_gateway.previewed"
      },
      {
        "event": "business_approval.policy_checked",
        "status": "would_record",
        "actorRole": "system",
        "subject": "deal:DEAL-2026-001",
        "externalMutation": false,
        "evidence": "business_approval_gateway.previewed"
      },
      {
        "event": "business_approval.commit_unlocked",
        "status": "blocked_until_approved",
        "actorRole": "owner",
        "subject": "deal:DEAL-2026-001",
        "externalMutation": false,
        "evidence": "business_approval_gateway.previewed"
      }
    ],
    "dataBoundaries": [
      {
        "name": "preview_only_no_approval_record",
        "status": "preview_only",
        "externalMutation": false
      },
      {
        "name": "provider_write_locked",
        "status": "closed",
        "externalMutation": false
      },
      {
        "name": "rbac_dual_control",
        "status": "enforced",
        "externalMutation": false
      },
      {
        "name": "safe_approval_payload",
        "status": "clean",
        "containsPii": false,
        "rawPayloadIncluded": false
      }
    ],
    "api": {
      "standalone": "GET /demo/business-approval-gateway",
      "preview": "POST /tenants/{tenant_id}/business-approval-gateway/preview",
      "actionExecution": "POST /tenants/{tenant_id}/business-action-executions/preview",
      "taskHandoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview"
    },
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
