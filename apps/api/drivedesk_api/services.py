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
    BusinessException,
    BusinessRecord,
    BusinessStateObservation,
    IntegrationConnection,
    IntegrationConnectionCheck,
    IntegrationIncident,
    IntegrationReconciliation,
    Membership,
    OutboxEvent,
    PlatformAdmin,
    RepairAction,
    Tenant,
    User,
    WorkflowActionRun,
    WorkflowRule,
)
from drivedesk_api.rbac import ActorContext
from drivedesk_api.schemas import (
    AccountingExportCreate,
    BusinessActionExecutionPreviewCreate,
    BusinessApprovalGatewayPreviewCreate,
    BusinessActionPlanPreviewCreate,
    BusinessBriefingPreviewCreate,
    BusinessDetectionPreviewCreate,
    BusinessEscalationPreviewCreate,
    BusinessIntakePipelinePreviewCreate,
    BusinessNotificationChannelMatrixPreviewCreate,
    BusinessNotificationPreviewCreate,
    BusinessProviderIntakePreviewCreate,
    BusinessTaskHandoffPreviewCreate,
    BusinessWorkbenchContextPreviewCreate,
    BusinessExceptionCreate,
    BusinessExceptionStatusChange,
    BusinessRecordCreate,
    BusinessRecordTransition,
    BusinessRecordType,
    BusinessStateObservationCreate,
    FileImportCreate,
    IntegrationConnectionCheckCreate,
    IntegrationConnectionCreate,
    IntegrationIncidentCreate,
    IntegrationIncidentStatusChange,
    IntegrationExecutionPreviewCreate,
    IntegrationMappingPreviewCreate,
    IntegrationRepairPreviewCreate,
    IntegrationReconciliationCreate,
    IntegrationRuntimePreviewCreate,
    MembershipCreate,
    OutboxEventRetryRequest,
    PlatformAdminCreate,
    RepairActionExecutionRequest,
    RepairActionPropose,
    TenantCreate,
    UserCreate,
    WorkflowRuleCreate,
)
from drivedesk_api.tenant_repository import list_tenant_owned, tenant_owned_select
from drivedesk_core import (
    AdapterExecutionError,
    AdapterValidationError,
    build_adapter_connection_diagnostics,
    build_adapter_execution_timeline,
    build_adapter_mapping_preview,
    build_adapter_runtime_plan,
    build_integration_repair_preview,
    list_adapter_descriptors,
    list_integration_runbooks,
    resolve_adapter,
    resolve_adapter_connection_scopes,
    select_integration_runbook,
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


async def preview_integration_runtime(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: IntegrationRuntimePreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    try:
        plan = build_adapter_runtime_plan(
            payload.adapter_key,
            operation_key=payload.operation_key,
            scopes=payload.connection_scopes or None,
            execution_mode=payload.execution_mode,
        )
    except (AdapterExecutionError, AdapterValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    operation_contract = plan["operation_contract"]
    if not isinstance(operation_contract, dict):
        operation_contract = {}
    operation_key = str(operation_contract.get("key") or payload.operation_key or "unknown")
    reconciliation_plan = plan.get("reconciliation_plan", [])
    incident_routes = plan.get("incident_routes", [])

    return {
        "tenant_id": tenant_id,
        "runtime_kind": payload.runtime_kind,
        "adapter_key": str(plan["adapter_key"]),
        "operation_key": operation_key,
        "execution_mode": payload.execution_mode,
        "generated_at": datetime.now(UTC),
        "status": "previewed",
        "summary": (
            f"Integration runtime preview selected {plan['adapter_key']}.{operation_key}, "
            f"prepared {len(plan.get('runtime_steps', []))} runtime step(s), "
            f"{len(plan.get('preflight_checks', []))} preflight check(s), and "
            f"{len(incident_routes) if payload.include_incident_routes else 0} incident route(s)."
        ),
        "operation_contract": operation_contract,
        "runtime_steps": plan.get("runtime_steps", []),
        "preflight_checks": plan.get("preflight_checks", []),
        "outbox_handoff": plan.get("outbox_handoff", {}),
        "worker_boundary": plan.get("worker_boundary", {}),
        "reconciliation_plan": reconciliation_plan if payload.include_reconciliation else [],
        "incident_routes": incident_routes if payload.include_incident_routes else [],
        "data_boundaries": plan.get("data_boundaries", []),
        "evidence": [
            {
                "type": "integration_runtime",
                "event": "adapter_runtime.previewed",
                "adapter_key": str(plan["adapter_key"]),
                "operation_key": operation_key,
                "execution_mode": payload.execution_mode,
                "external_mutation": False,
                "provider_call_enabled": False,
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/integration-runtime/preview",
            "adapters": "GET /integration-adapters",
            "runbooks": "GET /integration-runbooks",
            "operator_review": "GET /tenants/{tenant_id}/integration-operator-review",
            "outbox": "GET /tenants/{tenant_id}/outbox",
        },
    }


async def preview_integration_execution(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: IntegrationExecutionPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    try:
        execution = build_adapter_execution_timeline(
            payload.adapter_key,
            operation_key=payload.operation_key,
            scopes=payload.connection_scopes or None,
            execution_mode=payload.execution_mode,
            request_id=payload.request_id,
            include_failure_path=payload.include_failure_path,
        )
    except (AdapterExecutionError, AdapterValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    timeline = execution.get("timeline", [])
    run_ledger = execution.get("run_ledger", {})
    retry_policy = execution.get("retry_policy", [])
    reconciliation_links = execution.get("reconciliation_links", [])
    observability = execution.get("observability", [])

    return {
        "tenant_id": tenant_id,
        "execution_kind": payload.execution_kind,
        "adapter_key": str(execution["adapter_key"]),
        "operation_key": str(execution["operation_key"]),
        "execution_mode": payload.execution_mode,
        "generated_at": datetime.now(UTC),
        "status": "previewed",
        "summary": (
            f"Integration execution preview prepared {len(timeline)} timeline stage(s), "
            f"{len(retry_policy)} retry policy item(s), "
            f"{len(reconciliation_links)} reconciliation link(s), and "
            f"{len(observability)} observability signal(s)."
        ),
        "run_ledger": run_ledger,
        "timeline": timeline,
        "state_transitions": execution.get("state_transitions", []),
        "retry_policy": retry_policy,
        "reconciliation_links": reconciliation_links,
        "observability": observability,
        "data_boundaries": execution.get("data_boundaries", []),
        "evidence": [
            {
                "type": "integration_execution",
                "event": "integration_execution.timeline_previewed",
                "adapter_key": str(execution["adapter_key"]),
                "operation_key": str(execution["operation_key"]),
                "execution_mode": payload.execution_mode,
                "external_mutation": False,
                "provider_call_enabled": False,
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/integration-executions/preview",
            "runtime_preview": "POST /tenants/{tenant_id}/integration-runtime/preview",
            "workflow_action_runs": "GET /tenants/{tenant_id}/workflow-action-runs",
            "outbox": "GET /tenants/{tenant_id}/outbox-events",
            "reconciliations": "GET /tenants/{tenant_id}/integration-reconciliations",
            "incidents": "GET /tenants/{tenant_id}/integration-incidents",
        },
    }


async def preview_integration_repair(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: IntegrationRepairPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    try:
        preview = build_integration_repair_preview(
            incident_id=payload.incident_id,
            action=payload.action,
            operator_role=payload.operator_role,
            include_postchecks=payload.include_postchecks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "tenant_id": tenant_id,
        "generated_at": datetime.now(UTC),
        **preview,
    }


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


async def create_business_state_observation(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessStateObservationCreate,
    actor: ActorContext,
) -> BusinessStateObservation:
    await ensure_tenant_exists(session, tenant_id)
    observed_at = payload.observed_at or datetime.now(UTC)
    observation = BusinessStateObservation(
        id=new_id(),
        tenant_id=tenant_id,
        system_key=payload.system_key,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        external_ref=payload.external_ref,
        state=payload.state,
        observed_at=observed_at,
        payload_json=json.dumps(payload.payload, ensure_ascii=False, sort_keys=True),
    )
    session.add(observation)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="business_state.observation.recorded",
        entity_type="business_state_observation",
        entity_id=observation.id,
        summary=f"Business state observed from {observation.system_key}: {observation.state}",
        metadata={
            "observation_id": observation.id,
            "system_key": observation.system_key,
            "subject_type": observation.subject_type,
            "subject_id": observation.subject_id,
            "external_ref": observation.external_ref,
            "state": observation.state,
            "payload_keys": sorted(payload.payload.keys()),
        },
    )
    await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="business_state.observation.recorded",
        adapter_key="internal.business_state",
        payload={
            "observation_id": observation.id,
            "system_key": observation.system_key,
            "subject_type": observation.subject_type,
            "subject_id": observation.subject_id,
            "state": observation.state,
        },
    )
    await commit_or_conflict(session, "business state observation already exists")
    return observation


async def list_business_state_observations(
    session: AsyncSession,
    *,
    tenant_id: str,
    system_key: str | None = None,
    subject_type: str | None = None,
    subject_id: str | None = None,
    limit: int = 50,
) -> list[BusinessStateObservation]:
    await ensure_tenant_exists(session, tenant_id)
    query = (
        select(BusinessStateObservation)
        .where(BusinessStateObservation.tenant_id == tenant_id)
        .order_by(BusinessStateObservation.observed_at.desc(), BusinessStateObservation.created_at.desc())
        .limit(limit)
    )
    if system_key:
        query = query.where(BusinessStateObservation.system_key == system_key)
    if subject_type:
        query = query.where(BusinessStateObservation.subject_type == subject_type)
    if subject_id:
        query = query.where(BusinessStateObservation.subject_id == subject_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def _load_business_state_observations(
    session: AsyncSession,
    *,
    tenant_id: str,
    observation_ids: list[str],
) -> list[BusinessStateObservation]:
    if not observation_ids:
        return []
    result = await session.execute(
        select(BusinessStateObservation).where(
            BusinessStateObservation.tenant_id == tenant_id,
            BusinessStateObservation.id.in_(observation_ids),
        )
    )
    observations = list(result.scalars().all())
    if len(observations) != len(set(observation_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="business state observation not found")
    return observations


async def create_business_exception(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessExceptionCreate,
    actor: ActorContext,
) -> BusinessException:
    await ensure_tenant_exists(session, tenant_id)
    observations = await _load_business_state_observations(
        session,
        tenant_id=tenant_id,
        observation_ids=payload.observation_ids,
    )
    observation_evidence = [
        {
            "observation_id": observation.id,
            "system_key": observation.system_key,
            "state": observation.state,
            "subject_type": observation.subject_type,
            "subject_id": observation.subject_id,
            "observed_at": observation.observed_at.isoformat(),
        }
        for observation in observations
    ]
    evidence = {
        **payload.evidence,
        "observation_ids": payload.observation_ids,
        "observations": observation_evidence,
    }
    business_exception = BusinessException(
        id=new_id(),
        tenant_id=tenant_id,
        exception_type=payload.exception_type,
        severity=payload.severity,
        status="open",
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        title=payload.title,
        summary=payload.summary,
        impact_json=json.dumps(payload.impact, ensure_ascii=False, sort_keys=True),
        evidence_json=json.dumps(evidence, ensure_ascii=False, sort_keys=True),
        detected_at=datetime.now(UTC),
    )
    session.add(business_exception)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="business_exception.created",
        entity_type="business_exception",
        entity_id=business_exception.id,
        summary=f"Business exception created: {business_exception.exception_type}",
        metadata={
            "business_exception_id": business_exception.id,
            "exception_type": business_exception.exception_type,
            "severity": business_exception.severity,
            "subject_type": business_exception.subject_type,
            "subject_id": business_exception.subject_id,
            "observation_count": len(observations),
            "impact_keys": sorted(payload.impact.keys()),
        },
    )
    await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="business_exception.created",
        adapter_key="internal.business_exception",
        payload={
            "business_exception_id": business_exception.id,
            "exception_type": business_exception.exception_type,
            "severity": business_exception.severity,
            "status": business_exception.status,
            "subject_type": business_exception.subject_type,
            "subject_id": business_exception.subject_id,
        },
    )
    await commit_or_conflict(session, "business exception already exists")
    return business_exception


async def list_business_exceptions(
    session: AsyncSession,
    *,
    tenant_id: str,
    status_filter: str | None = None,
    severity: str | None = None,
    exception_type: str | None = None,
    limit: int = 50,
) -> list[BusinessException]:
    await ensure_tenant_exists(session, tenant_id)
    query = (
        select(BusinessException)
        .where(BusinessException.tenant_id == tenant_id)
        .order_by(BusinessException.detected_at.desc(), BusinessException.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        query = query.where(BusinessException.status == status_filter)
    if severity:
        query = query.where(BusinessException.severity == severity)
    if exception_type:
        query = query.where(BusinessException.exception_type == exception_type)
    result = await session.execute(query)
    return list(result.scalars().all())


async def _tenant_business_exception(
    session: AsyncSession,
    *,
    tenant_id: str,
    business_exception_id: str,
) -> BusinessException:
    await ensure_tenant_exists(session, tenant_id)
    business_exception = await session.get(BusinessException, business_exception_id)
    if not business_exception or business_exception.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="business exception not found")
    return business_exception


async def change_business_exception_status(
    session: AsyncSession,
    *,
    tenant_id: str,
    business_exception_id: str,
    payload: BusinessExceptionStatusChange,
    actor: ActorContext,
) -> BusinessException:
    business_exception = await _tenant_business_exception(
        session,
        tenant_id=tenant_id,
        business_exception_id=business_exception_id,
    )
    if business_exception.status == "resolved":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="business exception already resolved")
    previous_status = business_exception.status
    changed_at = datetime.now(UTC)
    business_exception.status = payload.status
    business_exception.updated_at = changed_at
    if payload.status == "resolved":
        business_exception.resolved_at = changed_at
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="business_exception.status_changed",
        entity_type="business_exception",
        entity_id=business_exception.id,
        summary=f"Business exception status changed: {previous_status} -> {business_exception.status}",
        metadata={
            "business_exception_id": business_exception.id,
            "previous_status": previous_status,
            "new_status": business_exception.status,
            "note": payload.note,
        },
    )
    await commit_or_conflict(session, "business exception status change failed")
    return business_exception


def _default_repair_summary(business_exception: BusinessException, action_type: str) -> str:
    if action_type == "sync_status":
        return f"Synchronize {business_exception.subject_type} state after verified cross-system evidence."
    if action_type == "create_task":
        return f"Create an operator task for {business_exception.subject_type} exception review."
    if action_type == "notify_owner":
        return f"Notify the accountable owner about {business_exception.exception_type}."
    return f"Prepare {action_type} repair for {business_exception.exception_type}."


async def propose_repair_action(
    session: AsyncSession,
    *,
    tenant_id: str,
    business_exception_id: str,
    payload: RepairActionPropose,
    actor: ActorContext,
) -> RepairAction:
    business_exception = await _tenant_business_exception(
        session,
        tenant_id=tenant_id,
        business_exception_id=business_exception_id,
    )
    if business_exception.status == "resolved":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="business exception already resolved")
    repair_payload = {
        "business_exception_id": business_exception.id,
        "exception_type": business_exception.exception_type,
        "subject_type": business_exception.subject_type,
        "subject_id": business_exception.subject_id,
        "target_adapter_key": "internal.repair_engine",
        "external_mutation": False,
        **payload.payload,
    }
    repair_action = RepairAction(
        id=new_id(),
        tenant_id=tenant_id,
        business_exception_id=business_exception.id,
        action_type=payload.action_type,
        safety_level=payload.safety_level,
        requires_approval=1 if payload.requires_approval else 0,
        status="proposed",
        summary=payload.summary or _default_repair_summary(business_exception, payload.action_type),
        payload_json=json.dumps(repair_payload, ensure_ascii=False, sort_keys=True),
        result_json=json.dumps({}, ensure_ascii=False, sort_keys=True),
    )
    session.add(repair_action)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="repair_action.proposed",
        entity_type="repair_action",
        entity_id=repair_action.id,
        summary=f"Repair action proposed: {repair_action.action_type}",
        metadata={
            "repair_action_id": repair_action.id,
            "business_exception_id": business_exception.id,
            "action_type": repair_action.action_type,
            "safety_level": repair_action.safety_level,
            "requires_approval": bool(repair_action.requires_approval),
        },
    )
    await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="repair_action.proposed",
        adapter_key="internal.repair_engine",
        payload={
            "repair_action_id": repair_action.id,
            "business_exception_id": business_exception.id,
            "action_type": repair_action.action_type,
            "status": repair_action.status,
        },
    )
    await commit_or_conflict(session, "repair action already exists")
    return repair_action


async def list_repair_actions(
    session: AsyncSession,
    *,
    tenant_id: str,
    business_exception_id: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[RepairAction]:
    await ensure_tenant_exists(session, tenant_id)
    query = (
        select(RepairAction)
        .where(RepairAction.tenant_id == tenant_id)
        .order_by(RepairAction.created_at.desc())
        .limit(limit)
    )
    if business_exception_id:
        query = query.where(RepairAction.business_exception_id == business_exception_id)
    if status_filter:
        query = query.where(RepairAction.status == status_filter)
    result = await session.execute(query)
    return list(result.scalars().all())


async def _tenant_repair_action(
    session: AsyncSession,
    *,
    tenant_id: str,
    repair_action_id: str,
) -> RepairAction:
    await ensure_tenant_exists(session, tenant_id)
    repair_action = await session.get(RepairAction, repair_action_id)
    if not repair_action or repair_action.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="repair action not found")
    return repair_action


async def approve_repair_action(
    session: AsyncSession,
    *,
    tenant_id: str,
    repair_action_id: str,
    actor: ActorContext,
) -> RepairAction:
    repair_action = await _tenant_repair_action(session, tenant_id=tenant_id, repair_action_id=repair_action_id)
    if repair_action.status not in {"proposed", "approved"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="repair action cannot be approved")
    approved_at = datetime.now(UTC)
    repair_action.status = "approved"
    repair_action.updated_at = approved_at
    repair_action.approved_at = repair_action.approved_at or approved_at
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="repair_action.approved",
        entity_type="repair_action",
        entity_id=repair_action.id,
        summary=f"Repair action approved: {repair_action.action_type}",
        metadata={
            "repair_action_id": repair_action.id,
            "business_exception_id": repair_action.business_exception_id,
            "action_type": repair_action.action_type,
        },
    )
    await commit_or_conflict(session, "repair action approval failed")
    return repair_action


async def execute_repair_action(
    session: AsyncSession,
    *,
    tenant_id: str,
    repair_action_id: str,
    payload: RepairActionExecutionRequest,
    actor: ActorContext,
) -> RepairAction:
    repair_action = await _tenant_repair_action(session, tenant_id=tenant_id, repair_action_id=repair_action_id)
    if repair_action.requires_approval and repair_action.status != "approved":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="repair action approval required")
    if repair_action.status == "executed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="repair action already executed")

    try:
        action_payload = json.loads(repair_action.payload_json or "{}")
    except json.JSONDecodeError:
        action_payload = {"payload_valid": False}
    if not isinstance(action_payload, dict):
        action_payload = {"payload_valid": False}

    execution_payload = {
        "repair_action_id": repair_action.id,
        "business_exception_id": repair_action.business_exception_id,
        "action_type": repair_action.action_type,
        "mode": payload.mode,
        "dry_run": payload.mode == "dry_run",
        "external_mutation": False,
        "note": payload.note,
        "payload": action_payload,
    }
    outbox = await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="repair_action.execution_requested",
        adapter_key=str(action_payload.get("target_adapter_key") or "internal.repair_engine"),
        payload=execution_payload,
    )
    executed_at = datetime.now(UTC)
    repair_action.status = "executed"
    repair_action.updated_at = executed_at
    repair_action.executed_at = executed_at
    repair_action.result_json = json.dumps(
        {
            "mode": payload.mode,
            "dry_run": payload.mode == "dry_run",
            "external_mutation": False,
            "outbox_event_id": outbox.id,
            "queued_event_type": outbox.event_type,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="repair_action.executed",
        entity_type="repair_action",
        entity_id=repair_action.id,
        summary=f"Repair action executed: {repair_action.action_type}",
        metadata={
            "repair_action_id": repair_action.id,
            "business_exception_id": repair_action.business_exception_id,
            "action_type": repair_action.action_type,
            "mode": payload.mode,
            "outbox_event_id": outbox.id,
        },
    )
    await commit_or_conflict(session, "repair action execution failed")
    return repair_action


def _json_dict(raw_json: str | None) -> dict[str, object]:
    try:
        payload = json.loads(raw_json or "{}")
    except json.JSONDecodeError:
        return {"payload_valid": False}
    if not isinstance(payload, dict):
        return {"payload_valid": False}
    return payload


def _subject_label(subject_type: str | None, subject_id: str | None) -> str:
    if subject_type and subject_id:
        return f"{subject_type}:{subject_id}"
    if subject_type:
        return f"{subject_type}:*"
    if subject_id:
        return f"*:{subject_id}"
    return "tenant"


def _briefing_risk_level(exceptions: list[BusinessException], repairs: list[RepairAction]) -> str:
    open_exceptions = [item for item in exceptions if item.status != "resolved"]
    if any(item.severity == "critical" for item in open_exceptions):
        return "critical"
    if any(item.severity == "warning" for item in open_exceptions):
        return "attention"
    if any(item.status in {"proposed", "approved"} for item in repairs):
        return "attention"
    return "normal"


def _briefing_repair_action(
    *,
    tenant_id: str,
    repair: RepairAction,
) -> dict[str, object]:
    if repair.status == "proposed" and repair.requires_approval:
        return {
            "action": "review_repair_action",
            "status": "requires_approval",
            "summary": repair.summary,
            "endpoint": f"POST /tenants/{tenant_id}/repair-actions/{repair.id}/approve",
            "evidence": "repair_action.proposed",
        }
    if repair.status == "approved":
        return {
            "action": "execute_repair_dry_run",
            "status": "ready",
            "summary": repair.summary,
            "endpoint": f"POST /tenants/{tenant_id}/repair-actions/{repair.id}/execute",
            "evidence": "repair_action.approved",
        }
    return {
        "action": "inspect_repair_result",
        "status": repair.status,
        "summary": repair.summary,
        "endpoint": f"GET /tenants/{tenant_id}/repair-actions?business_exception_id={repair.business_exception_id}",
        "evidence": "repair_action.executed" if repair.status == "executed" else "repair_action.proposed",
    }


async def build_business_briefing(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessBriefingPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    observations_query = (
        select(BusinessStateObservation)
        .where(BusinessStateObservation.tenant_id == tenant_id)
        .order_by(BusinessStateObservation.observed_at.desc(), BusinessStateObservation.created_at.desc())
        .limit(payload.limit)
    )
    exceptions_query = (
        select(BusinessException)
        .where(BusinessException.tenant_id == tenant_id)
        .order_by(BusinessException.detected_at.desc(), BusinessException.created_at.desc())
        .limit(payload.limit)
    )
    repairs_query = (
        select(RepairAction)
        .where(RepairAction.tenant_id == tenant_id)
        .order_by(RepairAction.created_at.desc())
        .limit(payload.limit)
    )
    if payload.subject_type:
        observations_query = observations_query.where(BusinessStateObservation.subject_type == payload.subject_type)
        exceptions_query = exceptions_query.where(BusinessException.subject_type == payload.subject_type)
    if payload.subject_id:
        observations_query = observations_query.where(BusinessStateObservation.subject_id == payload.subject_id)
        exceptions_query = exceptions_query.where(BusinessException.subject_id == payload.subject_id)
    if not payload.include_resolved:
        exceptions_query = exceptions_query.where(BusinessException.status != "resolved")
        repairs_query = repairs_query.where(RepairAction.status != "executed")

    observations_result = await session.execute(observations_query)
    exceptions_result = await session.execute(exceptions_query)
    observations = list(observations_result.scalars().all())
    exceptions = list(exceptions_result.scalars().all())
    exception_ids = {item.id for item in exceptions}
    subject_filter_requested = bool(payload.subject_type or payload.subject_id)
    if exception_ids:
        repairs_query = repairs_query.where(RepairAction.business_exception_id.in_(exception_ids))
    elif subject_filter_requested:
        repairs_query = repairs_query.where(RepairAction.business_exception_id == "__no_matching_exception__")
    repairs_result = await session.execute(repairs_query)
    repairs = list(repairs_result.scalars().all())

    source_systems = sorted({item.system_key for item in observations})
    risk_level = _briefing_risk_level(exceptions, repairs)
    subject = _subject_label(payload.subject_type, payload.subject_id)
    open_count = len([item for item in exceptions if item.status != "resolved"])
    summary = (
        f"{payload.role} briefing for {subject}: {open_count} open exception(s), "
        f"{len(source_systems)} source system(s), {len(repairs)} pending repair action(s)."
    )

    highlights: list[dict[str, object]] = []
    for exception in exceptions[:5]:
        impact = _json_dict(exception.impact_json)
        highlights.append(
            {
                "type": "business_exception",
                "severity": exception.severity,
                "status": exception.status,
                "title": exception.title,
                "subject": _subject_label(exception.subject_type, exception.subject_id),
                "impact": impact,
                "evidence": "business_exception.created",
            }
        )
    for observation in observations[:5]:
        observation_payload = _json_dict(observation.payload_json)
        highlights.append(
            {
                "type": "state_observation",
                "system": observation.system_key,
                "state": observation.state,
                "subject": _subject_label(observation.subject_type, observation.subject_id),
                "observed_at": observation.observed_at.isoformat(),
                "payload_keys": sorted(observation_payload.keys()),
                "evidence": "business_state.observation.recorded",
            }
        )

    repair_exception_ids = {repair.business_exception_id for repair in repairs}
    recommended_actions = [
        _briefing_repair_action(tenant_id=tenant_id, repair=repair)
        for repair in repairs[:5]
    ]
    for exception in exceptions[:5]:
        if exception.id not in repair_exception_ids and exception.status != "resolved":
            recommended_actions.append(
                {
                    "action": "propose_repair_action",
                    "status": "available",
                    "summary": f"Create a repair action for {exception.exception_type}.",
                    "endpoint": (
                        "POST "
                        f"/tenants/{tenant_id}/business-exceptions/{exception.id}/repair-actions"
                    ),
                    "evidence": "business_exception.created",
                }
            )

    review_points = [
        {
            "name": "source_evidence",
            "status": "ready" if source_systems else "missing",
            "detail": "Briefing is based on normalized observations, exceptions, and repair actions.",
        },
        {
            "name": "external_mutation",
            "status": "review_required" if recommended_actions else "not_requested",
            "detail": "External writes stay behind the existing repair action approval and outbox evidence path.",
        },
        {
            "name": "role_context",
            "status": payload.role,
            "detail": "The same business facts can be rendered for accountant, operator, manager, owner, or support work.",
        },
    ]

    evidence: list[dict[str, object]] = []
    for observation in observations[:5]:
        evidence.append(
            {
                "type": "observation",
                "id": observation.id,
                "system": observation.system_key,
                "state": observation.state,
                "event": "business_state.observation.recorded",
            }
        )
    for exception in exceptions[:5]:
        evidence.append(
            {
                "type": "exception",
                "id": exception.id,
                "severity": exception.severity,
                "status": exception.status,
                "event": "business_exception.created",
            }
        )
    for repair in repairs[:5]:
        evidence.append(
            {
                "type": "repair_action",
                "id": repair.id,
                "status": repair.status,
                "action": repair.action_type,
                "event": "repair_action.proposed",
            }
        )

    return {
        "tenant_id": tenant_id,
        "role": payload.role,
        "subject_type": payload.subject_type,
        "subject_id": payload.subject_id,
        "generated_at": datetime.now(UTC),
        "risk_level": risk_level,
        "summary": summary,
        "source_systems": source_systems,
        "highlights": highlights,
        "recommended_actions": recommended_actions,
        "review_points": review_points,
        "evidence": evidence,
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-briefings/preview",
            "observations": "GET /tenants/{tenant_id}/business-state/observations",
            "exceptions": "GET /tenants/{tenant_id}/business-exceptions",
            "repair_actions": "GET /tenants/{tenant_id}/repair-actions",
        },
    }


SEVERITY_RANK = {"info": 1, "warning": 2, "critical": 3}


def _escalation_owner_role(business_exception: BusinessException) -> str:
    if business_exception.severity == "critical":
        return "owner"
    if business_exception.exception_type in {"crm_payment_mismatch"}:
        return "accountant"
    if "support" in business_exception.exception_type:
        return "support"
    return "operator"


def _escalation_sla_minutes(severity: str) -> int:
    if severity == "critical":
        return 15
    if severity == "warning":
        return 120
    return 1440


def _escalation_queue(owner_role: str) -> str:
    if owner_role == "accountant":
        return "finance_reconciliation"
    if owner_role == "owner":
        return "owner_review"
    if owner_role == "manager":
        return "ops_management"
    if owner_role == "support":
        return "support_queue"
    return "operations_triage"


def _repair_next_action(
    *,
    tenant_id: str,
    business_exception: BusinessException,
    repair: RepairAction | None,
) -> dict[str, object]:
    if repair is None:
        return {
            "action": "propose_repair_action",
            "status": "available",
            "summary": f"Create a repair action for {business_exception.exception_type}.",
            "endpoint": f"POST /tenants/{tenant_id}/business-exceptions/{business_exception.id}/repair-actions",
            "requires_approval": True,
            "external_mutation": False,
            "evidence": "business_exception.created",
        }
    if repair.status == "proposed" and repair.requires_approval:
        return {
            "action": "approve_repair_action",
            "status": "requires_approval",
            "summary": repair.summary,
            "endpoint": f"POST /tenants/{tenant_id}/repair-actions/{repair.id}/approve",
            "requires_approval": True,
            "external_mutation": False,
            "evidence": "repair_action.proposed",
            "repair_action_id": repair.id,
        }
    if repair.status == "approved":
        return {
            "action": "execute_repair_dry_run",
            "status": "ready",
            "summary": repair.summary,
            "endpoint": f"POST /tenants/{tenant_id}/repair-actions/{repair.id}/execute",
            "requires_approval": False,
            "external_mutation": False,
            "evidence": "repair_action.approved",
            "repair_action_id": repair.id,
        }
    return {
        "action": "inspect_repair_result",
        "status": repair.status,
        "summary": repair.summary,
        "endpoint": f"GET /tenants/{tenant_id}/repair-actions?business_exception_id={repair.business_exception_id}",
        "requires_approval": False,
        "external_mutation": False,
        "evidence": "repair_action.executed" if repair.status == "executed" else "repair_action.proposed",
        "repair_action_id": repair.id,
    }


def _latest_repair_by_exception(repairs: list[RepairAction]) -> dict[str, RepairAction]:
    latest: dict[str, RepairAction] = {}
    for repair in repairs:
        previous = latest.get(repair.business_exception_id)
        if previous is None or repair.created_at > previous.created_at:
            latest[repair.business_exception_id] = repair
    return latest


async def preview_business_action_plan(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessActionPlanPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    observations_query = (
        select(BusinessStateObservation)
        .where(BusinessStateObservation.tenant_id == tenant_id)
        .order_by(BusinessStateObservation.observed_at.desc(), BusinessStateObservation.created_at.desc())
        .limit(payload.limit)
    )
    exceptions_query = (
        select(BusinessException)
        .where(BusinessException.tenant_id == tenant_id)
        .order_by(BusinessException.detected_at.desc(), BusinessException.created_at.desc())
        .limit(payload.limit)
    )
    if payload.subject_type:
        observations_query = observations_query.where(BusinessStateObservation.subject_type == payload.subject_type)
        exceptions_query = exceptions_query.where(BusinessException.subject_type == payload.subject_type)
    if payload.subject_id:
        observations_query = observations_query.where(BusinessStateObservation.subject_id == payload.subject_id)
        exceptions_query = exceptions_query.where(BusinessException.subject_id == payload.subject_id)
    if not payload.include_resolved:
        exceptions_query = exceptions_query.where(BusinessException.status != "resolved")

    observations_result = await session.execute(observations_query)
    exceptions_result = await session.execute(exceptions_query)
    observations = list(observations_result.scalars().all())
    exceptions = list(exceptions_result.scalars().all())
    exception_ids = [item.id for item in exceptions]
    repairs: list[RepairAction] = []
    if exception_ids:
        repairs_result = await session.execute(
            select(RepairAction)
            .where(
                RepairAction.tenant_id == tenant_id,
                RepairAction.business_exception_id.in_(exception_ids),
            )
            .order_by(RepairAction.created_at.desc())
        )
        repairs = list(repairs_result.scalars().all())

    repairs_by_exception = _latest_repair_by_exception(repairs)
    source_systems = sorted({item.system_key for item in observations})
    lanes: dict[str, dict[str, object]] = {}
    steps: list[dict[str, object]] = []
    automation_candidates: list[dict[str, object]] = []
    approval_gates: list[dict[str, object]] = []
    evidence: list[dict[str, object]] = []
    sequence = 1

    for observation in observations[:5]:
        evidence.append(
            {
                "type": "observation",
                "id": observation.id,
                "system": observation.system_key,
                "state": observation.state,
                "event": "business_state.observation.recorded",
            }
        )

    for business_exception in exceptions:
        owner_role = _escalation_owner_role(business_exception)
        queue = _escalation_queue(owner_role)
        sla_minutes = _escalation_sla_minutes(business_exception.severity)
        lane = lanes.setdefault(
            queue,
            {
                "lane": queue,
                "owner_role": owner_role,
                "sla_minutes": sla_minutes,
                "work_items": 0,
                "status": "active",
            },
        )
        lane["work_items"] = int(lane["work_items"]) + 1
        lane["sla_minutes"] = min(int(lane["sla_minutes"]), sla_minutes)

        repair = repairs_by_exception.get(business_exception.id)
        next_action = _repair_next_action(
            tenant_id=tenant_id,
            business_exception=business_exception,
            repair=repair,
        )
        subject = _subject_label(business_exception.subject_type, business_exception.subject_id)

        steps.append(
            {
                "sequence": sequence,
                "step": "verify_source_evidence",
                "lane": queue,
                "owner_role": owner_role,
                "actor_role": payload.role,
                "status": "ready" if source_systems else "blocked",
                "summary": f"Review normalized evidence for {subject} before any repair.",
                "source_systems": source_systems,
                "endpoint": "GET /tenants/{tenant_id}/business-state/observations",
                "requires_approval": False,
                "external_mutation": False,
                "evidence": "business_state.observation.recorded",
            }
        )
        sequence += 1

        steps.append(
            {
                "sequence": sequence,
                "step": next_action["action"],
                "lane": queue,
                "owner_role": owner_role,
                "actor_role": payload.role,
                "status": next_action["status"],
                "summary": next_action["summary"],
                "endpoint": next_action["endpoint"],
                "requires_approval": next_action["requires_approval"],
                "external_mutation": next_action["external_mutation"],
                "repair_action_id": next_action.get("repair_action_id"),
                "evidence": next_action["evidence"],
            }
        )
        sequence += 1

        close_status = "available" if repair is not None and repair.status == "executed" else "waiting_for_repair"
        steps.append(
            {
                "sequence": sequence,
                "step": "close_or_acknowledge_exception",
                "lane": queue,
                "owner_role": owner_role,
                "actor_role": payload.role,
                "status": close_status,
                "summary": f"Record the operator decision for {business_exception.exception_type}.",
                "endpoint": f"POST /tenants/{tenant_id}/business-exceptions/{business_exception.id}/status",
                "requires_approval": False,
                "external_mutation": False,
                "evidence": "business_exception.status_changed",
            }
        )
        sequence += 1

        if repair is not None:
            approval_gates.append(
                {
                    "name": "repair_action_approval",
                    "repair_action_id": repair.id,
                    "status": "satisfied" if repair.status in {"approved", "executed"} else "required",
                    "requires_approval": repair.requires_approval,
                    "external_mutation": False,
                    "evidence": "repair_action.approved" if repair.status in {"approved", "executed"} else "repair_action.proposed",
                }
            )
            automation_candidates.append(
                {
                    "name": "queue_repair_execution",
                    "status": "ready" if repair.status == "approved" else repair.status,
                    "action": next_action["action"],
                    "adapter_key": "internal.noop",
                    "endpoint": next_action["endpoint"],
                    "external_mutation": False,
                    "evidence": next_action["evidence"],
                }
            )
        else:
            approval_gates.append(
                {
                    "name": "repair_action_approval",
                    "business_exception_id": business_exception.id,
                    "status": "missing_repair_action",
                    "requires_approval": True,
                    "external_mutation": False,
                    "evidence": "business_exception.created",
                }
            )

        if any(_observation_family(item.system_key) == "accounting" for item in observations):
            automation_candidates.append(
                {
                    "name": "recheck_accounting_export",
                    "status": "available",
                    "action": "run_read_only_connection_check",
                    "adapter_key": "accounting.export.mock",
                    "endpoint": "POST /tenants/{tenant_id}/integration-connections/{connection_id}/checks",
                    "external_mutation": False,
                    "evidence": "integration_connection.check.requested",
                }
            )

        evidence.append(
            {
                "type": "business_exception",
                "id": business_exception.id,
                "severity": business_exception.severity,
                "status": business_exception.status,
                "event": "business_exception.created",
            }
        )
        if repair is not None:
            evidence.append(
                {
                    "type": "repair_action",
                    "id": repair.id,
                    "status": repair.status,
                    "action": repair.action_type,
                    "event": "repair_action.proposed",
                }
            )

    lanes_list = sorted(
        lanes.values(),
        key=lambda item: (int(item["sla_minutes"]), str(item["lane"])),
    )
    risk_level = _briefing_risk_level(exceptions, repairs)
    summary = (
        f"{payload.plan_kind} plan for {payload.role}: {len(steps)} step(s), "
        f"{len(lanes_list)} lane(s), {len(automation_candidates)} automation candidate(s)."
    )
    return {
        "tenant_id": tenant_id,
        "plan_kind": payload.plan_kind,
        "role": payload.role,
        "subject_type": payload.subject_type,
        "subject_id": payload.subject_id,
        "generated_at": datetime.now(UTC),
        "risk_level": risk_level,
        "summary": summary,
        "lanes": lanes_list,
        "steps": steps,
        "automation_candidates": automation_candidates,
        "approval_gates": approval_gates,
        "review_points": [
            {
                "name": "single_work_surface",
                "status": "ready" if steps else "empty",
                "detail": "The plan turns cross-system state into ordered operator work inside DriveDesk.",
            },
            {
                "name": "approval_boundary",
                "status": "satisfied" if approval_gates and all(item["status"] == "satisfied" for item in approval_gates) else "review_required",
                "detail": "External-facing repair execution stays behind existing repair approval evidence.",
            },
            {
                "name": "automation_boundary",
                "status": "preview_only",
                "detail": "Action plan preview does not create tasks, notify users, or mutate external systems.",
            },
        ],
        "evidence": evidence,
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-action-plans/preview",
            "detections": "POST /tenants/{tenant_id}/business-detections/preview",
            "escalations": "POST /tenants/{tenant_id}/business-escalations/preview",
            "briefings": "POST /tenants/{tenant_id}/business-briefings/preview",
            "execute_repair": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
        },
    }


def _notification_channel_state(channel: str) -> dict[str, object]:
    if channel == "in_app":
        return {
            "channel": channel,
            "status": "ready",
            "configured": True,
            "external_delivery": False,
            "requires_secret": False,
            "evidence": "business_notification.previewed",
        }
    return {
        "channel": channel,
        "status": "requires_channel_config",
        "configured": False,
        "external_delivery": False,
        "requires_secret": True,
        "evidence": "business_notification.previewed",
    }


async def preview_business_notifications(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessNotificationPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    action_plan = await preview_business_action_plan(
        session,
        tenant_id=tenant_id,
        payload=BusinessActionPlanPreviewCreate(
            plan_kind="exception_resolution",
            role=payload.role,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            include_resolved=payload.include_resolved,
            limit=payload.limit,
        ),
    )
    channels = [_notification_channel_state(channel) for channel in payload.channels]
    steps = list(action_plan.get("steps", []))
    lanes = list(action_plan.get("lanes", []))
    approval_gates = list(action_plan.get("approval_gates", []))
    primary_step = steps[1] if len(steps) > 1 else (steps[0] if steps else {})
    subject = _subject_label(payload.subject_type, payload.subject_id)
    recipient_role = str(primary_step.get("owner_role") or payload.role)
    action_status = str(primary_step.get("status") or "not_ready")
    source_systems = sorted(
        {
            system
            for step in steps
            for system in step.get("source_systems", [])
            if isinstance(system, str)
        }
    )
    drafts: list[dict[str, object]] = []
    delivery_plan: list[dict[str, object]] = []
    for channel in channels:
        channel_name = str(channel["channel"])
        draft = {
            "draft_id": f"{payload.notification_kind}.{channel_name}.{recipient_role}",
            "channel": channel_name,
            "recipient_role": recipient_role,
            "title": "Payment mismatch action plan is ready",
            "body": (
                f"{subject} has a {action_status} action plan step: "
                f"{primary_step.get('step', 'review_action_plan')}."
            ),
            "action_endpoint": str(primary_step.get("endpoint") or action_plan.get("api", {}).get("preview")),
            "source_systems": source_systems,
            "pii_included": False,
            "external_delivery": False,
            "status": "ready" if channel_name == "in_app" else "preview_only",
            "evidence": "business_notification.previewed",
        }
        drafts.append(draft)
        delivery_plan.append(
            {
                "channel": channel_name,
                "status": channel["status"],
                "recipient_role": recipient_role,
                "send_mode": "preview_only",
                "external_delivery": False,
                "requires_secret": channel["requires_secret"],
                "would_enqueue_event": "notification.delivery.requested",
                "evidence": "business_notification.previewed",
            }
        )

    summary = (
        f"{payload.notification_kind} preview prepared {len(drafts)} draft(s) "
        f"for {recipient_role} across {len(channels)} channel(s)."
    )
    return {
        "tenant_id": tenant_id,
        "notification_kind": payload.notification_kind,
        "role": payload.role,
        "subject_type": payload.subject_type,
        "subject_id": payload.subject_id,
        "generated_at": datetime.now(UTC),
        "risk_level": str(action_plan.get("risk_level", "normal")),
        "summary": summary,
        "channels": channels,
        "drafts": drafts,
        "delivery_plan": delivery_plan,
        "approval_gates": [
            {
                "name": "notification_content_review",
                "status": "ready" if drafts else "empty",
                "requires_approval": False,
                "external_delivery": False,
                "evidence": "business_notification.previewed",
            },
            *approval_gates,
        ],
        "review_points": [
            {
                "name": "no_external_send",
                "status": "preview_only",
                "detail": "Notification preview does not enqueue outbox events or call Telegram, email, or CRM providers.",
            },
            {
                "name": "pii_boundary",
                "status": "clean" if all(item["pii_included"] is False for item in drafts) else "review_required",
                "detail": "Drafts include role, subject key, action endpoint, and evidence labels, not raw personal data.",
            },
            {
                "name": "action_plan_link",
                "status": "ready" if steps else "empty",
                "detail": "Notification drafts are generated from the current action plan preview.",
            },
        ],
        "evidence": [
            {
                "type": "action_plan",
                "event": "business_action_plan.previewed",
                "step_count": len(steps),
                "lane_count": len(lanes),
            },
            *list(action_plan.get("evidence", []))[:5],
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-notifications/preview",
            "action_plan": "POST /tenants/{tenant_id}/business-action-plans/preview",
            "briefing": "POST /tenants/{tenant_id}/business-briefings/preview",
        },
    }


def _notification_matrix_channel_state(
    channel: str,
    *,
    role: str,
    subject: str,
) -> dict[str, object]:
    profiles: dict[str, dict[str, object]] = {
        "in_app": {
            "status": "ready",
            "configured": True,
            "destination_profile": "internal_user_inbox",
            "requires_secret": False,
            "requires_private_connector": False,
            "send_mode": "internal_preview",
            "readiness": "usable_for_internal_work",
        },
        "telegram": {
            "status": "requires_private_secret",
            "configured": False,
            "destination_profile": "telegram_bot_chat",
            "requires_secret": True,
            "requires_private_connector": True,
            "send_mode": "draft_only",
            "readiness": "private_connector_needed",
        },
        "email": {
            "status": "requires_private_secret",
            "configured": False,
            "destination_profile": "smtp_or_provider_template",
            "requires_secret": True,
            "requires_private_connector": True,
            "send_mode": "draft_only",
            "readiness": "private_connector_needed",
        },
        "sms": {
            "status": "requires_private_provider",
            "configured": False,
            "destination_profile": "sms_provider_template",
            "requires_secret": True,
            "requires_private_connector": True,
            "send_mode": "draft_only",
            "readiness": "provider_contract_needed",
        },
        "webhook": {
            "status": "requires_private_endpoint",
            "configured": False,
            "destination_profile": "signed_webhook_endpoint",
            "requires_secret": True,
            "requires_private_connector": True,
            "send_mode": "draft_only",
            "readiness": "endpoint_and_signing_key_needed",
        },
    }
    profile = profiles.get(channel, profiles["in_app"])
    return {
        "channel": channel,
        "status": profile["status"],
        "configured": profile["configured"],
        "recipient_role": role,
        "subject": subject,
        "destination_profile": profile["destination_profile"],
        "send_mode": profile["send_mode"],
        "readiness": profile["readiness"],
        "external_delivery": False,
        "requires_secret": profile["requires_secret"],
        "requires_private_connector": profile["requires_private_connector"],
        "external_provider_mutation": False,
        "contains_pii": False,
        "raw_payload_included": False,
        "safe_payload_profile": "role_subject_action_reference",
        "evidence": "business_notification_channel_matrix.previewed",
    }


async def preview_business_notification_channel_matrix(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessNotificationChannelMatrixPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    subject_type = payload.subject_type or "deal"
    subject_id = payload.subject_id or "DEAL-2026-001"
    subject = _subject_label(subject_type, subject_id)
    requested_channels = list(dict.fromkeys(payload.channels))
    channels = [
        _notification_matrix_channel_state(channel, role=payload.role, subject=subject)
        for channel in requested_channels
    ]
    ready_internal = [item for item in channels if item["status"] == "ready"]
    private_required = [item for item in channels if bool(item["requires_private_connector"])]
    delivery_drafts = [
        {
            "draft_id": f"channel_matrix.{channel['channel']}.{payload.role}",
            "channel": channel["channel"],
            "recipient_role": payload.role,
            "subject": subject,
            "title": "DriveDesk action update",
            "body": f"{subject} has an operator action ready for {payload.role}.",
            "status": "ready" if channel["status"] == "ready" else "draft_only",
            "send_mode": channel["send_mode"],
            "would_enqueue_event": "notification.delivery.requested",
            "safe_payload_profile": "role_subject_action_reference",
            "external_delivery": False,
            "requires_secret": bool(channel["requires_secret"]),
            "contains_pii": False,
            "raw_payload_included": False,
            "evidence": "business_notification_channel_matrix.previewed",
        }
        for channel in channels
    ] if payload.include_delivery_drafts else []

    return {
        "tenant_id": tenant_id,
        "matrix_kind": payload.matrix_kind,
        "role": payload.role,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "generated_at": datetime.now(UTC),
        "status": "previewed",
        "summary": (
            f"Notification channel matrix preview evaluated {len(channels)} channel(s), "
            f"found {len(ready_internal)} internal-ready channel(s), and kept "
            f"{len(private_required)} private connector channel(s) in draft-only mode."
        ),
        "channels": channels,
        "routing_rules": [
            {
                "rule": "prefer_internal_in_app",
                "status": "ready" if ready_internal else "empty",
                "channel": "in_app",
                "detail": "Internal work notifications can be represented without external delivery.",
                "evidence": "business_notification_channel_matrix.previewed",
            },
            {
                "rule": "external_channels_require_private_connector",
                "status": "required" if private_required else "not_needed",
                "channel_count": len(private_required),
                "detail": "Telegram, email, SMS, and webhook delivery stay behind private connector and secret setup.",
                "evidence": "business_notification_channel_matrix.previewed",
            },
            {
                "rule": "safe_payload_only",
                "status": "clean",
                "payload_profile": "role_subject_action_reference",
                "detail": "Channel drafts use role, subject key, title, action reference, and evidence labels only.",
                "evidence": "business_notification_channel_matrix.previewed",
            },
        ],
        "delivery_drafts": delivery_drafts,
        "approval_gates": [
            {
                "gate": "notification_content_review",
                "status": "ready",
                "requires_approval": False,
                "external_delivery": False,
                "evidence": "business_notification_channel_matrix.previewed",
            },
            {
                "gate": "private_channel_secret_setup",
                "status": "required" if private_required else "not_needed",
                "requires_approval": True,
                "external_delivery": False,
                "evidence": "business_notification_channel_matrix.previewed",
            },
            {
                "gate": "external_delivery_gate",
                "status": "closed",
                "requires_approval": True,
                "external_delivery": False,
                "evidence": "business_notification_channel_matrix.previewed",
            },
        ],
        "data_boundaries": [
            {
                "name": "preview_only_no_delivery",
                "status": "preview_only",
                "external_delivery": False,
                "external_provider_mutation": False,
                "detail": "The channel matrix does not enqueue outbox rows or call Telegram, email, SMS, webhook, CRM, or bank APIs.",
            },
            {
                "name": "server_secret_store_boundary",
                "status": "documented",
                "requires_secret": True,
                "browser_token_storage": False,
                "detail": "External channel credentials belong to private server-side connector configuration, not the public demo.",
            },
            {
                "name": "safe_notification_payload",
                "status": "clean",
                "contains_pii": False,
                "raw_payload_included": False,
                "detail": "Drafts expose only role, subject key, action summary, channel, and evidence labels.",
            },
        ],
        "evidence": [
            {
                "type": "notification_channel_matrix",
                "event": "business_notification_channel_matrix.previewed",
                "channel_count": len(channels),
                "ready_internal_count": len(ready_internal),
                "private_connector_required_count": len(private_required),
                "delivery_draft_count": len(delivery_drafts),
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-notification-channels/preview",
            "notifications": "POST /tenants/{tenant_id}/business-notifications/preview",
            "task_handoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
            "provider_connector_guide": "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
        },
    }


SAFE_CONTEXT_FACT_KEYS = {
    "amount_bucket",
    "export_batch_id",
    "matched_by",
    "owner_role",
    "reason",
}

SAFE_PROVIDER_DIRECT_KEYS = SAFE_CONTEXT_FACT_KEYS | {
    "currency",
    "invoice_id",
    "payment_status",
    "source_state",
}

UNSAFE_PROVIDER_KEY_TOKENS = {
    "address",
    "authorization",
    "birth",
    "cookie",
    "email",
    "full_name",
    "name",
    "passport",
    "password",
    "phone",
    "raw",
    "secret",
    "session",
    "telegram",
    "token",
}


def _preview_bucket_amount(value: object) -> str | None:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if amount < 0:
        return "negative"
    if amount < 1000:
        return "0-1000"
    if amount < 2000:
        return "1000-2000"
    if amount < 5000:
        return "2000-5000"
    return "5000+"


def _provider_key_is_unsafe(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in UNSAFE_PROVIDER_KEY_TOKENS)


def _clean_preview_state(value: object, fallback: str) -> str:
    raw = str(value or fallback).strip().lower()
    cleaned = "".join(character if character.isalnum() else "_" for character in raw)
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:64] or fallback


def _safe_provider_payload(provider_payload: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    safe_payload: dict[str, object] = {}
    dropped_keys: list[str] = []
    for key, value in sorted(provider_payload.items()):
        if _provider_key_is_unsafe(key):
            dropped_keys.append(key)
            continue
        if key in {"amount", "amount_cents", "sum", "total"}:
            bucket = _preview_bucket_amount(value)
            if bucket:
                safe_payload.setdefault("amount_bucket", bucket)
            else:
                dropped_keys.append(key)
            continue
        if key in SAFE_PROVIDER_DIRECT_KEYS and isinstance(value, str | int | float | bool):
            safe_payload[key] = value
            continue
        if key in {"stage", "status", "state"} and isinstance(value, str):
            safe_payload["source_state"] = _clean_preview_state(value, "received")
            continue
        dropped_keys.append(key)
    return safe_payload, sorted(set(dropped_keys))


def _provider_preview_state(source_type: str, provider_payload: dict[str, object]) -> str:
    if source_type == "crm_deal":
        return _clean_preview_state(
            provider_payload.get("state") or provider_payload.get("stage") or provider_payload.get("status"),
            "invoice_sent",
        )
    if source_type == "bank_payment":
        raw_state = _clean_preview_state(
            provider_payload.get("state") or provider_payload.get("payment_status") or provider_payload.get("status"),
            "paid",
        )
        return "paid" if raw_state in {"success", "succeeded", "completed", "captured"} else raw_state
    if source_type == "accounting_export":
        return _clean_preview_state(
            provider_payload.get("state") or provider_payload.get("export_status") or provider_payload.get("status"),
            "not_exported",
        )
    return _clean_preview_state(provider_payload.get("state") or provider_payload.get("status"), "received")


async def preview_business_provider_intake(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessProviderIntakePreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    provider_payload = dict(payload.provider_payload)
    safe_payload, dropped_keys = _safe_provider_payload(provider_payload)
    state = _provider_preview_state(payload.source_type, provider_payload)
    external_ref = payload.external_ref or str(
        provider_payload.get("external_ref")
        or provider_payload.get("id")
        or provider_payload.get("deal_id")
        or f"{payload.source_type}:{payload.subject_id}"
    )
    normalized_observation = {
        "system_key": payload.provider_key,
        "system_family": _observation_family(payload.provider_key),
        "subject_type": payload.subject_type,
        "subject_id": payload.subject_id,
        "subject": _subject_label(payload.subject_type, payload.subject_id),
        "external_ref": external_ref,
        "state": state,
        "safe_payload": safe_payload,
        "would_create": "BusinessStateObservation",
        "would_record_event": "business_state.observation.recorded",
        "external_fetch": False,
        "external_mutation": False,
        "raw_payload_included": False,
        "pii_included": False,
        "requires_secret": False,
    }
    summary = (
        f"{payload.source_type} intake from {payload.provider_key}: "
        f"{len(safe_payload)} safe field(s), {len(dropped_keys)} dropped key(s), "
        f"state={state} for {_subject_label(payload.subject_type, payload.subject_id)}."
    )
    return {
        "tenant_id": tenant_id,
        "provider_key": payload.provider_key,
        "source_type": payload.source_type,
        "subject_type": payload.subject_type,
        "subject_id": payload.subject_id,
        "generated_at": datetime.now(UTC),
        "summary": summary,
        "normalized_observation": normalized_observation,
        "safe_payload": safe_payload,
        "payload_keys": sorted(provider_payload.keys()),
        "dropped_keys": dropped_keys,
        "data_boundaries": [
            {
                "name": "preview_only_no_persist",
                "status": "preview_only",
                "external_fetch": False,
                "external_mutation": False,
                "detail": "The intake preview does not create observations, enqueue events, or call provider APIs.",
            },
            {
                "name": "raw_provider_payload_not_returned",
                "status": "clean",
                "raw_payload_included": False,
                "detail": "The response returns safe fields and dropped key names, not the original provider payload.",
            },
            {
                "name": "secret_boundary",
                "status": "clean",
                "requires_secret": False,
                "detail": "No Bitrix, bank, accounting, email, or Telegram credentials are required for preview.",
            },
        ],
        "next_steps": [
            {
                "step": "record_normalized_observation",
                "status": "available",
                "endpoint": "POST /tenants/{tenant_id}/business-state/observations",
                "external_mutation": False,
                "evidence": "business_state.observation.recorded",
            },
            {
                "step": "open_workbench_context",
                "status": "available",
                "endpoint": "POST /tenants/{tenant_id}/business-workbench-context/preview",
                "external_mutation": False,
                "evidence": "business_workbench_context.previewed",
            },
            {
                "step": "run_detection_preview",
                "status": "available",
                "endpoint": "POST /tenants/{tenant_id}/business-detections/preview",
                "external_mutation": False,
                "evidence": "business_detection.previewed",
            },
        ],
        "evidence": [
            {
                "type": "provider_payload",
                "event": "business_provider_intake.previewed",
                "provider_key": payload.provider_key,
                "payload_key_count": len(provider_payload),
                "dropped_key_count": len(dropped_keys),
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-provider-intake/preview",
            "observations": "POST /tenants/{tenant_id}/business-state/observations",
            "workbench_context": "POST /tenants/{tenant_id}/business-workbench-context/preview",
            "detections": "POST /tenants/{tenant_id}/business-detections/preview",
        },
    }


def _pipeline_card_from_intake(preview: dict[str, object]) -> dict[str, object]:
    normalized = preview.get("normalized_observation")
    if not isinstance(normalized, dict):
        normalized = {}
    safe_payload = preview.get("safe_payload")
    if not isinstance(safe_payload, dict):
        safe_payload = {}
    system_key = str(preview.get("provider_key") or normalized.get("system_key") or "unknown.provider")
    family = _observation_family(system_key)
    state = str(normalized.get("state") or "received")
    subject_type = str(preview.get("subject_type") or normalized.get("subject_type") or "subject")
    subject_id = str(preview.get("subject_id") or normalized.get("subject_id") or "unknown")
    status = "available"
    if family == "bank" and state in BANK_PAID_STATES:
        status = "confirmed"
    elif family == "accounting" and state in ACCOUNTING_NOT_EXPORTED_STATES:
        status = "action_required"
    elif family == "crm" and state in CRM_WAITING_PAYMENT_STATES:
        status = "needs_cross_check"
    return {
        "card_id": f"{family}.{subject_type}.{subject_id}.{state}",
        "title": {
            "crm": "CRM signal",
            "bank": "Bank signal",
            "accounting": "Accounting signal",
        }.get(family, "External signal"),
        "system_key": system_key,
        "system_family": family,
        "source_type": preview.get("source_type"),
        "subject_type": subject_type,
        "subject_id": subject_id,
        "subject": _subject_label(subject_type, subject_id),
        "state": state,
        "status": status,
        "safe_facts": [
            {"key": key, "value": str(safe_payload[key])}
            for key in sorted(safe_payload.keys())
        ],
        "payload_keys": list(preview.get("payload_keys") or []),
        "dropped_keys": list(preview.get("dropped_keys") or []),
        "raw_payload_included": False,
        "pii_included": False,
        "external_fetch": False,
        "external_mutation": False,
        "evidence": "business_provider_intake.previewed",
    }


def _pipeline_detect_from_cards(cards: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, object]]] = {}
    for card in cards:
        subject_key = (str(card["subject_type"]), str(card["subject_id"]))
        family = str(card["system_family"])
        if family == "other":
            continue
        grouped.setdefault(subject_key, {})[family] = card

    detected: list[dict[str, object]] = []
    repairs: list[dict[str, object]] = []
    for (subject_type, subject_id), family_cards in grouped.items():
        crm = family_cards.get("crm")
        bank = family_cards.get("bank")
        accounting = family_cards.get("accounting")
        if not crm or not bank or not accounting:
            continue
        if (
            str(crm.get("state")) in CRM_WAITING_PAYMENT_STATES
            and str(bank.get("state")) in BANK_PAID_STATES
            and str(accounting.get("state")) in ACCOUNTING_NOT_EXPORTED_STATES
        ):
            subject = _subject_label(subject_type, subject_id)
            evidence = [
                {
                    "system_key": str(card["system_key"]),
                    "system_family": str(card["system_family"]),
                    "state": str(card["state"]),
                    "status": str(card["status"]),
                    "event": "business_provider_intake.previewed",
                }
                for card in [crm, bank, accounting]
            ]
            detected.append(
                {
                    "exception_type": "crm_payment_mismatch",
                    "severity": "warning",
                    "status": "detected",
                    "subject_type": subject_type,
                    "subject_id": subject_id,
                    "subject": subject,
                    "title": "Payment signal needs CRM and accounting follow-up",
                    "summary": (
                        "Pipeline preview sees bank payment evidence while CRM is still waiting "
                        "for payment and accounting export is pending."
                    ),
                    "confidence": "high",
                    "would_create": "BusinessException",
                    "external_mutation": False,
                    "evidence": evidence,
                }
            )
            repairs.append(
                {
                    "action_type": "sync_status",
                    "safety_level": "medium",
                    "requires_approval": True,
                    "status": "suggested",
                    "subject_type": subject_type,
                    "subject_id": subject_id,
                    "summary": "Review payment evidence, sync CRM status after approval, then unblock accounting export.",
                    "would_create": "RepairAction",
                    "external_mutation": False,
                    "approval_gate": "operator_approval_required",
                }
            )
    return detected, repairs


def _pipeline_action_plan(
    *,
    role: str,
    intake_previews: list[dict[str, object]],
    cards: list[dict[str, object]],
    detected_exceptions: list[dict[str, object]],
    suggested_repairs: list[dict[str, object]],
) -> dict[str, object]:
    steps: list[dict[str, object]] = [
        {
            "step": "normalize_provider_events",
            "status": "previewed",
            "summary": f"Normalize {len(intake_previews)} provider event(s) into safe business facts.",
            "mode": "preview_only",
            "external_mutation": False,
            "evidence": "business_provider_intake.previewed",
        },
        {
            "step": "open_role_workbench",
            "status": "ready" if cards else "empty",
            "summary": f"Render {len(cards)} context card(s) for {role}.",
            "mode": "operator_review",
            "external_mutation": False,
            "evidence": "business_workbench_context.previewed",
        },
    ]
    if detected_exceptions:
        steps.append(
            {
                "step": "review_detected_exceptions",
                "status": "action_required",
                "summary": f"Review {len(detected_exceptions)} detected exception candidate(s).",
                "mode": "operator_review",
                "external_mutation": False,
                "evidence": "business_detection.previewed",
            }
        )
    if suggested_repairs:
        steps.append(
            {
                "step": "prepare_approval_gated_repair",
                "status": "approval_required",
                "summary": f"Prepare {len(suggested_repairs)} repair action(s) behind approval gates.",
                "mode": "approval_required",
                "external_mutation": False,
                "evidence": "business_action_plan.previewed",
            }
        )

    return {
        "plan_kind": "exception_resolution",
        "role": role,
        "risk_level": "attention" if detected_exceptions or suggested_repairs else "normal",
        "summary": (
            f"Pipeline action plan: {len(steps)} step(s), "
            f"{len(suggested_repairs)} approval-gated repair candidate(s)."
        ),
        "lanes": [
            {"lane": "intake", "count": len(intake_previews), "status": "previewed"},
            {"lane": "context", "count": len(cards), "status": "ready" if cards else "empty"},
            {
                "lane": "exceptions",
                "count": len(detected_exceptions),
                "status": "action_required" if detected_exceptions else "clear",
            },
            {
                "lane": "repair",
                "count": len(suggested_repairs),
                "status": "approval_required" if suggested_repairs else "not_requested",
            },
        ],
        "steps": steps,
        "automation_candidates": [
            {
                "candidate": "record_normalized_observations",
                "safe_to_auto_run": True,
                "boundary": "internal_record_only",
                "external_mutation": False,
            },
            {
                "candidate": "create_business_exception",
                "safe_to_auto_run": bool(detected_exceptions),
                "boundary": "internal_record_only",
                "external_mutation": False,
            },
            {
                "candidate": "send_external_notification",
                "safe_to_auto_run": False,
                "boundary": "requires_operator_approval",
                "external_mutation": False,
            },
        ],
        "approval_gates": [
            {
                "gate": "external_write_gate",
                "status": "closed",
                "detail": "Provider writes remain disabled in pipeline preview.",
            },
            {
                "gate": "notification_delivery_gate",
                "status": "approval_required",
                "detail": "Notification output is draft-only until an operator approves delivery.",
            },
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
            "action_plan": "POST /tenants/{tenant_id}/business-action-plans/preview",
            "repair": "POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/repair-actions",
        },
    }


def _pipeline_notification_preview(
    *,
    role: str,
    detected_exceptions: list[dict[str, object]],
    suggested_repairs: list[dict[str, object]],
) -> dict[str, object]:
    risk_level = "attention" if detected_exceptions or suggested_repairs else "normal"
    return {
        "notification_kind": "action_plan_updates",
        "role": role,
        "risk_level": risk_level,
        "summary": (
            f"Draft-only notification preview for {role}: "
            f"{len(detected_exceptions)} exception candidate(s), {len(suggested_repairs)} repair candidate(s)."
        ),
        "channels": [
            {"channel": "in_app", "status": "draft_ready", "external_delivery": False},
            {"channel": "telegram", "status": "approval_required", "external_delivery": False},
            {"channel": "email", "status": "approval_required", "external_delivery": False},
        ],
        "drafts": [
            {
                "audience": role,
                "title": "Business intake pipeline needs review",
                "body": (
                    "DriveDesk detected cross-system context that should be reviewed "
                    "before any provider write or customer notification."
                ),
                "contains_pii": False,
                "external_delivery": False,
                "evidence": "business_notification.previewed",
            }
        ],
        "approval_gates": [
            {
                "gate": "operator_delivery_approval",
                "status": "required",
                "detail": "Preview creates message drafts only; no external notification is sent.",
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-notifications/preview",
            "pipeline": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
        },
    }


async def preview_business_intake_pipeline(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessIntakePipelinePreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    intake_previews = [
        await preview_business_provider_intake(session, tenant_id=tenant_id, payload=event)
        for event in payload.events
    ]
    cards = [_pipeline_card_from_intake(preview) for preview in intake_previews]
    detected_exceptions, suggested_repairs = _pipeline_detect_from_cards(cards)
    source_systems = sorted({str(card["system_key"]) for card in cards})
    role = payload.role
    workbench_context = {
        "context_kind": "role_assist",
        "role": role,
        "risk_level": "attention" if detected_exceptions else "normal",
        "summary": (
            f"Pipeline workbench for {role}: {len(cards)} context card(s) "
            f"from {len(source_systems)} source system(s)."
        ),
        "source_systems": source_systems,
        "context_cards": cards,
        "suggested_actions": [
            {
                "action": "review_pipeline_detection",
                "status": "action_required" if detected_exceptions else "available",
                "summary": "Review safe cross-system facts before persisting exceptions or repair actions.",
                "external_mutation": False,
                "requires_approval": False,
                "evidence": "business_workbench_context.previewed",
            },
            {
                "action": "open_action_plan_preview",
                "status": "ready",
                "summary": "Turn the current pipeline context into ordered operator work.",
                "external_mutation": False,
                "requires_approval": False,
                "evidence": "business_action_plan.previewed",
            },
        ],
        "data_boundaries": [
            {
                "name": "pipeline_preview_only",
                "status": "preview_only",
                "external_fetch": False,
                "external_mutation": False,
                "detail": "The pipeline reads request payloads, returns safe facts, and performs no persistence.",
            },
            {
                "name": "raw_payload_redaction",
                "status": "clean",
                "raw_payload_included": False,
                "detail": "Raw provider payloads are not returned; only safe facts and dropped key names are visible.",
            },
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
            "workbench_context": "POST /tenants/{tenant_id}/business-workbench-context/preview",
        },
    }
    action_plan = _pipeline_action_plan(
        role=role,
        intake_previews=intake_previews,
        cards=cards,
        detected_exceptions=detected_exceptions,
        suggested_repairs=suggested_repairs,
    )
    notification_preview = (
        _pipeline_notification_preview(
            role=role,
            detected_exceptions=detected_exceptions,
            suggested_repairs=suggested_repairs,
        )
        if payload.include_notification_drafts
        else {}
    )
    summary = (
        f"Business intake pipeline preview processed {len(intake_previews)} event(s), "
        f"built {len(cards)} context card(s), detected {len(detected_exceptions)} exception candidate(s), "
        f"and proposed {len(suggested_repairs)} approval-gated repair candidate(s)."
    )
    return {
        "tenant_id": tenant_id,
        "role": role,
        "generated_at": datetime.now(UTC),
        "status": "previewed",
        "summary": summary,
        "source_systems": source_systems,
        "intake_previews": intake_previews,
        "workbench_context": workbench_context,
        "detections": {
            "rule_set": "payment_reconciliation",
            "status": "detected" if detected_exceptions else "clear",
            "summary": (
                f"Pipeline detector found {len(detected_exceptions)} exception candidate(s) "
                f"from {len(cards)} context card(s)."
            ),
            "detected_exceptions": detected_exceptions,
            "suggested_repair_actions": suggested_repairs,
            "external_mutation": False,
            "api": {
                "preview": "POST /tenants/{tenant_id}/business-detections/preview",
                "pipeline": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
            },
        },
        "action_plan": action_plan,
        "notification_preview": notification_preview,
        "data_boundaries": [
            {
                "name": "no_external_calls",
                "status": "clean",
                "external_fetch": False,
                "external_mutation": False,
                "detail": "Pipeline preview does not call Bitrix24, bank, accounting, Telegram, email, or any provider API.",
            },
            {
                "name": "no_persistence",
                "status": "preview_only",
                "detail": "Pipeline preview does not create observations, exceptions, repair actions, outbox jobs, or notifications.",
            },
            {
                "name": "secret_and_pii_boundary",
                "status": "clean",
                "raw_payload_included": False,
                "pii_included": False,
                "requires_secret": False,
                "detail": "Unsafe keys are dropped and raw payloads are not returned.",
            },
        ],
        "evidence": [
            {
                "type": "pipeline",
                "event": "business_intake_pipeline.previewed",
                "source_system_count": len(source_systems),
                "intake_count": len(intake_previews),
                "detected_exception_count": len(detected_exceptions),
                "repair_candidate_count": len(suggested_repairs),
            },
            *[
                {
                    "type": "provider_intake",
                    "event": "business_provider_intake.previewed",
                    "provider_key": str(preview.get("provider_key")),
                    "dropped_key_count": len(list(preview.get("dropped_keys") or [])),
                }
                for preview in intake_previews
            ],
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-intake-pipeline/preview",
            "provider_intake": "POST /tenants/{tenant_id}/business-provider-intake/preview",
            "workbench_context": "POST /tenants/{tenant_id}/business-workbench-context/preview",
            "detections": "POST /tenants/{tenant_id}/business-detections/preview",
            "action_plan": "POST /tenants/{tenant_id}/business-action-plans/preview",
            "notifications": "POST /tenants/{tenant_id}/business-notifications/preview",
        },
    }


def _task_handoff_steps(payload: BusinessTaskHandoffPreviewCreate) -> list[dict[str, object]]:
    if payload.action_plan_steps:
        source_steps = payload.action_plan_steps
    else:
        source_steps = [
            {
                "step": "review_detected_exceptions",
                "status": "action_required",
                "requiresApproval": False,
                "externalMutation": False,
                "evidence": "business_detection.previewed",
            },
            {
                "step": "execute_repair_dry_run",
                "status": "approval_required",
                "requiresApproval": True,
                "externalMutation": False,
                "evidence": "repair_action.approved",
            },
        ]

    safe_steps: list[dict[str, object]] = []
    for index, item in enumerate(source_steps, start=1):
        if not isinstance(item, dict):
            continue
        action = str(
            item.get("step")
            or item.get("action")
            or item.get("name")
            or f"operator_step_{index}"
        )
        safe_steps.append(
            {
                "action": action[:96],
                "status": str(item.get("status") or "ready")[:32],
                "requires_approval": bool(
                    item.get("requires_approval")
                    or item.get("requiresApproval")
                    or item.get("approvalRequired")
                ),
                "external_mutation": bool(
                    item.get("external_mutation")
                    or item.get("externalMutation")
                    or item.get("externalWrite")
                ),
                "evidence": str(item.get("evidence") or "business_action_plan.previewed")[:128],
            }
        )
    return safe_steps


async def preview_business_task_handoff(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessTaskHandoffPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    steps = _task_handoff_steps(payload)
    subject_type = payload.subject_type or "deal"
    subject_id = payload.subject_id or "DEAL-2026-001"
    subject = _subject_label(subject_type, subject_id)

    task_cards = [
        {
            "task_key": f"task.preview.{index:03d}",
            "title": step["action"],
            "assignee_role": payload.role,
            "status": "would_create",
            "priority": "high" if step["requires_approval"] else "normal",
            "source_action": step["action"],
            "subject": subject,
            "due": "same_day" if step["requires_approval"] else "next_business_day",
            "would_create": "BusinessRecord(type=task)",
            "requires_approval": bool(step["requires_approval"]),
            "external_mutation": False,
            "contains_pii": False,
            "raw_payload_included": False,
            "evidence": "business_task_handoff.previewed",
        }
        for index, step in enumerate(steps, start=1)
    ]

    outbox_candidates = [
        {
            "event_type": "task.created",
            "adapter_key": "internal.noop",
            "status": "would_enqueue",
            "idempotency_key": f"business-task-handoff:{subject}:task-{index:03d}",
            "payload_profile": "safe_task_reference",
            "source_action": card["source_action"],
            "contains_pii": False,
            "external_mutation": False,
            "evidence": "business_task_handoff.previewed",
        }
        for index, card in enumerate(task_cards, start=1)
    ] if payload.include_internal_outbox else []

    notification_drafts = [
        {
            "draft_id": f"task_handoff.in_app.{payload.role}.{index:03d}",
            "channel": "in_app",
            "recipient_role": payload.role,
            "title": "Task handoff ready",
            "body": f"{subject} has internal task preview: {card['source_action']}.",
            "status": "draft_only",
            "external_delivery": False,
            "contains_pii": False,
            "requires_secret": False,
            "evidence": "business_task_handoff.previewed",
        }
        for index, card in enumerate(task_cards, start=1)
    ] if payload.include_notification_drafts else []

    approval_gates = [
        {
            "gate": "task_creation_review",
            "status": "required",
            "requires_approval": False,
            "external_mutation": False,
            "detail": "Preview shows internal task records before persistence.",
        },
        {
            "gate": "external_write_gate",
            "status": "closed",
            "requires_approval": True,
            "external_mutation": False,
            "detail": "No external provider write is available from this public preview.",
        },
    ]
    if any(bool(step["requires_approval"]) for step in steps):
        approval_gates.append(
            {
                "gate": "repair_action_approval",
                "status": "required",
                "requires_approval": True,
                "external_mutation": False,
                "detail": "Repair-like actions remain approval-gated before execution.",
            }
        )

    return {
        "tenant_id": tenant_id,
        "handoff_kind": payload.handoff_kind,
        "role": payload.role,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "generated_at": datetime.now(UTC),
        "status": "previewed",
        "summary": (
            f"Task handoff preview prepared {len(task_cards)} internal task card(s), "
            f"{len(outbox_candidates)} internal outbox candidate(s), and "
            f"{len(notification_drafts)} notification draft(s) for {payload.role}."
        ),
        "task_cards": task_cards,
        "outbox_candidates": outbox_candidates,
        "notification_drafts": notification_drafts,
        "approval_gates": approval_gates,
        "data_boundaries": [
            {
                "name": "preview_only_no_persistence",
                "status": "preview_only",
                "external_mutation": False,
                "detail": "The handoff preview does not create task records, outbox rows, or notifications.",
            },
            {
                "name": "internal_only_outbox",
                "status": "clean",
                "adapter_key": "internal.noop",
                "external_mutation": False,
                "detail": "Outbox candidates are internal event contracts, not provider calls.",
            },
            {
                "name": "safe_task_payload",
                "status": "clean",
                "raw_payload_included": False,
                "pii_included": False,
                "contains_pii": False,
                "detail": "Task cards contain role, subject key, source action, and evidence labels only.",
            },
        ],
        "evidence": [
            {
                "type": "task_handoff",
                "event": "business_task_handoff.previewed",
                "task_count": len(task_cards),
                "outbox_candidate_count": len(outbox_candidates),
                "notification_draft_count": len(notification_drafts),
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
            "action_plan": "POST /tenants/{tenant_id}/business-action-plans/preview",
            "workflow_rules": "POST /tenants/{tenant_id}/workflow-rules",
            "task_records": "POST /tenants/{tenant_id}/business-records",
        },
    }


def _action_execution_steps(payload: BusinessActionExecutionPreviewCreate) -> list[dict[str, object]]:
    if payload.action_steps:
        source_steps = payload.action_steps
    else:
        source_steps = [
            {
                "action": "open_reconciliation_plan",
                "status": "ready",
                "adapter_key": "internal.noop",
                "would_enqueue_event": "business.action.review_requested",
                "requiresApproval": False,
                "commitWouldMutateProvider": False,
                "evidence": "business_action_plan.previewed",
            },
            {
                "action": "queue_accounting_export_after_review",
                "status": "approval_required",
                "adapter_key": "accounting.export.mock",
                "would_enqueue_event": "accounting.export.requested",
                "requiresApproval": True,
                "commitWouldMutateProvider": True,
                "evidence": "accounting.export.requested",
            },
            {
                "action": "prepare_internal_notification",
                "status": "draft_only",
                "adapter_key": "internal.notification",
                "would_enqueue_event": "notification.delivery.requested",
                "requiresApproval": False,
                "commitWouldMutateProvider": False,
                "evidence": "business_notification_channel_matrix.previewed",
            },
        ]

    safe_steps: list[dict[str, object]] = []
    for index, item in enumerate(source_steps, start=1):
        if not isinstance(item, dict):
            continue
        action = str(item.get("action") or item.get("step") or item.get("name") or f"execution_step_{index}")
        adapter_key = str(item.get("adapter_key") or item.get("adapterKey") or "internal.noop")
        would_enqueue_event = str(
            item.get("would_enqueue_event")
            or item.get("wouldEnqueueEvent")
            or item.get("event_type")
            or item.get("eventType")
            or "business.action.execution_requested"
        )
        requires_approval = bool(
            item.get("requires_approval")
            or item.get("requiresApproval")
            or item.get("approvalRequired")
        )
        commit_would_mutate_provider = bool(
            item.get("commit_would_mutate_provider")
            or item.get("commitWouldMutateProvider")
            or item.get("externalMutationOnCommit")
        )
        safe_steps.append(
            {
                "action": action[:96],
                "status": str(item.get("status") or "ready")[:32],
                "adapter_key": adapter_key[:128],
                "would_enqueue_event": would_enqueue_event[:128],
                "requires_approval": requires_approval,
                "commit_would_mutate_provider": commit_would_mutate_provider,
                "evidence": str(item.get("evidence") or "business_action_execution.previewed")[:128],
            }
        )
    return safe_steps


async def preview_business_action_execution(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessActionExecutionPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    steps = _action_execution_steps(payload)
    subject_type = payload.subject_type or "deal"
    subject_id = payload.subject_id or "DEAL-2026-001"
    subject = _subject_label(subject_type, subject_id)

    execution_plan = [
        {
            "execution_key": f"execution.preview.{index:03d}",
            "action": step["action"],
            "status": "approval_required" if step["requires_approval"] else "dry_run_ready",
            "mode": payload.execution_mode,
            "adapter_key": step["adapter_key"],
            "would_enqueue_event": step["would_enqueue_event"],
            "idempotency_key": f"business-action-execution:{subject}:{step['action']}:{index:03d}",
            "safe_payload_profile": "role_subject_action_reference",
            "dry_run": True,
            "safe_to_auto_run": bool(not step["requires_approval"] and not step["commit_would_mutate_provider"]),
            "requires_approval": bool(step["requires_approval"]),
            "commit_would_mutate_provider": bool(step["commit_would_mutate_provider"]),
            "external_mutation": False,
            "contains_pii": False,
            "raw_payload_included": False,
            "evidence": "business_action_execution.previewed",
        }
        for index, step in enumerate(steps, start=1)
    ]

    preflight_checks = [
        {
            "check": "safe_payload_profile",
            "status": "passed",
            "detail": "Execution preview contains role, subject key, action key, and evidence references only.",
            "external_mutation": False,
            "evidence": "business_action_execution.previewed",
        },
        {
            "check": "idempotency_key_ready",
            "status": "passed",
            "detail": "Each execution candidate has a deterministic preview idempotency key.",
            "external_mutation": False,
            "evidence": "business_action_execution.previewed",
        },
        {
            "check": "approval_gate_attached",
            "status": "required" if any(item["requires_approval"] for item in execution_plan) else "passed",
            "detail": "Provider-changing commits stay behind explicit operator approval.",
            "external_mutation": False,
            "evidence": "business_action_execution.previewed",
        },
        {
            "check": "connector_secret_boundary",
            "status": "clean",
            "detail": "Preview does not require provider credentials or browser token storage.",
            "external_mutation": False,
            "requires_secret": False,
            "browser_token_storage": False,
            "evidence": "business_action_execution.previewed",
        },
    ] if payload.include_preflight else []

    dry_run_results = [
        {
            "result_key": f"dry_run.{index:03d}",
            "action": item["action"],
            "status": "would_enqueue" if item["mode"] == "dry_run" else "would_request_approval",
            "would_record": "WorkflowActionRun",
            "would_enqueue_event": item["would_enqueue_event"],
            "adapter_key": item["adapter_key"],
            "external_mutation": False,
            "contains_pii": False,
            "raw_payload_included": False,
            "evidence": "business_action_execution.previewed",
        }
        for index, item in enumerate(execution_plan, start=1)
    ]

    rollback_plan = [
        {
            "step": "preview_has_no_rollback",
            "status": "not_needed",
            "detail": "Dry-run preview writes nothing, so there is no external state to roll back.",
            "external_mutation": False,
        },
        {
            "step": "commit_uses_outbox_recovery",
            "status": "documented",
            "detail": "A future commit path should use outbox retry, dead-letter review, and audit evidence.",
            "external_mutation": False,
        },
    ] if payload.include_rollback_plan else []

    return {
        "tenant_id": tenant_id,
        "execution_kind": payload.execution_kind,
        "role": payload.role,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "generated_at": datetime.now(UTC),
        "status": "previewed",
        "summary": (
            f"Execution preview prepared {len(execution_plan)} dry-run candidate(s), "
            f"{len(preflight_checks)} preflight check(s), and {len(rollback_plan)} rollback note(s) for {payload.role}."
        ),
        "execution_plan": execution_plan,
        "preflight_checks": preflight_checks,
        "dry_run_results": dry_run_results,
        "approval_gates": [
            {
                "gate": "operator_review_gate",
                "status": "required",
                "requires_approval": True,
                "external_mutation": False,
                "detail": "The operator sees the full execution plan before commit.",
            },
            {
                "gate": "external_write_gate",
                "status": "closed",
                "requires_approval": True,
                "external_mutation": False,
                "detail": "Public preview never sends provider writes.",
            },
            {
                "gate": "idempotent_outbox_gate",
                "status": "ready",
                "requires_approval": False,
                "external_mutation": False,
                "detail": "Commit candidates carry idempotency keys before queueing.",
            },
        ],
        "rollback_plan": rollback_plan,
        "data_boundaries": [
            {
                "name": "dry_run_only",
                "status": "preview_only",
                "external_mutation": False,
                "detail": "The preview computes the execution plan but does not persist it.",
            },
            {
                "name": "no_provider_write",
                "status": "closed",
                "external_mutation": False,
                "detail": "No CRM, bank, accounting, notification, or webhook provider is mutated.",
            },
            {
                "name": "safe_execution_payload",
                "status": "clean",
                "contains_pii": False,
                "raw_payload_included": False,
                "detail": "Payloads use subject references and action keys only.",
            },
            {
                "name": "audit_and_outbox_contract",
                "status": "documented",
                "external_mutation": False,
                "detail": "A future commit path must record audit and outbox evidence before provider execution.",
            },
        ],
        "evidence": [
            {
                "type": "action_execution",
                "event": "business_action_execution.previewed",
                "execution_count": len(execution_plan),
                "dry_run": True,
                "external_mutation": False,
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-action-executions/preview",
            "action_plan": "POST /tenants/{tenant_id}/business-action-plans/preview",
            "task_handoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
            "repair_execute": "POST /tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
            "outbox": "GET /tenants/{tenant_id}/outbox",
        },
    }


def _approval_gateway_execution_plan(
    payload: BusinessApprovalGatewayPreviewCreate,
) -> list[dict[str, object]]:
    if payload.execution_plan:
        source_items = payload.execution_plan
    else:
        source_items = [
            {
                "action": "open_reconciliation_plan",
                "status": "dry_run_ready",
                "adapter_key": "internal.noop",
                "requiresApproval": False,
                "commitWouldMutateProvider": False,
                "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:open_reconciliation_plan:001",
            },
            {
                "action": "queue_accounting_export_after_review",
                "status": "approval_required",
                "adapter_key": "accounting.export.mock",
                "requiresApproval": True,
                "commitWouldMutateProvider": True,
                "idempotencyKey": (
                    "business-action-execution:deal:DEAL-2026-001:"
                    "queue_accounting_export_after_review:002"
                ),
            },
            {
                "action": "prepare_internal_notification",
                "status": "dry_run_ready",
                "adapter_key": "internal.notification",
                "requiresApproval": False,
                "commitWouldMutateProvider": False,
                "idempotencyKey": "business-action-execution:deal:DEAL-2026-001:prepare_internal_notification:003",
            },
        ]

    plan: list[dict[str, object]] = []
    for index, item in enumerate(source_items, start=1):
        if not isinstance(item, dict):
            continue
        action = str(item.get("action") or item.get("step") or item.get("name") or f"approval_step_{index}")
        adapter_key = str(item.get("adapter_key") or item.get("adapterKey") or "internal.noop")
        requires_approval = bool(
            item.get("requires_approval")
            or item.get("requiresApproval")
            or item.get("approvalRequired")
            or item.get("commitWouldMutateProvider")
            or item.get("commit_would_mutate_provider")
        )
        commit_would_mutate_provider = bool(
            item.get("commit_would_mutate_provider")
            or item.get("commitWouldMutateProvider")
            or item.get("externalMutationOnCommit")
        )
        idempotency_key = str(
            item.get("idempotency_key")
            or item.get("idempotencyKey")
            or f"business-approval-gateway:{action}:{index:03d}"
        )
        plan.append(
            {
                "action": action[:96],
                "status": str(item.get("status") or "approval_required")[:32],
                "adapter_key": adapter_key[:128],
                "requires_approval": requires_approval,
                "commit_would_mutate_provider": commit_would_mutate_provider,
                "idempotency_key": idempotency_key[:256],
            }
        )
    return plan


async def preview_business_approval_gateway(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessApprovalGatewayPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    subject_type = payload.subject_type or "deal"
    subject_id = payload.subject_id or "DEAL-2026-001"
    subject = _subject_label(subject_type, subject_id)
    execution_plan = _approval_gateway_execution_plan(payload)
    approval_candidates = [
        item for item in execution_plan if item["requires_approval"] or item["commit_would_mutate_provider"]
    ]

    approval_requests = [
        {
            "approval_key": f"approval.preview.{index:03d}",
            "action": item["action"],
            "status": "approval_required",
            "requester_role": payload.requester_role,
            "approver_role": payload.approver_role,
            "subject": subject,
            "idempotency_key": f"business-approval-gateway:{subject}:{item['action']}:{index:03d}",
            "source_idempotency_key": item["idempotency_key"],
            "requires_dual_control": bool(payload.include_dual_control),
            "commit_would_mutate_provider": bool(item["commit_would_mutate_provider"]),
            "external_mutation": False,
            "contains_pii": False,
            "raw_payload_included": False,
            "evidence": "business_approval_gateway.previewed",
        }
        for index, item in enumerate(approval_candidates, start=1)
    ]

    if not approval_requests:
        approval_requests = [
            {
                "approval_key": "approval.preview.001",
                "action": "no_provider_commit_required",
                "status": "not_required",
                "requester_role": payload.requester_role,
                "approver_role": payload.approver_role,
                "subject": subject,
                "idempotency_key": f"business-approval-gateway:{subject}:no_provider_commit_required:001",
                "source_idempotency_key": "none",
                "requires_dual_control": bool(payload.include_dual_control),
                "commit_would_mutate_provider": False,
                "external_mutation": False,
                "contains_pii": False,
                "raw_payload_included": False,
                "evidence": "business_approval_gateway.previewed",
            }
        ]

    policy_checks = [
        {
            "check": "rbac_approver_role",
            "status": "passed",
            "detail": "Approval is routed to a role that can approve provider-changing commits.",
            "external_mutation": False,
            "evidence": "business_approval_gateway.previewed",
        },
        {
            "check": "dual_control_required",
            "status": "required" if payload.include_dual_control else "not_required",
            "detail": "Requester and approver roles are separated before commit unlock.",
            "external_mutation": False,
            "evidence": "business_approval_gateway.previewed",
        },
        {
            "check": "idempotency_preserved",
            "status": "passed",
            "detail": "Approval requests carry both approval and source execution idempotency keys.",
            "external_mutation": False,
            "evidence": "business_approval_gateway.previewed",
        },
        {
            "check": "provider_write_closed_until_approval",
            "status": "closed",
            "detail": "No provider write is unlocked before an approval record exists.",
            "external_mutation": False,
            "evidence": "business_approval_gateway.previewed",
        },
    ]

    approver_routing = [
        {
            "route": "owner_or_accountant_review",
            "status": "ready",
            "queue": "approval.review",
            "owner_role": payload.approver_role,
            "sla_minutes": 120,
            "notification_channel": "in_app",
            "external_delivery": False,
            "evidence": "business_approval_gateway.previewed",
        },
        {
            "route": "escalate_if_sla_missed",
            "status": "armed",
            "queue": "approval.escalation",
            "owner_role": "owner",
            "sla_minutes": 240,
            "notification_channel": "in_app",
            "external_delivery": False,
            "evidence": "business_approval_gateway.previewed",
        },
    ]

    commit_unlocks = [
        {
            "unlock_key": f"commit.unlock.{index:03d}",
            "action": item["action"],
            "status": "blocked_until_approved",
            "would_record": "WorkflowActionRun",
            "would_enqueue_event": "business.action.approval_granted",
            "outbox_ready": True,
            "provider_write_unlocked": False,
            "external_mutation": False,
            "rollback_attached": True,
            "evidence": "business_approval_gateway.previewed",
        }
        for index, item in enumerate(approval_requests, start=1)
    ]

    audit_trail = [
        {
            "event": "business_approval.requested",
            "status": "would_record",
            "actor_role": payload.requester_role,
            "subject": subject,
            "external_mutation": False,
            "evidence": "business_approval_gateway.previewed",
        },
        {
            "event": "business_approval.policy_checked",
            "status": "would_record",
            "actor_role": "system",
            "subject": subject,
            "external_mutation": False,
            "evidence": "business_approval_gateway.previewed",
        },
        {
            "event": "business_approval.commit_unlocked",
            "status": "blocked_until_approved",
            "actor_role": payload.approver_role,
            "subject": subject,
            "external_mutation": False,
            "evidence": "business_approval_gateway.previewed",
        },
    ]

    return {
        "tenant_id": tenant_id,
        "approval_kind": payload.approval_kind,
        "role": payload.role,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "generated_at": datetime.now(UTC),
        "status": "previewed",
        "summary": (
            f"Approval gateway prepared {len(approval_requests)} request(s), "
            f"{len(policy_checks)} policy check(s), and {len(commit_unlocks)} commit unlock candidate(s) for {payload.role}."
        ),
        "approval_requests": approval_requests,
        "policy_checks": policy_checks,
        "approver_routing": approver_routing,
        "commit_unlocks": commit_unlocks,
        "audit_trail": audit_trail,
        "data_boundaries": [
            {
                "name": "preview_only_no_approval_record",
                "status": "preview_only",
                "external_mutation": False,
                "detail": "The public preview computes approval routing without persisting approval rows.",
            },
            {
                "name": "provider_write_locked",
                "status": "closed",
                "external_mutation": False,
                "detail": "Provider-changing commits remain locked until approval is recorded.",
            },
            {
                "name": "rbac_dual_control",
                "status": "enforced",
                "external_mutation": False,
                "detail": "Requester and approver roles are separated for high-impact commits.",
            },
            {
                "name": "safe_approval_payload",
                "status": "clean",
                "contains_pii": False,
                "raw_payload_included": False,
                "detail": "Approval payload contains role, subject, action, idempotency, and evidence references only.",
            },
        ],
        "evidence": [
            {
                "type": "approval_gateway",
                "event": "business_approval_gateway.previewed",
                "approval_count": len(approval_requests),
                "provider_write_unlocked": False,
                "external_mutation": False,
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-approval-gateway/preview",
            "action_execution": "POST /tenants/{tenant_id}/business-action-executions/preview",
            "task_handoff": "POST /tenants/{tenant_id}/business-task-handoffs/preview",
            "outbox": "GET /tenants/{tenant_id}/outbox",
        },
    }


def _workbench_context_card(observation: BusinessStateObservation) -> dict[str, object]:
    family = _observation_family(observation.system_key)
    payload = _json_dict(observation.payload_json)
    safe_facts = [
        {"key": key, "value": str(payload[key])}
        for key in sorted(SAFE_CONTEXT_FACT_KEYS)
        if key in payload
    ]
    title_by_family = {
        "crm": "CRM deal context",
        "bank": "Payment evidence",
        "accounting": "Accounting export context",
    }
    state_status = "available"
    if family == "bank" and observation.state in BANK_PAID_STATES:
        state_status = "confirmed"
    elif family == "accounting" and observation.state in ACCOUNTING_NOT_EXPORTED_STATES:
        state_status = "action_required"
    elif family == "crm" and observation.state in CRM_WAITING_PAYMENT_STATES:
        state_status = "needs_cross_check"

    return {
        "card_id": f"{family}.{observation.subject_type}.{observation.subject_id}.{observation.state}",
        "title": title_by_family.get(family, "External system context"),
        "system_key": observation.system_key,
        "system_family": family,
        "subject": _subject_label(observation.subject_type, observation.subject_id),
        "state": observation.state,
        "status": state_status,
        "safe_facts": safe_facts,
        "payload_keys": sorted(payload.keys()),
        "raw_payload_included": False,
        "pii_included": False,
        "external_fetch": False,
        "external_mutation": False,
        "observed_at": observation.observed_at.isoformat(),
        "evidence": "business_workbench_context.previewed",
    }


def _workbench_context_suggested_actions(
    *,
    tenant_id: str,
    cards: list[dict[str, object]],
    exceptions: list[BusinessException],
    repairs: list[RepairAction],
) -> list[dict[str, object]]:
    statuses_by_family = {
        str(card["system_family"]): str(card["status"])
        for card in cards
    }
    actions: list[dict[str, object]] = []
    if statuses_by_family.get("bank") == "confirmed" and statuses_by_family.get("crm") == "needs_cross_check":
        actions.append(
            {
                "action": "reconcile_crm_payment_status",
                "status": "available",
                "summary": "Compare the paid bank state with the CRM deal state before any external write.",
                "endpoint": "POST /tenants/{tenant_id}/business-detections/preview",
                "external_mutation": False,
                "requires_approval": False,
                "evidence": "business_workbench_context.previewed",
            }
        )
    if statuses_by_family.get("accounting") == "action_required":
        actions.append(
            {
                "action": "review_accounting_export",
                "status": "available",
                "summary": "Open the accounting export evidence and decide whether a dry-run repair is needed.",
                "endpoint": "GET /tenants/{tenant_id}/business-state/observations",
                "external_mutation": False,
                "requires_approval": False,
                "evidence": "business_workbench_context.previewed",
            }
        )
    if exceptions or repairs:
        actions.append(
            {
                "action": "open_action_plan_preview",
                "status": "ready" if repairs else "available",
                "summary": "Turn the current context into ordered operator work inside DriveDesk.",
                "endpoint": "POST /tenants/{tenant_id}/business-action-plans/preview",
                "external_mutation": False,
                "requires_approval": False,
                "evidence": "business_action_plan.previewed",
            }
        )
    return actions


async def preview_business_workbench_context(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessWorkbenchContextPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    observations_query = (
        select(BusinessStateObservation)
        .where(BusinessStateObservation.tenant_id == tenant_id)
        .order_by(BusinessStateObservation.observed_at.desc(), BusinessStateObservation.created_at.desc())
        .limit(payload.limit)
    )
    exceptions_query = (
        select(BusinessException)
        .where(BusinessException.tenant_id == tenant_id)
        .order_by(BusinessException.detected_at.desc(), BusinessException.created_at.desc())
        .limit(payload.limit)
    )
    if payload.subject_type:
        observations_query = observations_query.where(BusinessStateObservation.subject_type == payload.subject_type)
        exceptions_query = exceptions_query.where(BusinessException.subject_type == payload.subject_type)
    if payload.subject_id:
        observations_query = observations_query.where(BusinessStateObservation.subject_id == payload.subject_id)
        exceptions_query = exceptions_query.where(BusinessException.subject_id == payload.subject_id)
    if payload.source_systems:
        observations_query = observations_query.where(BusinessStateObservation.system_key.in_(payload.source_systems))
    if not payload.include_resolved:
        exceptions_query = exceptions_query.where(BusinessException.status != "resolved")

    observations_result = await session.execute(observations_query)
    exceptions_result = await session.execute(exceptions_query)
    observations = list(observations_result.scalars().all())
    exceptions = list(exceptions_result.scalars().all())
    exception_ids = [item.id for item in exceptions]
    repairs: list[RepairAction] = []
    if exception_ids:
        repairs_result = await session.execute(
            select(RepairAction)
            .where(
                RepairAction.tenant_id == tenant_id,
                RepairAction.business_exception_id.in_(exception_ids),
            )
            .order_by(RepairAction.created_at.desc())
            .limit(payload.limit)
        )
        repairs = list(repairs_result.scalars().all())

    cards = [_workbench_context_card(observation) for observation in observations]
    source_systems = sorted({str(card["system_key"]) for card in cards})
    suggested_actions = _workbench_context_suggested_actions(
        tenant_id=tenant_id,
        cards=cards,
        exceptions=exceptions,
        repairs=repairs,
    )
    subject = _subject_label(payload.subject_type, payload.subject_id)
    summary = (
        f"{payload.context_kind} context for {payload.role}: {len(cards)} card(s), "
        f"{len(source_systems)} source system(s), {len(suggested_actions)} suggested action(s) for {subject}."
    )
    return {
        "tenant_id": tenant_id,
        "context_kind": payload.context_kind,
        "role": payload.role,
        "subject_type": payload.subject_type,
        "subject_id": payload.subject_id,
        "generated_at": datetime.now(UTC),
        "risk_level": _briefing_risk_level(exceptions, repairs),
        "summary": summary,
        "source_systems": source_systems,
        "context_cards": cards,
        "suggested_actions": suggested_actions,
        "data_boundaries": [
            {
                "name": "read_only_source_context",
                "status": "preview_only",
                "external_fetch": False,
                "external_mutation": False,
                "detail": "The preview uses already-normalized DriveDesk observations and does not call provider APIs.",
            },
            {
                "name": "pii_redaction",
                "status": "clean" if all(card["pii_included"] is False for card in cards) else "review_required",
                "raw_payload_included": False,
                "detail": "Cards expose system, state, subject key, safe facts, and payload keys, not raw provider payloads.",
            },
            {
                "name": "secret_boundary",
                "status": "clean",
                "requires_secret": False,
                "detail": "No Bitrix, bank, accounting, Telegram, or email credentials are required for preview.",
            },
        ],
        "review_points": [
            {
                "name": "single_work_surface",
                "status": "ready" if cards else "empty",
                "detail": "External facts are rendered next to the operator workflow inside DriveDesk.",
            },
            {
                "name": "source_coverage",
                "status": "ready" if len(source_systems) >= 2 else "partial",
                "detail": "Context quality improves as CRM, bank, accounting, and support observations converge.",
            },
            {
                "name": "next_action_boundary",
                "status": "preview_only",
                "detail": "Suggested actions link to DriveDesk previews and approval-gated flows only.",
            },
        ],
        "evidence": [
            {
                "type": "observation",
                "id": observation.id,
                "system": observation.system_key,
                "state": observation.state,
                "event": "business_state.observation.recorded",
            }
            for observation in observations[:5]
        ]
        + [
            {
                "type": "business_exception",
                "id": business_exception.id,
                "severity": business_exception.severity,
                "status": business_exception.status,
                "event": "business_exception.created",
            }
            for business_exception in exceptions[:5]
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-workbench-context/preview",
            "observations": "GET /tenants/{tenant_id}/business-state/observations",
            "detections": "POST /tenants/{tenant_id}/business-detections/preview",
            "action_plan": "POST /tenants/{tenant_id}/business-action-plans/preview",
            "briefing": "POST /tenants/{tenant_id}/business-briefings/preview",
        },
    }


async def preview_business_escalations(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessEscalationPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    exceptions_query = (
        select(BusinessException)
        .where(BusinessException.tenant_id == tenant_id)
        .order_by(BusinessException.detected_at.desc(), BusinessException.created_at.desc())
        .limit(payload.limit)
    )
    if payload.subject_type:
        exceptions_query = exceptions_query.where(BusinessException.subject_type == payload.subject_type)
    if payload.subject_id:
        exceptions_query = exceptions_query.where(BusinessException.subject_id == payload.subject_id)
    if not payload.include_resolved:
        exceptions_query = exceptions_query.where(BusinessException.status != "resolved")

    exceptions_result = await session.execute(exceptions_query)
    exceptions = list(exceptions_result.scalars().all())
    exception_ids = [item.id for item in exceptions]
    repairs: list[RepairAction] = []
    if exception_ids:
        repairs_result = await session.execute(
            select(RepairAction)
            .where(
                RepairAction.tenant_id == tenant_id,
                RepairAction.business_exception_id.in_(exception_ids),
            )
            .order_by(RepairAction.created_at.desc())
        )
        repairs = list(repairs_result.scalars().all())

    repairs_by_exception = _latest_repair_by_exception(repairs)
    escalation_items: list[dict[str, object]] = []
    suggested_actions: list[dict[str, object]] = []
    evidence: list[dict[str, object]] = []
    queue_state: dict[str, dict[str, object]] = {}

    for business_exception in exceptions:
        owner_role = _escalation_owner_role(business_exception)
        queue = _escalation_queue(owner_role)
        sla_minutes = _escalation_sla_minutes(business_exception.severity)
        repair = repairs_by_exception.get(business_exception.id)
        next_action = _repair_next_action(
            tenant_id=tenant_id,
            business_exception=business_exception,
            repair=repair,
        )
        escalation_level = "L3" if business_exception.severity == "critical" else "L2"
        item = {
            "business_exception_id": business_exception.id,
            "exception_type": business_exception.exception_type,
            "severity": business_exception.severity,
            "status": business_exception.status,
            "subject_type": business_exception.subject_type,
            "subject_id": business_exception.subject_id,
            "subject": _subject_label(business_exception.subject_type, business_exception.subject_id),
            "owner_role": owner_role,
            "queue": queue,
            "escalation_level": escalation_level,
            "sla_minutes": sla_minutes,
            "next_action": next_action["action"],
            "next_action_status": next_action["status"],
            "repair_action_id": next_action.get("repair_action_id"),
            "external_mutation": False,
            "evidence": "business_escalation.previewed",
        }
        escalation_items.append(item)
        suggested_actions.append(next_action)
        evidence.append(
            {
                "type": "business_exception",
                "id": business_exception.id,
                "event": "business_exception.created",
                "severity": business_exception.severity,
                "status": business_exception.status,
            }
        )
        if repair is not None:
            evidence.append(
                {
                    "type": "repair_action",
                    "id": repair.id,
                    "event": "repair_action.proposed",
                    "action": repair.action_type,
                    "status": repair.status,
                }
            )

        state = queue_state.setdefault(
            queue,
            {
                "queue": queue,
                "owner_role": owner_role,
                "open_items": 0,
                "highest_severity": "info",
                "min_sla_minutes": sla_minutes,
                "status": "active",
            },
        )
        state["open_items"] = int(state["open_items"]) + 1
        if SEVERITY_RANK[business_exception.severity] > SEVERITY_RANK[str(state["highest_severity"])]:
            state["highest_severity"] = business_exception.severity
        state["min_sla_minutes"] = min(int(state["min_sla_minutes"]), sla_minutes)

    queues = sorted(
        queue_state.values(),
        key=lambda item: (-SEVERITY_RANK[str(item["highest_severity"])], int(item["min_sla_minutes"]), str(item["queue"])),
    )
    risk_level = _briefing_risk_level(exceptions, repairs)
    summary = (
        f"{payload.policy} policy routed {len(escalation_items)} open exception(s) "
        f"across {len(queues)} queue(s) with {len(suggested_actions)} next action(s)."
    )
    return {
        "tenant_id": tenant_id,
        "policy": payload.policy,
        "subject_type": payload.subject_type,
        "subject_id": payload.subject_id,
        "generated_at": datetime.now(UTC),
        "risk_level": risk_level,
        "summary": summary,
        "queues": queues,
        "escalation_items": escalation_items,
        "suggested_actions": suggested_actions,
        "review_points": [
            {
                "name": "write_boundary",
                "status": "preview_only",
                "detail": "Escalation preview does not create tasks, approve repairs, or mutate external systems.",
            },
            {
                "name": "owner_routing",
                "status": "ready" if escalation_items else "empty",
                "detail": "Business exception type and severity are mapped to owner role, queue, and SLA.",
            },
            {
                "name": "repair_handoff",
                "status": "ready" if suggested_actions else "not_requested",
                "detail": "Next actions reuse existing approval-gated repair endpoints.",
            },
        ],
        "evidence": evidence,
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-escalations/preview",
            "briefing": "POST /tenants/{tenant_id}/business-briefings/preview",
            "exceptions": "GET /tenants/{tenant_id}/business-exceptions",
            "repair_actions": "GET /tenants/{tenant_id}/repair-actions",
        },
    }


CRM_WAITING_PAYMENT_STATES = {"invoice_sent", "awaiting_payment", "unpaid"}
BANK_PAID_STATES = {"paid", "settled", "captured"}
ACCOUNTING_NOT_EXPORTED_STATES = {"not_exported", "waiting_for_crm_status", "export_pending"}


def _observation_family(system_key: str) -> str:
    lowered = system_key.lower()
    if "bank" in lowered or "payment" in lowered:
        return "bank"
    if "accounting" in lowered or "1c" in lowered or "export" in lowered:
        return "accounting"
    if "crm" in lowered or "bitrix" in lowered:
        return "crm"
    return "other"


def _observation_snapshot(observation: BusinessStateObservation) -> dict[str, object]:
    payload = _json_dict(observation.payload_json)
    return {
        "observation_id": observation.id,
        "system_key": observation.system_key,
        "system_family": _observation_family(observation.system_key),
        "subject_type": observation.subject_type,
        "subject_id": observation.subject_id,
        "subject": _subject_label(observation.subject_type, observation.subject_id),
        "state": observation.state,
        "observed_at": observation.observed_at.isoformat(),
        "payload_keys": sorted(payload.keys()),
        "evidence": "business_state.observation.recorded",
    }


def _latest_family_states(observations: list[BusinessStateObservation]) -> dict[str, BusinessStateObservation]:
    latest: dict[str, BusinessStateObservation] = {}
    for observation in observations:
        family = _observation_family(observation.system_key)
        if family == "other":
            continue
        previous = latest.get(family)
        if previous is None or observation.observed_at > previous.observed_at:
            latest[family] = observation
    return latest


def _detect_payment_reconciliation_subject(
    *,
    subject_type: str,
    subject_id: str,
    observations: list[BusinessStateObservation],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    family_states = _latest_family_states(observations)
    crm = family_states.get("crm")
    bank = family_states.get("bank")
    accounting = family_states.get("accounting")
    evidence = [
        _observation_snapshot(observation)
        for observation in [crm, bank, accounting]
        if observation is not None
    ]

    detected: list[dict[str, object]] = []
    repairs: list[dict[str, object]] = []
    if (
        crm is not None
        and bank is not None
        and accounting is not None
        and crm.state in CRM_WAITING_PAYMENT_STATES
        and bank.state in BANK_PAID_STATES
        and accounting.state in ACCOUNTING_NOT_EXPORTED_STATES
    ):
        subject = _subject_label(subject_type, subject_id)
        detected.append(
            {
                "exception_type": "crm_payment_mismatch",
                "severity": "warning",
                "status": "detected",
                "subject_type": subject_type,
                "subject_id": subject_id,
                "subject": subject,
                "title": "Payment received but CRM and accounting lag behind",
                "summary": (
                    "Bank evidence shows payment while CRM is still waiting for payment "
                    "and accounting export is not completed."
                ),
                "confidence": "high",
                "impact": {
                    "cash_state": "received",
                    "operational_risk": "manual follow-up required",
                    "accounting_export_state": accounting.state,
                },
                "evidence": evidence,
                "would_create": "BusinessException",
            }
        )
        repairs.append(
            {
                "action_type": "sync_status",
                "safety_level": "medium",
                "requires_approval": True,
                "status": "suggested",
                "subject_type": subject_type,
                "subject_id": subject_id,
                "summary": "Synchronize CRM status from verified bank evidence, then unblock accounting export.",
                "payload": {
                    "target_adapter_key": crm.system_key,
                    "desired_state": "paid",
                    "source_evidence": bank.system_key,
                    "accounting_follow_up": accounting.system_key,
                    "external_mutation": False,
                },
                "would_create": "RepairAction",
            }
        )

    return detected, repairs, evidence


async def preview_business_detections(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: BusinessDetectionPreviewCreate,
) -> dict[str, object]:
    await ensure_tenant_exists(session, tenant_id)
    query = (
        select(BusinessStateObservation)
        .where(BusinessStateObservation.tenant_id == tenant_id)
        .order_by(BusinessStateObservation.observed_at.desc(), BusinessStateObservation.created_at.desc())
        .limit(payload.limit)
    )
    if payload.subject_type:
        query = query.where(BusinessStateObservation.subject_type == payload.subject_type)
    if payload.subject_id:
        query = query.where(BusinessStateObservation.subject_id == payload.subject_id)

    result = await session.execute(query)
    observations = list(result.scalars().all())
    grouped: dict[tuple[str, str], list[BusinessStateObservation]] = {}
    for observation in observations:
        grouped.setdefault((observation.subject_type, observation.subject_id), []).append(observation)

    detected_exceptions: list[dict[str, object]] = []
    suggested_repairs: list[dict[str, object]] = []
    evidence: list[dict[str, object]] = []
    for (subject_type, subject_id), subject_observations in grouped.items():
        detected, repairs, subject_evidence = _detect_payment_reconciliation_subject(
            subject_type=subject_type,
            subject_id=subject_id,
            observations=subject_observations,
        )
        detected_exceptions.extend(detected)
        suggested_repairs.extend(repairs)
        evidence.extend(subject_evidence)

    source_systems = sorted({observation.system_key for observation in observations})
    summary = (
        f"{payload.rule_set} detector reviewed {len(grouped)} subject(s), "
        f"{len(observations)} observation(s), and found {len(detected_exceptions)} exception candidate(s)."
    )
    return {
        "tenant_id": tenant_id,
        "rule_set": payload.rule_set,
        "subject_type": payload.subject_type,
        "subject_id": payload.subject_id,
        "generated_at": datetime.now(UTC),
        "summary": summary,
        "source_systems": source_systems,
        "observations": evidence,
        "detected_exceptions": detected_exceptions,
        "suggested_repair_actions": suggested_repairs,
        "rules": [
            {
                "key": "payment_reconciliation.crm_bank_accounting_mismatch",
                "status": "active",
                "if": [
                    "crm.state in invoice_sent,awaiting_payment,unpaid",
                    "bank.state in paid,settled,captured",
                    "accounting.state in not_exported,waiting_for_crm_status,export_pending",
                ],
                "then": [
                    "detect crm_payment_mismatch",
                    "suggest sync_status repair action",
                    "keep execution approval-gated",
                ],
            }
        ],
        "api": {
            "preview": "POST /tenants/{tenant_id}/business-detections/preview",
            "observations": "POST /tenants/{tenant_id}/business-state/observations",
            "exceptions": "POST /tenants/{tenant_id}/business-exceptions",
            "repair": "POST /tenants/{tenant_id}/business-exceptions/{business_exception_id}/repair-actions",
            "briefing": "POST /tenants/{tenant_id}/business-briefings/preview",
        },
    }


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


async def count_business_state_observations_by_system_state(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            BusinessStateObservation.system_key,
            BusinessStateObservation.state,
            func.count().label("observation_count"),
        ).group_by(BusinessStateObservation.system_key, BusinessStateObservation.state)
    )
    return [
        {
            "system_key": row.system_key,
            "state": row.state,
            "observation_count": int(row.observation_count or 0),
        }
        for row in result.all()
    ]


async def count_business_exceptions_by_type_severity_status(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            BusinessException.exception_type,
            BusinessException.severity,
            BusinessException.status,
            func.count().label("exception_count"),
        ).group_by(BusinessException.exception_type, BusinessException.severity, BusinessException.status)
    )
    return [
        {
            "exception_type": row.exception_type,
            "severity": row.severity,
            "status": row.status,
            "exception_count": int(row.exception_count or 0),
        }
        for row in result.all()
    ]


async def count_repair_actions_by_action_status(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            RepairAction.action_type,
            RepairAction.status,
            func.count().label("repair_action_count"),
        ).group_by(RepairAction.action_type, RepairAction.status)
    )
    return [
        {
            "action_type": row.action_type,
            "status": row.status,
            "repair_action_count": int(row.repair_action_count or 0),
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


async def count_integration_reconciliations_by_adapter_status(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            IntegrationReconciliation.adapter_key,
            IntegrationReconciliation.status,
            func.count().label("reconciliation_count"),
        ).group_by(IntegrationReconciliation.adapter_key, IntegrationReconciliation.status)
    )
    return [
        {
            "adapter_key": row.adapter_key,
            "status": row.status,
            "reconciliation_count": int(row.reconciliation_count or 0),
        }
        for row in result.all()
    ]


async def count_integration_incidents_by_adapter_severity_status(session: AsyncSession) -> list[dict[str, object]]:
    result = await session.execute(
        select(
            IntegrationIncident.adapter_key,
            IntegrationIncident.severity,
            IntegrationIncident.status,
            func.count().label("incident_count"),
        ).group_by(IntegrationIncident.adapter_key, IntegrationIncident.severity, IntegrationIncident.status)
    )
    return [
        {
            "adapter_key": row.adapter_key,
            "severity": row.severity,
            "status": row.status,
            "incident_count": int(row.incident_count or 0),
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


def _safe_json_dict(raw_json: str | None) -> dict[str, object]:
    try:
        payload = json.loads(raw_json or "{}")
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _safe_outbox_expected_evidence(event: OutboxEvent) -> dict[str, object]:
    result = _safe_json_dict(event.result_json)
    expected: dict[str, object] = {
        "outbox_status": event.status,
        "event_type": event.event_type,
        "adapter_key": event.adapter_key or "internal.noop",
        "attempts": event.attempts,
        "processed": event.status == "processed",
        "error_present": bool(event.last_error),
    }
    if event.status != "processed":
        return expected

    for key in ("status", "external_ref", "records_received", "records_accepted", "records_rejected"):
        value = result.get(key)
        if isinstance(value, str | int) or value is None:
            expected[key] = value
    return expected


def _safe_provider_evidence(payload: IntegrationReconciliationCreate) -> dict[str, object]:
    actual: dict[str, object] = {
        "provider_status": payload.provider_status,
        "provider_reference": payload.provider_reference,
        "records_received": payload.records_received,
        "records_accepted": payload.records_accepted,
        "records_rejected": payload.records_rejected,
    }
    if payload.note:
        actual["note_present"] = True
    return actual


def _integration_reconciliation_result(
    event: OutboxEvent,
    *,
    actual: dict[str, object],
    expected: dict[str, object],
) -> tuple[str, str, dict[str, object]]:
    if event.status in {"pending", "retry"}:
        return "pending", "Outbox event is not processed yet.", {"outbox_status": event.status}
    if event.status == "dead_letter":
        return "blocked", "Outbox event is dead-lettered; reconciliation is blocked.", {"outbox_status": event.status}
    if event.status != "processed":
        return "pending", "Outbox event has not produced processed evidence.", {"outbox_status": event.status}

    diff: dict[str, object] = {}
    comparisons = {
        "status": (expected.get("status"), actual.get("provider_status")),
        "external_ref": (expected.get("external_ref"), actual.get("provider_reference")),
        "records_received": (expected.get("records_received"), actual.get("records_received")),
        "records_accepted": (expected.get("records_accepted"), actual.get("records_accepted")),
        "records_rejected": (expected.get("records_rejected"), actual.get("records_rejected")),
    }
    for key, (expected_value, actual_value) in comparisons.items():
        if expected_value != actual_value:
            diff[key] = {
                "expected": expected_value,
                "actual": actual_value,
            }

    if diff:
        return "mismatched", "Provider evidence does not match outbox result evidence.", diff
    return "matched", "Provider evidence matches outbox result evidence.", {}


async def create_integration_reconciliation(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: IntegrationReconciliationCreate,
    actor: ActorContext,
) -> IntegrationReconciliation:
    await ensure_tenant_exists(session, tenant_id)
    event = await session.get(OutboxEvent, payload.outbox_event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="outbox event not found")

    adapter_key = event.adapter_key or "internal.noop"
    operation = _adapter_operation_by_event_type(event.adapter_key, event.event_type)
    operation_key = operation.get("key") if operation else None
    expected = _safe_outbox_expected_evidence(event)
    actual = _safe_provider_evidence(payload)
    reconciliation_status, summary, diff = _integration_reconciliation_result(
        event,
        actual=actual,
        expected=expected,
    )
    reconciliation = IntegrationReconciliation(
        id=new_id(),
        tenant_id=tenant_id,
        outbox_event_id=event.id,
        adapter_key=adapter_key,
        operation_key=str(operation_key) if operation_key else None,
        status=reconciliation_status,
        summary=summary,
        expected_json=json.dumps(expected, ensure_ascii=False, sort_keys=True),
        actual_json=json.dumps(actual, ensure_ascii=False, sort_keys=True),
        diff_json=json.dumps(diff, ensure_ascii=False, sort_keys=True),
        created_at=datetime.now(UTC),
    )
    session.add(reconciliation)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="integration.reconciliation.recorded",
        entity_type="integration_reconciliation",
        entity_id=reconciliation.id,
        summary=summary,
        metadata={
            "integration_reconciliation_id": reconciliation.id,
            "outbox_event_id": event.id,
            "adapter_key": adapter_key,
            "operation_key": operation_key,
            "status": reconciliation_status,
            "diff_keys": sorted(diff.keys()),
            "provider_status": payload.provider_status,
            "provider_reference_present": bool(payload.provider_reference),
        },
    )
    await commit_or_conflict(session, "integration reconciliation already exists")
    return reconciliation


async def list_integration_reconciliations(
    session: AsyncSession,
    *,
    tenant_id: str,
    status_filter: str | None = None,
    adapter_key: str | None = None,
    outbox_event_id: str | None = None,
    limit: int = 50,
) -> list[IntegrationReconciliation]:
    await ensure_tenant_exists(session, tenant_id)
    allowed_statuses = {"matched", "mismatched", "pending", "blocked"}
    if status_filter and status_filter not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be matched, mismatched, pending, or blocked",
        )

    query = (
        select(IntegrationReconciliation)
        .where(IntegrationReconciliation.tenant_id == tenant_id)
        .order_by(IntegrationReconciliation.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        query = query.where(IntegrationReconciliation.status == status_filter)
    if adapter_key:
        query = query.where(IntegrationReconciliation.adapter_key == adapter_key)
    if outbox_event_id:
        query = query.where(IntegrationReconciliation.outbox_event_id == outbox_event_id)

    result = await session.execute(query)
    return list(result.scalars().all())


def _incident_safe_payload_summary(payload_summary: dict[str, object]) -> dict[str, object]:
    allowed_keys = {
        "payload_valid",
        "has_integration_connection",
        "source_format",
        "record_count",
        "document_count",
        "document_types",
        "raw_records_redacted",
        "raw_documents_redacted",
        "connection_scopes",
        "mapping_keys",
        "simulate_failure",
    }
    return {key: payload_summary[key] for key in sorted(allowed_keys) if key in payload_summary}


def _primary_runbook_action(runbook: dict[str, object]) -> str:
    actions = runbook.get("recommended_actions")
    if isinstance(actions, list) and actions:
        return " | ".join(str(action) for action in actions)
    return str(runbook.get("summary") or "Review the integration incident.")


def _incident_from_outbox_event(event: OutboxEvent, *, tenant_id: str) -> tuple[dict[str, object], dict[str, object]]:
    runbook = select_integration_runbook("outbox_event", event.status)
    if not runbook:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="outbox event does not require an integration incident runbook",
        )

    operation = _adapter_operation_by_event_type(event.adapter_key, event.event_type)
    _, payload_summary = _safe_outbox_payload_summary(event.payload_json)
    evidence = {
        "source_type": "outbox_event",
        "outbox_event_id": event.id,
        "event_type": event.event_type,
        "outbox_status": event.status,
        "adapter_key": event.adapter_key or "internal.noop",
        "operation_key": operation.get("key") if operation else None,
        "attempts": event.attempts,
        "last_error_present": bool(event.last_error),
        "next_retry_at": event.next_retry_at.isoformat() if event.next_retry_at else None,
        "dead_lettered_at": event.dead_lettered_at.isoformat() if event.dead_lettered_at else None,
        "payload_summary": _incident_safe_payload_summary(payload_summary),
        "retry_endpoint": f"/tenants/{tenant_id}/outbox-events/{event.id}/retry",
    }
    return runbook, evidence


def _incident_from_reconciliation(
    reconciliation: IntegrationReconciliation,
) -> tuple[dict[str, object], dict[str, object]]:
    runbook = select_integration_runbook("reconciliation", reconciliation.status)
    if not runbook:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="reconciliation does not require an integration incident runbook",
        )

    actual = _safe_json_dict(reconciliation.actual_json)
    diff = _safe_json_dict(reconciliation.diff_json)
    evidence = {
        "source_type": "reconciliation",
        "reconciliation_id": reconciliation.id,
        "outbox_event_id": reconciliation.outbox_event_id,
        "reconciliation_status": reconciliation.status,
        "adapter_key": reconciliation.adapter_key,
        "operation_key": reconciliation.operation_key,
        "diff_keys": sorted(diff.keys()),
        "provider_status": actual.get("provider_status"),
        "provider_reference_present": bool(actual.get("provider_reference")),
        "note_present": bool(actual.get("note_present")),
    }
    return runbook, evidence


async def create_integration_incident(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: IntegrationIncidentCreate,
    actor: ActorContext,
) -> IntegrationIncident:
    await ensure_tenant_exists(session, tenant_id)

    if payload.source_type == "outbox_event":
        source = await session.get(OutboxEvent, payload.source_id)
        if not source or source.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="outbox event not found")
        runbook, evidence = _incident_from_outbox_event(source, tenant_id=tenant_id)
        adapter_key = source.adapter_key or "internal.noop"
        operation_key = evidence.get("operation_key")
    else:
        source = await session.get(IntegrationReconciliation, payload.source_id)
        if not source or source.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="reconciliation not found")
        runbook, evidence = _incident_from_reconciliation(source)
        adapter_key = source.adapter_key
        operation_key = source.operation_key

    if payload.note:
        evidence["operator_note_present"] = True

    incident = IntegrationIncident(
        id=new_id(),
        tenant_id=tenant_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        adapter_key=adapter_key,
        operation_key=str(operation_key) if operation_key else None,
        runbook_key=str(runbook["key"]),
        severity=str(runbook["severity"]),
        status="open",
        summary=str(runbook["summary"]),
        recommended_action=_primary_runbook_action(runbook),
        evidence_json=json.dumps(evidence, ensure_ascii=False, sort_keys=True),
        created_at=datetime.now(UTC),
    )
    session.add(incident)
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="integration.incident.created",
        entity_type="integration_incident",
        entity_id=incident.id,
        summary=incident.summary,
        metadata={
            "integration_incident_id": incident.id,
            "source_type": incident.source_type,
            "source_id": incident.source_id,
            "adapter_key": incident.adapter_key,
            "operation_key": incident.operation_key,
            "runbook_key": incident.runbook_key,
            "severity": incident.severity,
            "status": incident.status,
            "operator_note_present": bool(payload.note),
        },
    )
    await commit_or_conflict(session, "integration incident already exists")
    return incident


async def list_integration_incidents(
    session: AsyncSession,
    *,
    tenant_id: str,
    status_filter: str | None = None,
    severity: str | None = None,
    adapter_key: str | None = None,
    source_type: str | None = None,
    limit: int = 50,
) -> list[IntegrationIncident]:
    await ensure_tenant_exists(session, tenant_id)
    allowed_statuses = {"open", "acknowledged", "resolved"}
    if status_filter and status_filter not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be open, acknowledged, or resolved",
        )
    allowed_severities = {"info", "warning", "critical"}
    if severity and severity not in allowed_severities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="severity must be info, warning, or critical",
        )
    allowed_source_types = {"outbox_event", "reconciliation"}
    if source_type and source_type not in allowed_source_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_type must be outbox_event or reconciliation",
        )

    query = (
        select(IntegrationIncident)
        .where(IntegrationIncident.tenant_id == tenant_id)
        .order_by(IntegrationIncident.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        query = query.where(IntegrationIncident.status == status_filter)
    if severity:
        query = query.where(IntegrationIncident.severity == severity)
    if adapter_key:
        query = query.where(IntegrationIncident.adapter_key == adapter_key)
    if source_type:
        query = query.where(IntegrationIncident.source_type == source_type)

    result = await session.execute(query)
    return list(result.scalars().all())


async def change_integration_incident_status(
    session: AsyncSession,
    *,
    tenant_id: str,
    incident_id: str,
    payload: IntegrationIncidentStatusChange,
    actor: ActorContext,
) -> IntegrationIncident:
    await ensure_tenant_exists(session, tenant_id)
    incident = await session.get(IntegrationIncident, incident_id)
    if not incident or incident.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="integration incident not found")

    previous_status = incident.status
    incident.status = payload.status
    incident.updated_at = datetime.now(UTC)
    incident.resolved_at = datetime.now(UTC) if payload.status == "resolved" else None
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="integration.incident.status_changed",
        entity_type="integration_incident",
        entity_id=incident.id,
        summary=f"Integration incident status changed to {incident.status}",
        metadata={
            "integration_incident_id": incident.id,
            "source_type": incident.source_type,
            "source_id": incident.source_id,
            "adapter_key": incident.adapter_key,
            "runbook_key": incident.runbook_key,
            "previous_status": previous_status,
            "new_status": incident.status,
            "operator_note_present": bool(payload.note),
        },
    )
    await commit_or_conflict(session, "integration incident status update failed")
    return incident


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
