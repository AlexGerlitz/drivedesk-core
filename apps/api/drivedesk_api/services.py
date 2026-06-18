from __future__ import annotations

import json
from time import perf_counter
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from drivedesk_api.auth import hash_credential
from drivedesk_api.db import (
    AuditEvent,
    BusinessRecord,
    IntegrationConnection,
    IntegrationConnectionCheck,
    Membership,
    OutboxEvent,
    PlatformAdmin,
    Tenant,
    User,
    WorkflowActionRun,
    WorkflowRule,
)
from drivedesk_api.rbac import ActorContext
from drivedesk_api.schemas import (
    AccountingExportCreate,
    BusinessRecordCreate,
    BusinessRecordTransition,
    BusinessRecordType,
    FileImportCreate,
    IntegrationConnectionCheckCreate,
    IntegrationConnectionCreate,
    IntegrationMappingPreviewCreate,
    MembershipCreate,
    OutboxEventRetryRequest,
    PlatformAdminCreate,
    TenantCreate,
    UserCreate,
    WorkflowRuleCreate,
)
from drivedesk_api.tenant_repository import list_tenant_owned, tenant_owned_select
from drivedesk_core import (
    AdapterExecutionError,
    AdapterValidationError,
    build_adapter_connection_diagnostics,
    build_adapter_mapping_preview,
    list_adapter_descriptors,
    resolve_adapter,
    resolve_adapter_connection_scopes,
    validate_adapter_connection_scope,
    validate_adapter_connection_profile,
)


def new_id() -> str:
    return str(uuid4())


async def write_audit(
    session: AsyncSession,
    *,
    tenant_id: str,
    actor: ActorContext,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    summary: str | None = None,
    metadata: dict[str, object] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        id=new_id(),
        tenant_id=tenant_id,
        actor_id=actor.actor_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
    )
    session.add(event)
    return event


async def enqueue_outbox(
    session: AsyncSession,
    *,
    tenant_id: str,
    event_type: str,
    payload: dict[str, object],
    adapter_key: str | None = "internal.noop",
) -> OutboxEvent:
    event = OutboxEvent(
        id=new_id(),
        tenant_id=tenant_id,
        event_type=event_type,
        adapter_key=adapter_key,
        payload_json=json.dumps(payload, ensure_ascii=False, sort_keys=True),
        status="pending",
        attempts=0,
    )
    session.add(event)
    return event


async def create_tenant(session: AsyncSession, payload: TenantCreate, actor: ActorContext) -> Tenant:
    tenant = Tenant(id=new_id(), slug=payload.slug, name=payload.name, status="active")
    session.add(tenant)
    await write_audit(
        session,
        tenant_id=tenant.id,
        actor=actor,
        event_type="tenant.created",
        entity_type="tenant",
        entity_id=tenant.id,
        summary=f"Tenant created: {tenant.slug}",
        metadata={"slug": tenant.slug},
    )
    await enqueue_outbox(
        session,
        tenant_id=tenant.id,
        event_type="tenant.created",
        payload={"tenant_id": tenant.id, "slug": tenant.slug},
    )
    await commit_or_conflict(session, "tenant already exists")
    return tenant


async def create_user(session: AsyncSession, payload: UserCreate, actor: ActorContext) -> User:
    user = User(
        id=new_id(),
        email=str(payload.email).lower(),
        display_name=payload.display_name,
        credential_hash=hash_credential(payload.password) if payload.password else None,
        status="active",
    )
    session.add(user)
    await write_audit(
        session,
        tenant_id="platform",
        actor=actor,
        event_type="user.created",
        entity_type="user",
        entity_id=user.id,
        summary=f"User created: {user.email}",
        metadata={"email": user.email},
    )
    await enqueue_outbox(
        session,
        tenant_id="platform",
        event_type="user.created",
        payload={"user_id": user.id, "email": user.email},
    )
    await commit_or_conflict(session, "user already exists")
    return user


async def create_membership(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: MembershipCreate,
    actor: ActorContext,
) -> Membership:
    await ensure_tenant_exists(session, tenant_id)
    await ensure_user_exists(session, payload.user_id)
    membership = Membership(
        id=new_id(),
        tenant_id=tenant_id,
        user_id=payload.user_id,
        role=payload.role,
        status="active",
    )
    session.add(membership)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="membership.created",
        entity_type="membership",
        entity_id=membership.id,
        summary=f"Membership created with role {membership.role}",
        metadata={"user_id": membership.user_id, "role": membership.role},
    )
    await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="membership.created",
        payload={"membership_id": membership.id, "user_id": membership.user_id, "role": membership.role},
    )
    await commit_or_conflict(session, "membership already exists")
    return membership


async def create_platform_admin(
    session: AsyncSession,
    payload: PlatformAdminCreate,
    actor: ActorContext,
) -> PlatformAdmin:
    await ensure_user_exists(session, payload.user_id)
    platform_admin = PlatformAdmin(
        id=new_id(),
        user_id=payload.user_id,
        role=payload.role,
        status="active",
    )
    session.add(platform_admin)
    await write_audit(
        session,
        tenant_id="platform",
        actor=actor,
        event_type="platform_admin.granted",
        entity_type="platform_admin",
        entity_id=platform_admin.id,
        summary=f"Platform admin granted: {platform_admin.role}",
        metadata={"user_id": platform_admin.user_id, "role": platform_admin.role},
    )
    await enqueue_outbox(
        session,
        tenant_id="platform",
        event_type="platform_admin.granted",
        payload={
            "platform_admin_id": platform_admin.id,
            "user_id": platform_admin.user_id,
            "role": platform_admin.role,
        },
    )
    await commit_or_conflict(session, "platform admin already exists")
    return platform_admin


async def list_platform_admins(session: AsyncSession) -> list[PlatformAdmin]:
    result = await session.execute(select(PlatformAdmin).order_by(PlatformAdmin.created_at.desc()))
    return list(result.scalars().all())


async def create_integration_connection(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: IntegrationConnectionCreate,
    actor: ActorContext,
) -> IntegrationConnection:
    await ensure_tenant_exists(session, tenant_id)
    try:
        validate_adapter_connection_profile(payload.adapter_key, mapping=payload.mapping, scopes=payload.scopes)
        scopes = resolve_adapter_connection_scopes(payload.adapter_key, scopes=payload.scopes)
    except (AdapterExecutionError, AdapterValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    connection = IntegrationConnection(
        id=new_id(),
        tenant_id=tenant_id,
        name=payload.name,
        adapter_key=payload.adapter_key,
        status=payload.status,
        config_json=json.dumps(payload.config, ensure_ascii=False, sort_keys=True),
        mapping_json=json.dumps(payload.mapping, ensure_ascii=False, sort_keys=True),
        scopes_json=json.dumps(scopes, ensure_ascii=False, sort_keys=True),
    )
    session.add(connection)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="integration_connection.created",
        entity_type="integration_connection",
        entity_id=connection.id,
        summary=f"Integration connection created: {connection.adapter_key}",
        metadata={
            "integration_connection_id": connection.id,
            "adapter_key": connection.adapter_key,
            "status": connection.status,
            "config_keys": sorted(payload.config.keys()),
            "mapping_keys": sorted(payload.mapping.keys()),
            "scopes": scopes,
        },
    )
    await commit_or_conflict(session, "integration connection already exists")
    return connection


async def list_integration_connections(session: AsyncSession, *, tenant_id: str) -> list[IntegrationConnection]:
    return await list_tenant_owned(
        session,
        IntegrationConnection,
        tenant_id,
        order_by=IntegrationConnection.created_at.desc(),
    )


async def _tenant_integration_connection(
    session: AsyncSession,
    *,
    tenant_id: str,
    connection_id: str,
) -> IntegrationConnection:
    await ensure_tenant_exists(session, tenant_id)
    connection = await session.get(IntegrationConnection, connection_id)
    if not connection or connection.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="integration connection not found")
    return connection


def _json_object_from_connection(raw_json: str, *, field_name: str) -> dict[str, object]:
    try:
        payload = json.loads(raw_json or "{}")
    except json.JSONDecodeError as exc:
        raise AdapterValidationError(
            f"integration connection {field_name} is invalid",
            adapter_key="integration_connection",
        ) from exc
    if not isinstance(payload, dict):
        raise AdapterValidationError(
            f"integration connection {field_name} is invalid",
            adapter_key="integration_connection",
        )
    return payload


def _raw_connection_scopes(connection: IntegrationConnection) -> list[str]:
    try:
        scopes = json.loads(connection.scopes_json or "[]")
    except json.JSONDecodeError as exc:
        raise AdapterValidationError(
            "integration connection scopes are invalid",
            adapter_key=connection.adapter_key,
        ) from exc
    if not isinstance(scopes, list) or any(not isinstance(scope, str) for scope in scopes):
        raise AdapterValidationError(
            "integration connection scopes are invalid",
            adapter_key=connection.adapter_key,
        )
    return scopes


async def run_integration_connection_check(
    session: AsyncSession,
    *,
    tenant_id: str,
    connection_id: str,
    payload: IntegrationConnectionCheckCreate,
    actor: ActorContext,
) -> IntegrationConnectionCheck:
    connection = await _tenant_integration_connection(session, tenant_id=tenant_id, connection_id=connection_id)
    started_at = perf_counter()
    check_status = "passed"
    summary = "Integration connection diagnostics passed."
    details: dict[str, object] = {
        "connection_status": connection.status,
        "adapter_key": connection.adapter_key,
        "check_type": payload.check_type,
        "simulated": bool(payload.simulate_failure),
    }

    try:
        if payload.simulate_failure == "provider_unavailable":
            raise AdapterValidationError(
                "synthetic provider is unavailable",
                adapter_key=connection.adapter_key,
            )
        if payload.simulate_failure == "credential_rejected":
            raise AdapterValidationError(
                "synthetic credentials were rejected",
                adapter_key=connection.adapter_key,
            )
        if connection.status != "active":
            raise AdapterValidationError(
                "integration connection is not active",
                adapter_key=connection.adapter_key,
            )
        config = _json_object_from_connection(connection.config_json, field_name="config")
        mapping = _json_object_from_connection(connection.mapping_json, field_name="mapping")
        diagnostics = build_adapter_connection_diagnostics(
            connection.adapter_key,
            mapping=mapping,
            scopes=_raw_connection_scopes(connection),
        )
        details.update(
            {
                **diagnostics,
                "config_keys": sorted(str(key) for key in config.keys()),
            }
        )
    except (AdapterExecutionError, AdapterValidationError) as exc:
        check_status = "failed"
        summary = exc.message
        details.update(
            {
                "error_type": exc.__class__.__name__,
                "adapter_key": getattr(exc, "adapter_key", connection.adapter_key),
            }
        )

    duration_ms = round((perf_counter() - started_at) * 1000, 3)
    check = IntegrationConnectionCheck(
        id=new_id(),
        tenant_id=tenant_id,
        integration_connection_id=connection.id,
        adapter_key=connection.adapter_key,
        check_type=payload.check_type,
        status=check_status,
        summary=summary,
        details_json=json.dumps(details, ensure_ascii=False, sort_keys=True),
        duration_ms=duration_ms,
        created_at=datetime.now(UTC),
    )
    session.add(check)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="integration_connection.health_checked",
        entity_type="integration_connection",
        entity_id=connection.id,
        summary=f"Integration connection health check {check_status}: {connection.adapter_key}",
        metadata={
            "integration_connection_id": connection.id,
            "adapter_key": connection.adapter_key,
            "check_status": check_status,
            "check_type": payload.check_type,
            "duration_ms": duration_ms,
            "detail_keys": sorted(details.keys()),
            "simulated": bool(payload.simulate_failure),
        },
    )
    await commit_or_conflict(session, "integration connection check failed")
    return check


async def list_integration_connection_checks(
    session: AsyncSession,
    *,
    tenant_id: str,
    connection_id: str,
    limit: int = 25,
) -> list[IntegrationConnectionCheck]:
    await _tenant_integration_connection(session, tenant_id=tenant_id, connection_id=connection_id)
    result = await session.execute(
        select(IntegrationConnectionCheck)
        .where(
            IntegrationConnectionCheck.tenant_id == tenant_id,
            IntegrationConnectionCheck.integration_connection_id == connection_id,
        )
        .order_by(IntegrationConnectionCheck.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_integration_connection_health(
    session: AsyncSession,
    *,
    tenant_id: str,
    connection_id: str,
) -> dict[str, object]:
    connection = await _tenant_integration_connection(session, tenant_id=tenant_id, connection_id=connection_id)
    result = await session.execute(
        select(IntegrationConnectionCheck)
        .where(
            IntegrationConnectionCheck.tenant_id == tenant_id,
            IntegrationConnectionCheck.integration_connection_id == connection_id,
        )
        .order_by(IntegrationConnectionCheck.created_at.desc())
    )
    checks = list(result.scalars().all())
    latest = checks[0] if checks else None
    last_success = next((check.created_at for check in checks if check.status == "passed"), None)
    last_failure = next((check.created_at for check in checks if check.status == "failed"), None)
    latest_details: dict[str, object] = {}
    if latest is not None:
        try:
            parsed_details = json.loads(latest.details_json or "{}")
            if isinstance(parsed_details, dict):
                latest_details = parsed_details
        except json.JSONDecodeError:
            latest_details = {"details_valid": False}

    return {
        "tenant_id": tenant_id,
        "integration_connection_id": connection.id,
        "adapter_key": connection.adapter_key,
        "connection_status": connection.status,
        "latest_status": latest.status if latest else "never_checked",
        "latest_checked_at": latest.created_at if latest else None,
        "last_success_at": last_success,
        "last_failure_at": last_failure,
        "check_count": len(checks),
        "latest_summary": latest.summary if latest else None,
        "latest_details": latest_details,
    }


async def preview_integration_mapping(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: IntegrationMappingPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    adapter_key = payload.adapter_key
    mapping = payload.mapping

    if payload.integration_connection_id:
        connection = await session.get(IntegrationConnection, payload.integration_connection_id)
        if not connection or connection.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="integration connection not found")
        if connection.adapter_key != payload.adapter_key:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration connection adapter mismatch")
        adapter_key = connection.adapter_key
        scopes = _connection_scopes(connection)
        try:
            validate_adapter_connection_scope(
                adapter_key,
                scopes=scopes,
                required_scope="file_import:preview",
            )
        except AdapterValidationError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
        mapping = json.loads(connection.mapping_json)
        if not isinstance(mapping, dict):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration connection mapping is invalid")

    try:
        return build_adapter_mapping_preview(
            adapter_key,
            records=payload.records,
            mapping=mapping,
        )
    except (AdapterExecutionError, AdapterValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


async def _active_connection_for_file_import(
    session: AsyncSession,
    *,
    tenant_id: str,
    connection_id: str | None,
) -> IntegrationConnection | None:
    return await _active_connection_for_adapter(
        session,
        tenant_id=tenant_id,
        connection_id=connection_id,
        adapter_key="file.import.fake",
        required_scope="file_import:execute",
    )


async def _active_connection_for_adapter(
    session: AsyncSession,
    *,
    tenant_id: str,
    connection_id: str | None,
    adapter_key: str,
    required_scope: str,
) -> IntegrationConnection | None:
    if not connection_id:
        return None

    connection = await session.get(IntegrationConnection, connection_id)
    if not connection or connection.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="integration connection not found")
    if connection.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration connection is not active")
    if connection.adapter_key != adapter_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration connection adapter mismatch")
    scopes = _connection_scopes(connection)
    try:
        mapping = json.loads(connection.mapping_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration connection mapping is invalid") from exc
    if not isinstance(mapping, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration connection mapping is invalid")
    try:
        validate_adapter_connection_scope(
            connection.adapter_key,
            scopes=scopes,
            required_scope=required_scope,
        )
        validate_adapter_connection_profile(
            connection.adapter_key,
            mapping=mapping,
            scopes=scopes,
        )
    except (AdapterExecutionError, AdapterValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    return connection


def _connection_scopes(connection: IntegrationConnection) -> list[str]:
    try:
        scopes = json.loads(connection.scopes_json or "[]")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration connection scopes are invalid") from exc
    if not isinstance(scopes, list) or any(not isinstance(scope, str) for scope in scopes):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration connection scopes are invalid")
    try:
        return resolve_adapter_connection_scopes(connection.adapter_key, scopes=scopes)
    except AdapterValidationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc


async def create_file_import_job(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: FileImportCreate,
    actor: ActorContext,
) -> OutboxEvent:
    await ensure_tenant_exists(session, tenant_id)
    connection = await _active_connection_for_file_import(
        session,
        tenant_id=tenant_id,
        connection_id=payload.integration_connection_id,
    )
    record_count = len(payload.records)
    source_name = payload.source_name.strip()
    adapter_key = connection.adapter_key if connection else "file.import.fake"
    mapping = json.loads(connection.mapping_json) if connection else {}
    scopes = _connection_scopes(connection) if connection else []
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="integration.file_import.requested",
        entity_type="integration_job",
        summary=f"File import requested from {source_name}",
        metadata={
            "adapter_key": adapter_key,
            "integration_connection_id": connection.id if connection else None,
            "record_count": record_count,
            "source_format": payload.source_format,
            "source_name": source_name,
            "mapping_keys": sorted(mapping.keys()),
            "scopes": scopes,
        },
    )
    event = await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="integration.file_import.requested",
        adapter_key=adapter_key,
        payload={
            "adapter_key": adapter_key,
            "integration_connection_id": connection.id if connection else None,
            "source_name": source_name,
            "source_format": payload.source_format,
            "record_count": record_count,
            "mapping": mapping,
            "connection_scopes": scopes,
            "records": payload.records,
            "simulate_failure": payload.simulate_failure,
        },
    )
    await commit_or_conflict(session, "file import job already exists")
    return event


async def create_accounting_export_job(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: AccountingExportCreate,
    actor: ActorContext,
) -> OutboxEvent:
    await ensure_tenant_exists(session, tenant_id)
    connection = await _active_connection_for_adapter(
        session,
        tenant_id=tenant_id,
        connection_id=payload.integration_connection_id,
        adapter_key="accounting.export.mock",
        required_scope="accounting:export",
    )
    documents = payload.documents
    export_batch_id = payload.export_batch_id.strip()
    document_types = sorted(
        {
            str(document.get("document_type")).strip()
            for document in documents
            if isinstance(document.get("document_type"), str) and str(document.get("document_type")).strip()
        }
    )
    adapter_key = connection.adapter_key if connection else "accounting.export.mock"
    scopes = _connection_scopes(connection) if connection else []
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="integration.accounting_export.requested",
        entity_type="integration_job",
        summary=f"Accounting export requested: {export_batch_id}",
        metadata={
            "adapter_key": adapter_key,
            "integration_connection_id": connection.id if connection else None,
            "export_batch_id": export_batch_id,
            "document_count": len(documents),
            "document_types": document_types,
            "scopes": scopes,
        },
    )
    event = await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="accounting.export.requested",
        adapter_key=adapter_key,
        payload={
            "adapter_key": adapter_key,
            "integration_connection_id": connection.id if connection else None,
            "export_batch_id": export_batch_id,
            "document_count": len(documents),
            "document_types": document_types,
            "connection_scopes": scopes,
            "documents": documents,
            "simulate_failure": payload.simulate_failure,
        },
    )
    await commit_or_conflict(session, "accounting export job already exists")
    return event


async def create_business_record(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessRecordCreate,
    actor: ActorContext,
) -> BusinessRecord:
    await ensure_tenant_exists(session, tenant_id)
    record_payload = payload.payload
    record = BusinessRecord(
        id=new_id(),
        tenant_id=tenant_id,
        record_type=payload.record_type,
        status=payload.status,
        title=payload.title,
        external_ref=payload.external_ref,
        payload_json=json.dumps(record_payload, ensure_ascii=False, sort_keys=True),
    )
    session.add(record)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="business_record.created",
        entity_type=f"business_record.{record.record_type}",
        entity_id=record.id,
        summary=f"Business record created: {record.record_type}",
        metadata={
            "record_id": record.id,
            "record_type": record.record_type,
            "status": record.status,
            "external_ref": record.external_ref,
        },
    )
    await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="business_record.created",
        adapter_key="internal.business_record",
        payload={
            "record_id": record.id,
            "record_type": record.record_type,
            "status": record.status,
            "external_ref": record.external_ref,
        },
    )
    await commit_or_conflict(session, "business record already exists")
    return record


async def list_business_records(
    session: AsyncSession,
    *,
    tenant_id: str,
    record_type: BusinessRecordType | None = None,
) -> list[BusinessRecord]:
    query = tenant_owned_select(
        BusinessRecord,
        tenant_id,
        order_by=BusinessRecord.created_at.desc(),
    )
    if record_type is not None:
        query = query.where(BusinessRecord.record_type == record_type)
        result = await session.execute(query)
        return list(result.scalars().all())
    return await list_tenant_owned(
        session,
        BusinessRecord,
        tenant_id,
        order_by=BusinessRecord.created_at.desc(),
    )


async def transition_business_record(
    session: AsyncSession,
    *,
    tenant_id: str,
    record_id: str,
    payload: BusinessRecordTransition,
    actor: ActorContext,
) -> BusinessRecord:
    await ensure_tenant_exists(session, tenant_id)
    record = await session.get(BusinessRecord, record_id)
    if not record or record.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="business record not found")

    previous_status = record.status
    record.status = payload.status
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="business_record.status_changed",
        entity_type=f"business_record.{record.record_type}",
        entity_id=record.id,
        summary=f"Business record status changed: {previous_status} -> {record.status}",
        metadata={
            "record_id": record.id,
            "record_type": record.record_type,
            "previous_status": previous_status,
            "new_status": record.status,
            "reason": payload.reason,
        },
    )
    await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="business_record.status_changed",
        adapter_key="internal.business_record",
        payload={
            "record_id": record.id,
            "record_type": record.record_type,
            "previous_status": previous_status,
            "new_status": record.status,
        },
    )
    await trigger_workflow_rules_for_business_record_transition(
        session,
        tenant_id=tenant_id,
        record=record,
        previous_status=previous_status,
        actor=actor,
        reason=payload.reason,
    )
    await commit_or_conflict(session, "business record transition failed")
    return record


async def create_workflow_rule(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: WorkflowRuleCreate,
    actor: ActorContext,
) -> WorkflowRule:
    await ensure_tenant_exists(session, tenant_id)
    rule = WorkflowRule(
        id=new_id(),
        tenant_id=tenant_id,
        name=payload.name,
        status="active",
        trigger_event_type=payload.trigger_event_type,
        record_type=payload.record_type,
        from_status=payload.from_status,
        to_status=payload.to_status,
        action_type=payload.action_type,
        action_config_json=json.dumps(payload.action_config, ensure_ascii=False, sort_keys=True),
    )
    session.add(rule)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="workflow_rule.created",
        entity_type="workflow_rule",
        entity_id=rule.id,
        summary=f"Workflow rule created: {rule.name}",
        metadata={
            "rule_id": rule.id,
            "trigger_event_type": rule.trigger_event_type,
            "record_type": rule.record_type,
            "from_status": rule.from_status,
            "to_status": rule.to_status,
            "action_type": rule.action_type,
        },
    )
    await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="workflow_rule.created",
        adapter_key="internal.workflow",
        payload={
            "rule_id": rule.id,
            "trigger_event_type": rule.trigger_event_type,
            "record_type": rule.record_type,
            "from_status": rule.from_status,
            "to_status": rule.to_status,
            "action_type": rule.action_type,
        },
    )
    await commit_or_conflict(session, "workflow rule already exists")
    return rule


async def list_workflow_rules(session: AsyncSession, *, tenant_id: str) -> list[WorkflowRule]:
    return await list_tenant_owned(
        session,
        WorkflowRule,
        tenant_id,
        order_by=WorkflowRule.created_at.desc(),
    )


async def record_workflow_action_run(
    session: AsyncSession,
    *,
    tenant_id: str,
    workflow_rule_id: str,
    trigger_event_type: str,
    action_type: str,
    source_record_id: str,
    source_record_type: str,
    previous_status: str | None,
    new_status: str | None,
    actor: ActorContext,
    outbox_event_id: str | None = None,
    task_record_id: str | None = None,
    result: dict[str, object] | None = None,
) -> WorkflowActionRun:
    result_payload = {
        "workflow_rule_id": workflow_rule_id,
        "action_type": action_type,
        "source_record_id": source_record_id,
        "created_outbox_event_id": outbox_event_id,
        "created_task_record_id": task_record_id,
        **(result or {}),
    }
    run = WorkflowActionRun(
        id=new_id(),
        tenant_id=tenant_id,
        workflow_rule_id=workflow_rule_id,
        trigger_event_type=trigger_event_type,
        action_type=action_type,
        status="created",
        source_record_id=source_record_id,
        source_record_type=source_record_type,
        previous_status=previous_status,
        new_status=new_status,
        outbox_event_id=outbox_event_id,
        task_record_id=task_record_id,
        result_json=json.dumps(result_payload, ensure_ascii=False, sort_keys=True),
    )
    session.add(run)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="workflow.action_run.created",
        entity_type="workflow_action_run",
        entity_id=run.id,
        summary=f"Workflow action run created: {action_type}",
        metadata={
            "workflow_action_run_id": run.id,
            "workflow_rule_id": workflow_rule_id,
            "trigger_event_type": trigger_event_type,
            "action_type": action_type,
            "status": run.status,
            "source_record_id": source_record_id,
            "source_record_type": source_record_type,
            "previous_status": previous_status,
            "new_status": new_status,
            "outbox_event_id": outbox_event_id,
            "task_record_id": task_record_id,
        },
    )
    return run


async def list_workflow_action_runs(session: AsyncSession, *, tenant_id: str) -> list[WorkflowActionRun]:
    return await list_tenant_owned(
        session,
        WorkflowActionRun,
        tenant_id,
        order_by=WorkflowActionRun.created_at.desc(),
    )


def _workflow_config_dict(rule: WorkflowRule) -> dict[str, object]:
    config = json.loads(rule.action_config_json or "{}")
    if not isinstance(config, dict):
        return {}
    return config


def _workflow_config_text(
    config: dict[str, object],
    key: str,
    default: str,
    *,
    max_length: int,
    status_value: bool = False,
) -> str:
    raw_value = config.get(key, default)
    value = str(raw_value if raw_value is not None else default).strip() or default
    value = value[:max_length]
    if status_value and (
        not value
        or not value[0].isalnum()
        or any(not (character.isalnum() or character in "_-") for character in value)
    ):
        return default
    return value


def _workflow_config_payload(config: dict[str, object]) -> dict[str, object]:
    configured_payload = config.get("payload", {})
    if not isinstance(configured_payload, dict):
        return {}
    return configured_payload


async def trigger_workflow_rules_for_business_record_transition(
    session: AsyncSession,
    *,
    tenant_id: str,
    record: BusinessRecord,
    previous_status: str,
    actor: ActorContext,
    reason: str | None = None,
) -> list[WorkflowRule]:
    result = await session.execute(
        select(WorkflowRule)
        .where(
            WorkflowRule.tenant_id == tenant_id,
            WorkflowRule.status == "active",
            WorkflowRule.trigger_event_type == "business_record.status_changed",
            or_(WorkflowRule.record_type.is_(None), WorkflowRule.record_type == record.record_type),
            or_(WorkflowRule.from_status.is_(None), WorkflowRule.from_status == previous_status),
            or_(WorkflowRule.to_status.is_(None), WorkflowRule.to_status == record.status),
        )
        .order_by(WorkflowRule.created_at)
    )
    matched_rules = list(result.scalars().all())
    for rule in matched_rules:
        config = _workflow_config_dict(rule)
        configured_payload = _workflow_config_payload(config)
        action_payload = {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "action_type": rule.action_type,
            "record_id": record.id,
            "record_type": record.record_type,
            "previous_status": previous_status,
            "new_status": record.status,
            "reason": reason,
            "payload": configured_payload,
        }
        await write_audit(
            session,
            tenant_id=tenant_id,
            actor=actor,
            event_type="workflow.rule.triggered",
            entity_type="workflow_rule",
            entity_id=rule.id,
            summary=f"Workflow rule triggered: {rule.name}",
            metadata=action_payload,
        )
        if rule.action_type == "create_task_record":
            task_status = _workflow_config_text(
                config,
                "status",
                "open",
                max_length=32,
                status_value=True,
            )
            task_title = _workflow_config_text(
                config,
                "title",
                f"Task from workflow: {rule.name}",
                max_length=255,
            )
            external_ref = config.get("external_ref")
            task_external_ref = str(external_ref).strip()[:128] if external_ref else None
            task_payload = {
                "source": {
                    "rule_id": rule.id,
                    "source_record_id": record.id,
                    "source_record_type": record.record_type,
                    "previous_status": previous_status,
                    "new_status": record.status,
                },
                "task": configured_payload,
            }
            task_record = BusinessRecord(
                id=new_id(),
                tenant_id=tenant_id,
                record_type="task",
                status=task_status,
                title=task_title,
                external_ref=task_external_ref,
                payload_json=json.dumps(task_payload, ensure_ascii=False, sort_keys=True),
            )
            session.add(task_record)
            await write_audit(
                session,
                tenant_id=tenant_id,
                actor=actor,
                event_type="business_record.created",
                entity_type="business_record.task",
                entity_id=task_record.id,
                summary="Workflow task record created",
                metadata={
                    "record_id": task_record.id,
                    "record_type": task_record.record_type,
                    "status": task_record.status,
                    "source_rule_id": rule.id,
                    "source_record_id": record.id,
                },
            )
            business_record_outbox = await enqueue_outbox(
                session,
                tenant_id=tenant_id,
                event_type="business_record.created",
                adapter_key="internal.business_record",
                payload={
                    "record_id": task_record.id,
                    "record_type": task_record.record_type,
                    "status": task_record.status,
                    "source_rule_id": rule.id,
                    "source_record_id": record.id,
                },
            )
            workflow_outbox = await enqueue_outbox(
                session,
                tenant_id=tenant_id,
                event_type="workflow.task_record.created",
                adapter_key="internal.workflow",
                payload={
                    **action_payload,
                    "task_record_id": task_record.id,
                    "task_status": task_record.status,
                },
            )
            await record_workflow_action_run(
                session,
                tenant_id=tenant_id,
                workflow_rule_id=rule.id,
                trigger_event_type=rule.trigger_event_type,
                action_type=rule.action_type,
                source_record_id=record.id,
                source_record_type=record.record_type,
                previous_status=previous_status,
                new_status=record.status,
                actor=actor,
                outbox_event_id=workflow_outbox.id,
                task_record_id=task_record.id,
                result={"business_record_outbox_event_id": business_record_outbox.id},
            )
            continue

        if rule.action_type == "request_adapter_sync":
            event_type = _workflow_config_text(
                config,
                "event_type",
                "workflow.adapter_sync.requested",
                max_length=128,
            )
            adapter_key = _workflow_config_text(
                config,
                "adapter_key",
                "internal.workflow",
                max_length=128,
            )
            adapter_outbox = await enqueue_outbox(
                session,
                tenant_id=tenant_id,
                event_type=event_type,
                adapter_key=adapter_key,
                payload=action_payload,
            )
            await record_workflow_action_run(
                session,
                tenant_id=tenant_id,
                workflow_rule_id=rule.id,
                trigger_event_type=rule.trigger_event_type,
                action_type=rule.action_type,
                source_record_id=record.id,
                source_record_type=record.record_type,
                previous_status=previous_status,
                new_status=record.status,
                actor=actor,
                outbox_event_id=adapter_outbox.id,
            )
            continue

        event_type = _workflow_config_text(config, "event_type", "workflow.rule.triggered", max_length=128)
        adapter_key = _workflow_config_text(config, "adapter_key", "internal.workflow", max_length=128)
        workflow_outbox = await enqueue_outbox(
            session,
            tenant_id=tenant_id,
            event_type=event_type,
            adapter_key=adapter_key,
            payload=action_payload,
        )
        await record_workflow_action_run(
            session,
            tenant_id=tenant_id,
            workflow_rule_id=rule.id,
            trigger_event_type=rule.trigger_event_type,
            action_type=rule.action_type,
            source_record_id=record.id,
            source_record_type=record.record_type,
            previous_status=previous_status,
            new_status=record.status,
            actor=actor,
            outbox_event_id=workflow_outbox.id,
        )
    return matched_rules


async def count_business_records_by_type_status(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            BusinessRecord.record_type,
            BusinessRecord.status,
            func.count().label("record_count"),
        ).group_by(BusinessRecord.record_type, BusinessRecord.status)
    )
    return [
        {
            "record_type": row.record_type,
            "status": row.status,
            "record_count": int(row.record_count or 0),
        }
        for row in result.all()
    ]


async def count_workflow_rules_by_status_trigger_action(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            WorkflowRule.status,
            WorkflowRule.trigger_event_type,
            WorkflowRule.action_type,
            func.count().label("rule_count"),
        ).group_by(WorkflowRule.status, WorkflowRule.trigger_event_type, WorkflowRule.action_type)
    )
    return [
        {
            "status": row.status,
            "trigger_event_type": row.trigger_event_type,
            "action_type": row.action_type,
            "rule_count": int(row.rule_count or 0),
        }
        for row in result.all()
    ]


async def count_workflow_action_runs_by_action_status(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            WorkflowActionRun.action_type,
            WorkflowActionRun.status,
            func.count().label("run_count"),
        ).group_by(WorkflowActionRun.action_type, WorkflowActionRun.status)
    )
    return [
        {
            "action_type": row.action_type,
            "status": row.status,
            "run_count": int(row.run_count or 0),
        }
        for row in result.all()
    ]


async def count_integration_connections_by_adapter_status(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            IntegrationConnection.adapter_key,
            IntegrationConnection.status,
            func.count().label("connection_count"),
        ).group_by(IntegrationConnection.adapter_key, IntegrationConnection.status)
    )
    return [
        {
            "adapter_key": row.adapter_key,
            "status": row.status,
            "connection_count": int(row.connection_count or 0),
        }
        for row in result.all()
    ]


async def count_integration_connection_checks_by_adapter_status(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            IntegrationConnectionCheck.adapter_key,
            IntegrationConnectionCheck.status,
            func.count().label("check_count"),
            func.avg(IntegrationConnectionCheck.duration_ms).label("avg_duration_ms"),
        ).group_by(IntegrationConnectionCheck.adapter_key, IntegrationConnectionCheck.status)
    )
    return [
        {
            "adapter_key": row.adapter_key,
            "status": row.status,
            "check_count": int(row.check_count or 0),
            "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms is not None else None,
        }
        for row in result.all()
    ]


async def ensure_tenant_exists(session: AsyncSession, tenant_id: str) -> Tenant:
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tenant not found")
    return tenant


async def ensure_user_exists(session: AsyncSession, user_id: str) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user


async def commit_or_conflict(session: AsyncSession, message: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc


async def list_processable_outbox(session: AsyncSession, limit: int = 25) -> list[OutboxEvent]:
    now = datetime.now(UTC)
    result = await session.execute(
        select(OutboxEvent)
        .where(
            or_(
                OutboxEvent.status == "pending",
                and_(
                    OutboxEvent.status == "retry",
                    or_(OutboxEvent.next_retry_at.is_(None), OutboxEvent.next_retry_at <= now),
                ),
            )
        )
        .order_by(OutboxEvent.created_at)
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_pending_outbox(session: AsyncSession, limit: int = 25) -> list[OutboxEvent]:
    return await list_processable_outbox(session, limit=limit)


async def count_outbox_by_status(session: AsyncSession) -> dict[str, int]:
    result = await session.execute(select(OutboxEvent.status, func.count()).group_by(OutboxEvent.status))
    return {status: count for status, count in result.all()}


def _adapter_operation_by_event_type(adapter_key: str | None, event_type: str) -> dict[str, object] | None:
    for descriptor in list_adapter_descriptors():
        if descriptor.get("key") != (adapter_key or "internal.noop"):
            continue
        for operation in descriptor.get("operation_contracts", []):
            if isinstance(operation, dict) and operation.get("event_type") == event_type:
                return operation
    return None


def _safe_outbox_payload_summary(payload_json: str) -> tuple[str | None, dict[str, object]]:
    try:
        payload = json.loads(payload_json or "{}")
    except json.JSONDecodeError:
        return None, {"payload_valid": False}
    if not isinstance(payload, dict):
        return None, {"payload_valid": False}

    summary: dict[str, object] = {"payload_valid": True}
    integration_connection_id = payload.get("integration_connection_id")
    if isinstance(integration_connection_id, str) and integration_connection_id:
        summary["has_integration_connection"] = True
    else:
        integration_connection_id = None
        summary["has_integration_connection"] = False

    for key in ("source_format", "record_count", "export_batch_id", "document_count", "simulate_failure"):
        value = payload.get(key)
        if isinstance(value, str | int) or value is None:
            summary[key] = value

    mapping = payload.get("mapping")
    if isinstance(mapping, dict):
        summary["mapping_keys"] = sorted(str(key) for key in mapping.keys())

    scopes = payload.get("connection_scopes")
    if isinstance(scopes, list) and all(isinstance(scope, str) for scope in scopes):
        summary["connection_scopes"] = sorted(scopes)

    records = payload.get("records")
    if isinstance(records, list):
        summary["raw_records_redacted"] = len(records)

    document_types = payload.get("document_types")
    if isinstance(document_types, list) and all(isinstance(document_type, str) for document_type in document_types):
        summary["document_types"] = sorted(document_types)

    documents = payload.get("documents")
    if isinstance(documents, list):
        summary["raw_documents_redacted"] = len(documents)

    return integration_connection_id, summary


async def list_integration_operator_review(
    session: AsyncSession,
    *,
    tenant_id: str,
    status_filter: str | None = None,
    adapter_key: str | None = None,
    limit: int = 50,
) -> list[dict[str, object]]:
    await ensure_tenant_exists(session, tenant_id)
    allowed_statuses = {"retry", "dead_letter"}
    statuses = [status_filter] if status_filter else sorted(allowed_statuses)
    if any(status_value not in allowed_statuses for status_value in statuses):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be retry or dead_letter",
        )

    query = (
        select(OutboxEvent)
        .where(
            OutboxEvent.tenant_id == tenant_id,
            OutboxEvent.status.in_(statuses),
            OutboxEvent.adapter_key.is_not(None),
        )
        .order_by(OutboxEvent.created_at.desc())
        .limit(limit)
    )
    if adapter_key:
        query = query.where(OutboxEvent.adapter_key == adapter_key)

    result = await session.execute(query)
    review_items: list[dict[str, object]] = []
    for event in result.scalars().all():
        operation = _adapter_operation_by_event_type(event.adapter_key, event.event_type)
        integration_connection_id, payload_summary = _safe_outbox_payload_summary(event.payload_json)
        status_value = "retry" if event.status == "retry" else "dead_letter"
        severity = "retryable" if status_value == "retry" else "operator_review"
        review_items.append(
            {
                "id": event.id,
                "tenant_id": event.tenant_id,
                "adapter_key": event.adapter_key or "internal.noop",
                "operation_key": operation.get("key") if operation else None,
                "event_type": event.event_type,
                "status": status_value,
                "severity": severity,
                "attempts": event.attempts,
                "last_error": event.last_error,
                "last_duration_ms": event.last_duration_ms,
                "next_retry_at": event.next_retry_at,
                "dead_lettered_at": event.dead_lettered_at,
                "created_at": event.created_at,
                "integration_connection_id": integration_connection_id,
                "required_connection_scope": operation.get("required_connection_scope") if operation else None,
                "payload_summary": payload_summary,
                "recommended_action": (
                    "wait for the provider or retry after confirming it recovered"
                    if status_value == "retry"
                    else "review mapping/provider contract, then requeue with an operator reason"
                ),
                "retry_endpoint": f"/tenants/{tenant_id}/outbox-events/{event.id}/retry",
            }
        )
    return review_items


async def retry_outbox_event(
    session: AsyncSession,
    *,
    tenant_id: str,
    event_id: str,
    payload: OutboxEventRetryRequest,
    actor: ActorContext,
) -> OutboxEvent:
    await ensure_tenant_exists(session, tenant_id)
    event = await session.get(OutboxEvent, event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="outbox event not found")

    if event.status not in {"retry", "dead_letter"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="outbox event is not in retry or dead_letter status",
        )

    previous_status = event.status
    previous_attempts = event.attempts
    previous_error = event.last_error
    previous_next_retry_at = event.next_retry_at.isoformat() if event.next_retry_at else None
    previous_dead_lettered_at = event.dead_lettered_at.isoformat() if event.dead_lettered_at else None

    event.status = "pending"
    if payload.reset_attempts:
        event.attempts = 0
    event.last_error = None
    event.last_duration_ms = None
    event.next_retry_at = None
    event.processed_at = None
    event.dead_lettered_at = None
    event.result_json = None

    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="outbox_event.retry_requested",
        entity_type="outbox_event",
        entity_id=event.id,
        summary="Outbox event requeued for retry",
        metadata={
            "outbox_event_id": event.id,
            "event_type": event.event_type,
            "adapter_key": event.adapter_key,
            "previous_status": previous_status,
            "new_status": event.status,
            "previous_attempts": previous_attempts,
            "new_attempts": event.attempts,
            "previous_error": previous_error,
            "previous_next_retry_at": previous_next_retry_at,
            "previous_dead_lettered_at": previous_dead_lettered_at,
            "reset_attempts": payload.reset_attempts,
            "reason": payload.reason,
        },
    )
    await commit_or_conflict(session, "outbox event retry request failed")
    return event


async def summarize_integration_outbox(session: AsyncSession) -> list[dict[str, object]]:
    adapter_key = func.coalesce(OutboxEvent.adapter_key, "internal.noop")
    result = await session.execute(
        select(
            adapter_key.label("adapter_key"),
            OutboxEvent.status,
            func.count().label("job_count"),
            func.coalesce(func.sum(OutboxEvent.attempts), 0).label("attempt_count"),
            func.coalesce(
                func.sum(case((OutboxEvent.last_error.is_not(None), 1), else_=0)),
                0,
            ).label("error_count"),
            func.avg(OutboxEvent.last_duration_ms).label("avg_duration_ms"),
        ).group_by(adapter_key, OutboxEvent.status)
    )
    rows = []
    for row in result.all():
        rows.append(
            {
                "adapter_key": row.adapter_key,
                "status": row.status,
                "job_count": int(row.job_count or 0),
                "attempt_count": int(row.attempt_count or 0),
                "error_count": int(row.error_count or 0),
                "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms is not None else None,
            }
        )
    return rows


async def mark_outbox_processed(
    session: AsyncSession,
    event: OutboxEvent,
    *,
    result: dict[str, object] | None = None,
    duration_ms: float | None = None,
) -> None:
    event.status = "processed"
    event.attempts += 1
    event.last_error = None
    event.next_retry_at = None
    event.last_duration_ms = duration_ms
    event.result_json = json.dumps(result or {}, ensure_ascii=False, sort_keys=True)
    event.processed_at = datetime.now(UTC)
    await session.commit()


def retry_delay_for_attempt(attempt: int) -> timedelta:
    return timedelta(seconds=min(60 * (2 ** max(attempt - 1, 0)), 3600))


async def mark_outbox_failed(
    session: AsyncSession,
    event: OutboxEvent,
    *,
    error_message: str,
    retryable: bool,
    max_attempts: int = 3,
    duration_ms: float | None = None,
) -> None:
    event.attempts += 1
    event.last_error = error_message
    event.last_duration_ms = duration_ms
    event.processed_at = None
    event.result_json = None

    if retryable and event.attempts < max_attempts:
        event.status = "retry"
        event.next_retry_at = datetime.now(UTC) + retry_delay_for_attempt(event.attempts)
        event.dead_lettered_at = None
    else:
        event.status = "dead_letter"
        event.next_retry_at = None
        event.dead_lettered_at = datetime.now(UTC)

    await session.commit()
