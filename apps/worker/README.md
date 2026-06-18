# DriveDesk Worker

Run locally from the repository root:

```bash
PYTHONPATH=apps/api:apps/worker:packages/core python -m drivedesk_worker.main
```

Sprint 0 worker behavior emits a heartbeat. Sprint 1 added an outbox skeleton.
Sprint 3 adds adapter execution:

- pending internal events pass through `internal.noop`;
- fake file import events pass through `file.import.fake`;
- mock accounting export events pass through `accounting.export.mock`;
- retryable adapter errors become `retry` with `next_retry_at`;
- permanent errors become `dead_letter`;
- successful adapter results are stored in `result_json`.
