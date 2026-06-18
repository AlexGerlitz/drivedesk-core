# Backup And Restore Evidence

DriveDesk treats backup/restore as an operational contract, not a manual note.
The public repository includes a safe recovery drill that can be run locally or
in CI without touching private infrastructure.

## Command

```bash
bash scripts/check_public_backup_restore.sh
```

## What The Drill Does

The script creates a temporary synthetic database, builds the current DriveDesk
Core schema, writes a backup artifact, restores it into a second temporary
database, and validates the restored state.

The drill verifies:

- schema creation through the current SQLAlchemy models;
- SQLite backup artifact creation;
- source, backup, and restored database integrity;
- restored row counts for tenant, user, membership, business record, outbox,
  audit, integration connection, health-check, reconciliation, and incident
  tables;
- restored tenant slug;
- restored `backup_restore.drill.completed` audit event;
- SHA-256 evidence for the backup artifact.

## Evidence Shape

The script emits JSON like this:

```json
{
  "schema_version": 1,
  "drill": "public_synthetic_backup_restore",
  "data_profile": "synthetic_fake_data",
  "backup_format": "sqlite_backup",
  "checks": {
    "source_integrity_ok": true,
    "backup_integrity_ok": true,
    "restore_integrity_ok": true,
    "counts_match": true,
    "core_tables_present": true,
    "tenant_slug_restored": true,
    "drill_audit_event_restored": true,
    "backup_sha256_recorded": true,
    "production_data_touched": false
  }
}
```

## Redaction Boundary

The public drill uses only synthetic fake data. It does not include private
paths, hostnames, addresses, raw logs, credentials, or production data.

The static public evidence snapshot is stored at:

```text
docs/public/evidence/backup-restore-drill.sanitized.json
```

## Why This Matters

For operations work, a backup is only useful if restore is tested. This drill
gives the public project a repeatable proof that recovery checks exist while
keeping the real private recovery process separate.
