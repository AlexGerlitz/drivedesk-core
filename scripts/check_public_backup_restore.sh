#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

cd "$ROOT"

if [[ -n "${DRIVEDESK_PYTHON:-}" && -x "$DRIVEDESK_PYTHON" ]]; then
  PYTHON_BIN="$DRIVEDESK_PYTHON"
elif [[ -n "${PUBLIC_EXPORT_PYTHON:-}" && -x "$PUBLIC_EXPORT_PYTHON" ]]; then
  PYTHON_BIN="$PUBLIC_EXPORT_PYTHON"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "ERROR: python is required" >&2
  exit 1
fi

export PYTHONPATH="$ROOT/apps/api:$ROOT/apps/worker:$ROOT/packages/core${PYTHONPATH:+:$PYTHONPATH}"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from drivedesk_api.db import (
    AuditEvent,
    Base,
    BusinessRecord,
    IntegrationConnection,
    IntegrationConnectionCheck,
    IntegrationIncident,
    IntegrationReconciliation,
    Membership,
    OutboxEvent,
    Tenant,
    User,
)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _integrity_check(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])


def _backup_sqlite(source: Path, target: Path) -> None:
    with sqlite3.connect(source) as source_connection:
        with sqlite3.connect(target) as target_connection:
            source_connection.backup(target_connection)


def _counts(session: Session) -> dict[str, int]:
    models = {
        "tenants": Tenant,
        "users": User,
        "memberships": Membership,
        "business_records": BusinessRecord,
        "outbox_events": OutboxEvent,
        "audit_events": AuditEvent,
        "integration_connections": IntegrationConnection,
        "integration_connection_checks": IntegrationConnectionCheck,
        "integration_reconciliations": IntegrationReconciliation,
        "integration_incidents": IntegrationIncident,
    }
    return {
        name: int(session.scalar(select(func.count()).select_from(model)) or 0)
        for name, model in models.items()
    }


def _seed_source_database(path: Path) -> dict[str, int]:
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)

    now = datetime.now(UTC)
    with Session(engine) as session:
        tenant = Tenant(
            id="tenant-demo",
            slug="demo-academy",
            name="DriveDesk Demo Academy",
            status="active",
        )
        owner = User(
            id="user-owner",
            email="owner@example.test",
            display_name="Demo Owner",
            credential_hash="synthetic-hash",
            status="active",
        )
        session.add_all(
            [
                tenant,
                owner,
                Membership(
                    id="membership-owner",
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role="owner",
                    status="active",
                ),
                BusinessRecord(
                    id="record-contract",
                    tenant_id=tenant.id,
                    record_type="contract",
                    status="approved",
                    title="Synthetic training contract",
                    external_ref="DEMO-CONTRACT",
                    payload_json=json.dumps({"data_profile": "synthetic_demo_data"}, sort_keys=True),
                ),
                BusinessRecord(
                    id="record-task",
                    tenant_id=tenant.id,
                    record_type="task",
                    status="open",
                    title="Synthetic restore evidence review",
                    external_ref="DEMO-TASK",
                    payload_json=json.dumps({"owner": "platform"}, sort_keys=True),
                ),
                OutboxEvent(
                    id="outbox-sync",
                    tenant_id=tenant.id,
                    event_type="student.sync.requested",
                    adapter_key="file.import.fake",
                    payload_json=json.dumps({"source": "public_restore_drill"}, sort_keys=True),
                    result_json=json.dumps({"accepted": 1, "rejected": 0}, sort_keys=True),
                    status="processed",
                    attempts=1,
                    processed_at=now,
                ),
                IntegrationConnection(
                    id="connection-file",
                    tenant_id=tenant.id,
                    name="Synthetic File Import",
                    adapter_key="file.import.fake",
                    status="active",
                    config_json=json.dumps({"data_profile": "synthetic_demo_data"}, sort_keys=True),
                    mapping_json=json.dumps(
                        {"lead_id": "external_id", "full_name": "display_name"},
                        sort_keys=True,
                    ),
                    scopes_json=json.dumps(["file_import:preview", "file_import:execute"], sort_keys=True),
                ),
                IntegrationConnectionCheck(
                    id="connection-check",
                    tenant_id=tenant.id,
                    integration_connection_id="connection-file",
                    adapter_key="file.import.fake",
                    status="success",
                    summary="Synthetic connection check passed",
                    details_json=json.dumps({"scope_check": "ok"}, sort_keys=True),
                    duration_ms=8.0,
                ),
                IntegrationReconciliation(
                    id="reconciliation-match",
                    tenant_id=tenant.id,
                    outbox_event_id="outbox-sync",
                    adapter_key="file.import.fake",
                    operation_key="file_import_execute",
                    status="matched",
                    summary="Synthetic provider evidence matched",
                    expected_json=json.dumps({"accepted": 1}, sort_keys=True),
                    actual_json=json.dumps({"accepted": 1}, sort_keys=True),
                    diff_json=json.dumps({}, sort_keys=True),
                ),
                IntegrationIncident(
                    id="incident-resolved",
                    tenant_id=tenant.id,
                    source_type="reconciliation",
                    source_id="reconciliation-match",
                    adapter_key="file.import.fake",
                    operation_key="file_import_execute",
                    runbook_key="integration.reconciliation_pending",
                    severity="info",
                    status="resolved",
                    summary="Synthetic restore drill incident",
                    recommended_action="Review restored counts before closing the drill.",
                    evidence_json=json.dumps({"raw_records_redacted": True}, sort_keys=True),
                    resolved_at=now + timedelta(seconds=1),
                ),
                AuditEvent(
                    id="audit-restore-drill",
                    tenant_id=tenant.id,
                    actor_id="public-drill",
                    event_type="backup_restore.drill.completed",
                    entity_type="backup_restore_drill",
                    entity_id="public-synthetic",
                    summary="Synthetic backup restore drill completed",
                    metadata_json=json.dumps(
                        {
                            "data_profile": "synthetic_demo_data",
                            "production_data_touched": False,
                        },
                        sort_keys=True,
                    ),
                ),
            ]
        )
        session.commit()
        return _counts(session)


def _verify_restored_database(path: Path, expected_counts: dict[str, int]) -> dict[str, object]:
    engine = create_engine(f"sqlite:///{path}")
    with Session(engine) as session:
        restored_counts = _counts(session)
        tenant_slug = session.scalar(select(Tenant.slug).where(Tenant.id == "tenant-demo"))
        drill_event = session.scalar(
            select(AuditEvent.event_type).where(AuditEvent.id == "audit-restore-drill")
        )
        return {
            "counts": restored_counts,
            "counts_match": restored_counts == expected_counts,
            "tenant_slug": tenant_slug,
            "drill_event": drill_event,
        }


with tempfile.TemporaryDirectory(prefix="drivedesk-public-restore-") as temp_dir:
    temp_path = Path(temp_dir)
    source_db = temp_path / "source.sqlite3"
    backup_file = temp_path / "backup.sqlite3"
    restored_db = temp_path / "restored.sqlite3"

    source_counts = _seed_source_database(source_db)
    _backup_sqlite(source_db, backup_file)
    _backup_sqlite(backup_file, restored_db)

    source_integrity = _integrity_check(source_db)
    backup_integrity = _integrity_check(backup_file)
    restored_integrity = _integrity_check(restored_db)
    restored = _verify_restored_database(restored_db, source_counts)
    backup_sha256 = _hash_file(backup_file)

    required_tables = {
        "dd_tenants",
        "dd_users",
        "dd_memberships",
        "dd_business_records",
        "dd_outbox_events",
        "dd_audit_events",
        "dd_integration_connections",
        "dd_integration_connection_checks",
        "dd_integration_reconciliations",
        "dd_integration_incidents",
    }
    actual_tables = set(Base.metadata.tables)
    missing_tables = sorted(required_tables - actual_tables)

    checks = {
        "source_integrity_ok": source_integrity == "ok",
        "backup_integrity_ok": backup_integrity == "ok",
        "restore_integrity_ok": restored_integrity == "ok",
        "counts_match": bool(restored["counts_match"]),
        "core_tables_present": not missing_tables,
        "tenant_slug_restored": restored["tenant_slug"] == "demo-academy",
        "drill_audit_event_restored": restored["drill_event"] == "backup_restore.drill.completed",
        "backup_sha256_recorded": len(backup_sha256) == 64,
        "production_data_touched": False,
    }

    payload = {
        "schema_version": 1,
        "drill": "public_synthetic_backup_restore",
        "data_profile": "synthetic_demo_data",
        "source_database": "temporary_sqlite",
        "backup_format": "sqlite_backup",
        "restore_target": "temporary_sqlite",
        "checks": checks,
        "source_counts": source_counts,
        "restored_counts": restored["counts"],
        "artifact": {
            "backup_size_bytes": backup_file.stat().st_size,
            "backup_sha256_prefix": backup_sha256[:16],
        },
        "redaction": {
            "paths_included": False,
            "hostnames_included": False,
            "addresses_included": False,
            "credentials_included": False,
            "raw_logs_included": False,
            "production_data_included": False,
        },
    }

    passed = all(value for key, value in checks.items() if key != "production_data_touched")
    passed = passed and checks["production_data_touched"] is False

    if not passed:
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit("public backup restore drill failed")

    print(json.dumps(payload, indent=2, sort_keys=True))
    print(
        "public backup restore drill ok: "
        f"tables={len(required_tables)} "
        f"backup_size_bytes={backup_file.stat().st_size} "
        f"sha256_prefix={backup_sha256[:16]}"
    )
PY
