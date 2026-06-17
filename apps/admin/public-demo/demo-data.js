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
      "value": "23",
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
      "contract": "Normalizes provider rows, returns accepted and rejected record counts, and stores the result on the outbox event."
    },
    {
      "key": "internal.noop",
      "name": "Internal Noop",
      "status": "active",
      "direction": "internal",
      "connectionProfileSupported": false,
      "contract": "Acknowledges internal domain events without calling an external provider."
    },
    {
      "key": "accounting.export.mock",
      "name": "Accounting Export",
      "status": "planned",
      "direction": "outbound",
      "connectionProfileSupported": true,
      "contract": "Future adapter boundary for accounting exports and reconciliation status."
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
      "state": "design",
      "progress": 15
    },
    {
      "name": "Public demo runtime",
      "state": "active",
      "progress": 35
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
