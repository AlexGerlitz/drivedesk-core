window.DRIVEDESK_DEMO_DATA = {
  "schemaVersion": 1,
  "generatedAt": "2026-06-17T08:20:00Z",
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
      "value": "34",
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
      "value": "9",
      "detail": "generated contract",
      "tone": "violet"
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
    }
  ],
  "adapters": [
    {
      "key": "file.import.fake",
      "name": "Fake File Import",
      "status": "active",
      "contract": "Normalizes provider rows, returns accepted and rejected record counts, and stores the result on the outbox event."
    },
    {
      "key": "internal.noop",
      "name": "Internal Noop",
      "status": "active",
      "contract": "Acknowledges internal domain events without calling an external provider."
    },
    {
      "key": "accounting.export.mock",
      "name": "Accounting Export",
      "status": "planned",
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
      "state": "next",
      "progress": 10
    }
  ]
};
