from __future__ import annotations

import json
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
    BusinessRecordCreate,
    BusinessRecordTransition,
    BusinessRecordType,
    FileImportCreate,
    MembershipCreate,
    PlatformAdminCreate,
    TenantCreate,
    UserCreate,
    WorkflowRuleCreate,
)
from drivedesk_api.tenant_repository import list_tenant_owned, tenant_owned_select


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


async def create_file_import_job(
    session: AsyncSession,
    *,
    tenant_id: str,
    payload: FileImportCreate,
    actor: ActorContext,
) -> OutboxEvent:
    await ensure_tenant_exists(session, tenant_id)
    record_count = len(payload.records)
    source_name = payload.source_name.strip()
    await write_audit(
        session,
        tenant_id=tenant_id,
        actor=actor,
        event_type="integration.file_import.requested",
        entity_type="integration_job",
        summary=f"File import requested from {source_name}",
        metadata={
            "adapter_key": "file.import.fake",
            "record_count": record_count,
            "source_format": payload.source_format,
            "source_name": source_name,
        },
    )
    event = await enqueue_outbox(
        session,
        tenant_id=tenant_id,
        event_type="integration.file_import.requested",
        adapter_key="file.import.fake",
        payload={
            "adapter_key": "file.import.fake",
            "source_name": source_name,
            "source_format": payload.source_format,
            "record_count": record_count,
            "records": payload.records,
            "simulate_failure": payload.simulate_failure,
        },
    )
    await commit_or_conflict(session, "file import job already exists")
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
