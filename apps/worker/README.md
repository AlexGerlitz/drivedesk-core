# DriveDesk Worker

Run locally from the repository root:

```bash
PYTHONPATH=apps/api:apps/worker:packages/core python -m drivedesk_worker.main
```

Sprint 0 worker behavior emits a heartbeat. Sprint 1 adds an outbox skeleton:
each worker loop reads pending `dd_outbox_events` rows and marks them
processed.

External delivery is not implemented yet. Future jobs can attach integration
retries, dead-letter handling, notifications, and analytics tasks here.
