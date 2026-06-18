# ADR-0043: Public-Safe Backup Restore Drill

Status: accepted

## Context

DriveDesk already has public smoke checks, generated OpenAPI evidence,
observability docs, integration recovery, and incident runbooks. The next
production-grade DevOps question is:

```text
Can this platform prove that data can be backed up and restored?
```

The private production and staging environments may contain operational details
that must not be copied into the public repository. The public project still
needs a repeatable recovery proof that runs locally and in CI.

## Decision

Add a public-safe backup/restore drill:

```text
scripts/check_public_backup_restore.sh
```

The drill:

- creates a temporary SQLite database;
- creates the current DriveDesk Core schema through SQLAlchemy metadata;
- seeds only synthetic tenant, user, membership, business record, outbox,
  integration connection, reconciliation, incident, and audit rows;
- writes a SQLite backup artifact in the temporary workspace;
- restores that backup into a separate temporary database;
- runs SQLite integrity checks;
- verifies restored row counts and required Core tables;
- emits a machine-readable JSON summary;
- deletes temporary files when the process exits.

## Public Evidence

The public evidence file is:

```text
docs/public/evidence/backup-restore-drill.sanitized.json
```

It records the shape of the drill and the expected checks without private
paths, hostnames, addresses, raw logs, credentials, or production data.

## Consequences

- The recovery check can run without access to private systems.
- Public CI can prove the exported project has a working backup/restore
  contract.
- The check uses current application models, so schema drift is caught.
- The public drill is not a substitute for private production restore drills.
  It is a public-safe proof of the recovery pattern.
