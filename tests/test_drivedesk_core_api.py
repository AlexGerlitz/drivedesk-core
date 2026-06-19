from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections import Counter
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


ROOT = Path(__file__).resolve().parents[1]
for relative in ("apps/api", "apps/worker", "packages/core"):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from drivedesk_api.db import (
    AccessToken,
    AuditEvent,
    AuthAttempt,
    Base,
    BusinessException,
    BusinessRecord,
    BusinessStateObservation,
    IntegrationConnection,
    IntegrationConnectionCheck,
    IntegrationIncident,
    IntegrationReconciliation,
    OutboxEvent,
    PlatformAdmin,
    RepairAction,
    User,
    WorkflowActionRun,
    WorkflowRule,
)
from drivedesk_api.main import build_app
from drivedesk_api.rbac import ActorContext
from drivedesk_api.session import get_session
from drivedesk_api.tenant_repository import list_tenant_owned, tenant_owned_select
from drivedesk_api.tenant_scope import actor_member_tenant_ids
from drivedesk_worker.main import process_outbox_once


@pytest.fixture()
def api_client() -> Iterator[tuple[TestClient, async_sessionmaker[AsyncSession]]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(create_schema())

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app = build_app()
    app.dependency_overrides[get_session] = override_session

    with TestClient(app) as client:
        yield client, session_factory

    asyncio.run(engine.dispose())


def test_tenant_scope_helper_reads_bearer_membership_ids() -> None:
    bearer_actor = ActorContext(
        actor_id="user_1",
        role="owner",
        source="bearer",
        tenant_roles={"tenant_a": "owner", "tenant_b": "viewer"},
    )
    header_actor = ActorContext(actor_id="owner_1", role="owner")

    assert actor_member_tenant_ids(bearer_actor) == ["tenant_a", "tenant_b"]
    assert actor_member_tenant_ids(header_actor) == []


def test_tenant_owned_repository_helper_filters_by_tenant(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_a_response = client.post(
        "/tenants",
        json={"slug": "repo-helper-a", "name": "Repository Helper A"},
        headers=owner_headers,
    )
    assert tenant_a_response.status_code == 201
    tenant_a_id = tenant_a_response.json()["id"]

    tenant_b_response = client.post(
        "/tenants",
        json={"slug": "repo-helper-b", "name": "Repository Helper B"},
        headers=owner_headers,
    )
    assert tenant_b_response.status_code == 201
    tenant_b_id = tenant_b_response.json()["id"]

    async def list_events_for_tenant() -> tuple[list[AuditEvent], list[OutboxEvent]]:
        async with session_factory() as session:
            audits = await list_tenant_owned(
                session,
                AuditEvent,
                tenant_a_id,
                order_by=AuditEvent.created_at.desc(),
            )
            outbox = await list_tenant_owned(
                session,
                OutboxEvent,
                tenant_a_id,
                order_by=OutboxEvent.created_at.desc(),
            )
            return audits, outbox

    audit_events, outbox_events = asyncio.run(list_events_for_tenant())

    assert {event.tenant_id for event in audit_events} == {tenant_a_id}
    assert {event.tenant_id for event in outbox_events} == {tenant_a_id}
    assert tenant_b_id not in {event.tenant_id for event in audit_events}
    assert tenant_b_id not in {event.tenant_id for event in outbox_events}

    with pytest.raises(ValueError, match="User is not a tenant-owned model"):
        tenant_owned_select(User, tenant_a_id)


def test_business_record_lifecycle_policy_catalog_and_preview(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    policies_response = client.get("/business-record-lifecycle-policies")
    assert policies_response.status_code == 200
    policies = {policy["record_type"]: policy for policy in policies_response.json()}
    assert set(policies) == {"contract", "document", "lesson", "payment", "task"}
    assert policies["contract"]["initial_status"] == "draft"
    assert policies["payment"]["terminal_statuses"] == ["cancelled", "refunded"]

    tenant_response = client.post(
        "/tenants",
        json={"slug": "lifecycle-preview", "name": "Lifecycle Preview"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    accepted_response = client.post(
        f"/tenants/{tenant_id}/business-records/lifecycle-preview",
        json={"record_type": "contract", "from_status": "draft", "to_status": "approved"},
        headers=owner_headers,
    )
    assert accepted_response.status_code == 200
    accepted = accepted_response.json()
    assert accepted["valid"] is True
    assert accepted["allowed_next_statuses"] == ["approved", "pending_signature", "cancelled"]
    assert accepted["terminal"] is False

    rejected_response = client.post(
        f"/tenants/{tenant_id}/business-records/lifecycle-preview",
        json={"record_type": "contract", "from_status": "completed", "to_status": "active"},
        headers=owner_headers,
    )
    assert rejected_response.status_code == 200
    rejected = rejected_response.json()
    assert rejected["valid"] is False
    assert rejected["terminal"] is True
    assert rejected["reason"] == "completed is terminal for contract."

    forbidden_response = client.post(
        f"/tenants/{tenant_id}/business-records/lifecycle-preview",
        json={"record_type": "task", "from_status": "open", "to_status": "done"},
        headers={"X-Actor-Id": "auth_1", "X-Actor-Role": "authenticated"},
    )
    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["detail"] == "permission required: business_record:read"


def test_business_record_foundation_is_tenant_scoped_and_audited(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_a_response = client.post(
        "/tenants",
        json={"slug": "business-a", "name": "Business A"},
        headers=owner_headers,
    )
    assert tenant_a_response.status_code == 201
    tenant_a_id = tenant_a_response.json()["id"]

    tenant_b_response = client.post(
        "/tenants",
        json={"slug": "business-b", "name": "Business B"},
        headers=owner_headers,
    )
    assert tenant_b_response.status_code == 201
    tenant_b_id = tenant_b_response.json()["id"]

    manager_a_response = client.post(
        "/users",
        json={"email": "business-manager-a@example.com", "display_name": "Business Manager A", "password": "correct-horse-a"},
        headers=owner_headers,
    )
    assert manager_a_response.status_code == 201
    manager_a_id = manager_a_response.json()["id"]

    viewer_b_response = client.post(
        "/users",
        json={"email": "business-viewer-b@example.com", "display_name": "Business Viewer B", "password": "correct-horse-b"},
        headers=owner_headers,
    )
    assert viewer_b_response.status_code == 201
    viewer_b_id = viewer_b_response.json()["id"]

    assert client.post(
        f"/tenants/{tenant_a_id}/memberships",
        json={"user_id": manager_a_id, "role": "manager"},
        headers=owner_headers,
    ).status_code == 201
    assert client.post(
        f"/tenants/{tenant_b_id}/memberships",
        json={"user_id": viewer_b_id, "role": "viewer"},
        headers=owner_headers,
    ).status_code == 201

    manager_login = client.post(
        "/auth/login",
        json={"email": "business-manager-a@example.com", "password": "correct-horse-a"},
    )
    assert manager_login.status_code == 200
    manager_headers = {"Authorization": f"Bearer {manager_login.json()['access_token']}"}

    viewer_b_login = client.post(
        "/auth/login",
        json={"email": "business-viewer-b@example.com", "password": "correct-horse-b"},
    )
    assert viewer_b_login.status_code == 200
    viewer_b_headers = {"Authorization": f"Bearer {viewer_b_login.json()['access_token']}"}

    workflow_rule_response = client.post(
        f"/tenants/{tenant_a_id}/workflow-rules",
        json={
            "name": "Contract approval sync",
            "record_type": "contract",
            "from_status": "draft",
            "to_status": "approved",
            "action_config": {
                "event_type": "workflow.contract_approved",
                "adapter_key": "internal.workflow",
                "payload": {"next_step": "prepare_signature"},
            },
        },
        headers=owner_headers,
    )
    assert workflow_rule_response.status_code == 201
    workflow_rule = workflow_rule_response.json()
    assert workflow_rule["tenant_id"] == tenant_a_id
    assert workflow_rule["trigger_event_type"] == "business_record.status_changed"
    assert workflow_rule["action_type"] == "emit_outbox_event"
    assert "workflow.contract_approved" in workflow_rule["action_config_json"]

    task_rule_response = client.post(
        f"/tenants/{tenant_a_id}/workflow-rules",
        json={
            "name": "Create signature task",
            "record_type": "contract",
            "from_status": "draft",
            "to_status": "approved",
            "action_type": "create_task_record",
            "action_config": {
                "title": "Prepare signature package",
                "status": "open",
                "payload": {"assignee_role": "manager", "checklist": "signature"},
            },
        },
        headers=owner_headers,
    )
    assert task_rule_response.status_code == 201
    task_rule = task_rule_response.json()
    assert task_rule["action_type"] == "create_task_record"
    assert "Prepare signature package" in task_rule["action_config_json"]

    adapter_sync_rule_response = client.post(
        f"/tenants/{tenant_a_id}/workflow-rules",
        json={
            "name": "Request accounting sync",
            "record_type": "contract",
            "from_status": "draft",
            "to_status": "approved",
            "action_type": "request_adapter_sync",
            "action_config": {
                "event_type": "workflow.contract_sync.requested",
                "adapter_key": "accounting.fake",
                "payload": {"target": "accounting"},
            },
        },
        headers=owner_headers,
    )
    assert adapter_sync_rule_response.status_code == 201
    adapter_sync_rule = adapter_sync_rule_response.json()
    assert adapter_sync_rule["action_type"] == "request_adapter_sync"
    assert "accounting.fake" in adapter_sync_rule["action_config_json"]

    workflow_rules_response = client.get(
        f"/tenants/{tenant_a_id}/workflow-rules",
        headers=manager_headers,
    )
    assert workflow_rules_response.status_code == 200
    assert {rule["name"] for rule in workflow_rules_response.json()} == {
        "Contract approval sync",
        "Create signature task",
        "Request accounting sync",
    }

    contract_response = client.post(
        f"/tenants/{tenant_a_id}/business-records",
        json={
            "record_type": "contract",
            "title": "Training contract draft",
            "status": "draft",
            "external_ref": "contract-001",
            "payload": {"amount_bucket": "1000-2000", "workflow": "lead_to_student"},
        },
        headers=manager_headers,
    )
    assert contract_response.status_code == 201
    contract = contract_response.json()
    assert contract["tenant_id"] == tenant_a_id
    assert contract["record_type"] == "contract"
    assert contract["external_ref"] == "contract-001"
    assert "amount_bucket" in contract["payload_json"]

    payment_response = client.post(
        f"/tenants/{tenant_a_id}/business-records",
        json={
            "record_type": "payment",
            "title": "Payment intent",
            "status": "pending",
            "payload": {"provider": "demo", "amount_bucket": "1000-2000"},
        },
        headers=manager_headers,
    )
    assert payment_response.status_code == 201

    records_response = client.get(
        f"/tenants/{tenant_a_id}/business-records",
        headers=manager_headers,
    )
    assert records_response.status_code == 200
    assert {record["record_type"] for record in records_response.json()} == {"contract", "payment"}

    contract_records_response = client.get(
        f"/tenants/{tenant_a_id}/business-records?record_type=contract",
        headers=manager_headers,
    )
    assert contract_records_response.status_code == 200
    assert [record["record_type"] for record in contract_records_response.json()] == ["contract"]

    transition_response = client.post(
        f"/tenants/{tenant_a_id}/business-records/{contract['id']}/transition",
        json={"status": "approved", "reason": "ready for signature"},
        headers=manager_headers,
    )
    assert transition_response.status_code == 200
    assert transition_response.json()["id"] == contract["id"]
    assert transition_response.json()["status"] == "approved"

    missing_transition_response = client.post(
        f"/tenants/{tenant_b_id}/business-records/{contract['id']}/transition",
        json={"status": "approved"},
        headers=viewer_b_headers,
    )
    assert missing_transition_response.status_code == 403
    assert missing_transition_response.json()["detail"] == "permission required: business_record:write"

    cross_tenant_read_response = client.get(
        f"/tenants/{tenant_b_id}/business-records",
        headers=manager_headers,
    )
    assert cross_tenant_read_response.status_code == 403
    assert cross_tenant_read_response.json()["detail"] == "tenant membership required"

    workflow_action_runs_response = client.get(
        f"/tenants/{tenant_a_id}/workflow-action-runs",
        headers=manager_headers,
    )
    assert workflow_action_runs_response.status_code == 200
    workflow_action_runs = workflow_action_runs_response.json()
    assert {run["action_type"] for run in workflow_action_runs} == {
        "emit_outbox_event",
        "create_task_record",
        "request_adapter_sync",
    }
    assert {run["status"] for run in workflow_action_runs} == {"created"}
    assert {run["source_record_id"] for run in workflow_action_runs} == {contract["id"]}

    cross_tenant_workflow_action_runs_response = client.get(
        f"/tenants/{tenant_b_id}/workflow-action-runs",
        headers=manager_headers,
    )
    assert cross_tenant_workflow_action_runs_response.status_code == 403
    assert cross_tenant_workflow_action_runs_response.json()["detail"] == "tenant membership required"

    viewer_write_response = client.post(
        f"/tenants/{tenant_b_id}/business-records",
        json={"record_type": "task", "title": "Viewer cannot write"},
        headers=viewer_b_headers,
    )
    assert viewer_write_response.status_code == 403
    assert viewer_write_response.json()["detail"] == "permission required: business_record:write"

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_business_records{record_type="contract",status="approved"} 1' in metrics_response.text
    assert 'drivedesk_business_records{record_type="payment",status="pending"} 1' in metrics_response.text
    assert 'drivedesk_business_records{record_type="task",status="open"} 1' in metrics_response.text
    assert (
        'drivedesk_workflow_rules{action_type="emit_outbox_event",'
        'status="active",trigger_event_type="business_record.status_changed"} 1'
    ) in metrics_response.text
    assert (
        'drivedesk_workflow_rules{action_type="create_task_record",'
        'status="active",trigger_event_type="business_record.status_changed"} 1'
    ) in metrics_response.text
    assert (
        'drivedesk_workflow_rules{action_type="request_adapter_sync",'
        'status="active",trigger_event_type="business_record.status_changed"} 1'
    ) in metrics_response.text
    assert 'drivedesk_workflow_action_runs{action_type="emit_outbox_event",status="created"} 1' in metrics_response.text
    assert 'drivedesk_workflow_action_runs{action_type="create_task_record",status="created"} 1' in metrics_response.text
    assert 'drivedesk_workflow_action_runs{action_type="request_adapter_sync",status="created"} 1' in metrics_response.text
    assert "contract-001" not in metrics_response.text
    assert "Training contract draft" not in metrics_response.text
    assert "Prepare signature package" not in metrics_response.text

    async def inspect_business_records() -> tuple[
        list[BusinessRecord],
        list[WorkflowRule],
        list[WorkflowActionRun],
        list[str],
        list[tuple[str, str, str, str]],
    ]:
        async with session_factory() as session:
            business_records = await list_tenant_owned(
                session,
                BusinessRecord,
                tenant_a_id,
                order_by=BusinessRecord.created_at.desc(),
            )
            workflow_rules = await list_tenant_owned(
                session,
                WorkflowRule,
                tenant_a_id,
                order_by=WorkflowRule.created_at.desc(),
            )
            workflow_action_runs = await list_tenant_owned(
                session,
                WorkflowActionRun,
                tenant_a_id,
                order_by=WorkflowActionRun.created_at.desc(),
            )
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(
                    AuditEvent.tenant_id == tenant_a_id,
                    AuditEvent.event_type.in_(
                        [
                            "business_record.created",
                            "business_record.status_changed",
                            "workflow_rule.created",
                            "workflow.rule.triggered",
                            "workflow.action_run.created",
                        ]
                    ),
                )
                .order_by(AuditEvent.created_at)
            )
            outbox_result = await session.execute(
                select(OutboxEvent.id, OutboxEvent.event_type, OutboxEvent.adapter_key, OutboxEvent.payload_json)
                .where(
                    OutboxEvent.tenant_id == tenant_a_id,
                    OutboxEvent.event_type.in_(
                        [
                            "business_record.created",
                            "business_record.status_changed",
                            "workflow_rule.created",
                            "workflow.contract_approved",
                            "workflow.contract_sync.requested",
                            "workflow.task_record.created",
                        ]
                    ),
                )
                .order_by(OutboxEvent.created_at)
            )
            outbox_rows = list(outbox_result.all())
            return (
                business_records,
                workflow_rules,
                workflow_action_runs,
                list(audit_result.scalars().all()),
                [(row.id, row.event_type, row.adapter_key, row.payload_json) for row in outbox_rows],
            )

    records, workflow_rules, workflow_action_runs, audit_events, outbox_rows = asyncio.run(inspect_business_records())
    assert {record.record_type for record in records} == {"contract", "payment", "task"}
    task_records = [record for record in records if record.record_type == "task"]
    assert len(task_records) == 1
    task_record = task_records[0]
    assert task_record.status == "open"
    assert task_record.title == "Prepare signature package"
    assert {rule.name for rule in workflow_rules} == {
        "Contract approval sync",
        "Create signature task",
        "Request accounting sync",
    }
    assert Counter(audit_events) == Counter(
        {
            "workflow_rule.created": 3,
            "business_record.created": 3,
            "business_record.status_changed": 1,
            "workflow.rule.triggered": 3,
            "workflow.action_run.created": 3,
        }
    )
    assert len(workflow_action_runs) == 3
    assert {run.status for run in workflow_action_runs} == {"created"}
    runs_by_action = {run.action_type: run for run in workflow_action_runs}
    outbox_events = [row[1] for row in outbox_rows]
    adapter_keys = [row[2] for row in outbox_rows]
    payloads = [row[3] for row in outbox_rows]
    assert Counter(outbox_events) == Counter(
        {
            "workflow_rule.created": 3,
            "business_record.created": 3,
            "business_record.status_changed": 1,
            "workflow.contract_approved": 1,
            "workflow.contract_sync.requested": 1,
            "workflow.task_record.created": 1,
        }
    )
    assert Counter(adapter_keys) == Counter(
        {
            "internal.workflow": 5,
            "internal.business_record": 4,
            "accounting.fake": 1,
        }
    )
    outbox_ids_by_event = {event: outbox_id for outbox_id, event, _, _ in outbox_rows}
    assert runs_by_action["emit_outbox_event"].outbox_event_id == outbox_ids_by_event["workflow.contract_approved"]
    assert runs_by_action["create_task_record"].outbox_event_id == outbox_ids_by_event["workflow.task_record.created"]
    assert runs_by_action["create_task_record"].task_record_id == task_record.id
    assert runs_by_action["request_adapter_sync"].outbox_event_id == outbox_ids_by_event["workflow.contract_sync.requested"]
    assert runs_by_action["request_adapter_sync"].task_record_id is None
    for run in workflow_action_runs:
        run_result = json.loads(run.result_json)
        assert run_result["workflow_rule_id"] == run.workflow_rule_id
        assert run_result["action_type"] == run.action_type
        assert run_result["source_record_id"] == contract["id"]
    workflow_payload = json.loads(next(payload for _, event, _, payload in outbox_rows if event == "workflow.contract_approved"))
    assert workflow_payload["rule_id"] == workflow_rule["id"]
    assert workflow_payload["record_id"] == contract["id"]
    assert workflow_payload["previous_status"] == "draft"
    assert workflow_payload["new_status"] == "approved"
    assert workflow_payload["payload"] == {"next_step": "prepare_signature"}
    task_payload = json.loads(next(payload for _, event, _, payload in outbox_rows if event == "workflow.task_record.created"))
    assert task_payload["rule_id"] == task_rule["id"]
    assert task_payload["task_record_id"] == task_record.id
    assert task_payload["task_status"] == "open"
    adapter_payload = json.loads(next(payload for _, event, _, payload in outbox_rows if event == "workflow.contract_sync.requested"))
    assert adapter_payload["rule_id"] == adapter_sync_rule["id"]
    assert adapter_payload["payload"] == {"target": "accounting"}


def test_business_control_tower_exception_and_repair_flow(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_response = client.post(
        "/tenants",
        json={"slug": "control-tower", "name": "Control Tower"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    provider_intake_response = client.post(
        f"/tenants/{tenant_id}/business-provider-intake/preview",
        json={
            "provider_key": "crm.bitrix24.mock",
            "source_type": "crm_deal",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "external_ref": "crm-deal-001",
            "provider_payload": {
                "stage": "invoice_sent",
                "amount": 1500,
                "owner_role": "sales",
                "full_name": "Synthetic Customer",
                "phone": "+70000000000",
                "access_token": "never-return-this",
            },
        },
        headers=owner_headers,
    )
    assert provider_intake_response.status_code == 200
    provider_intake = provider_intake_response.json()
    assert provider_intake["provider_key"] == "crm.bitrix24.mock"
    assert provider_intake["source_type"] == "crm_deal"
    assert provider_intake["subject_type"] == "deal"
    assert provider_intake["subject_id"] == "DEAL-2026-001"
    assert provider_intake["safe_payload"] == {
        "amount_bucket": "1000-2000",
        "owner_role": "sales",
        "source_state": "invoice_sent",
    }
    assert set(provider_intake["dropped_keys"]) >= {"access_token", "full_name", "phone"}
    normalized_observation = provider_intake["normalized_observation"]
    assert normalized_observation["system_key"] == "crm.bitrix24.mock"
    assert normalized_observation["system_family"] == "crm"
    assert normalized_observation["subject"] == "deal:DEAL-2026-001"
    assert normalized_observation["external_ref"] == "crm-deal-001"
    assert normalized_observation["state"] == "invoice_sent"
    assert normalized_observation["would_create"] == "BusinessStateObservation"
    assert normalized_observation["would_record_event"] == "business_state.observation.recorded"
    assert normalized_observation["external_fetch"] is False
    assert normalized_observation["external_mutation"] is False
    assert normalized_observation["raw_payload_included"] is False
    assert normalized_observation["pii_included"] is False
    assert normalized_observation["requires_secret"] is False
    assert {item["name"] for item in provider_intake["data_boundaries"]} == {
        "preview_only_no_persist",
        "raw_provider_payload_not_returned",
        "secret_boundary",
    }
    assert {item["step"] for item in provider_intake["next_steps"]} == {
        "record_normalized_observation",
        "open_workbench_context",
        "run_detection_preview",
    }
    assert {item["external_mutation"] for item in provider_intake["next_steps"]} == {False}
    assert provider_intake["evidence"][0]["event"] == "business_provider_intake.previewed"
    assert provider_intake["api"]["preview"] == "POST /tenants/{tenant_id}/business-provider-intake/preview"
    assert provider_intake["api"]["workbench_context"] == (
        "POST /tenants/{tenant_id}/business-workbench-context/preview"
    )

    async def count_control_tower_rows() -> tuple[int, int, int, int, int]:
        async with session_factory() as session:
            records_count = len(
                (
                    await session.execute(
                        select(BusinessRecord).where(BusinessRecord.tenant_id == tenant_id)
                    )
                )
                .scalars()
                .all()
            )
            observations_count = len(
                (
                    await session.execute(
                        select(BusinessStateObservation).where(BusinessStateObservation.tenant_id == tenant_id)
                    )
                )
                .scalars()
                .all()
            )
            exceptions_count = len(
                (
                    await session.execute(
                        select(BusinessException).where(BusinessException.tenant_id == tenant_id)
                    )
                )
                .scalars()
                .all()
            )
            repairs_count = len(
                (
                    await session.execute(
                        select(RepairAction).where(RepairAction.tenant_id == tenant_id)
                    )
                )
                .scalars()
                .all()
            )
            outbox_count = len(
                (await session.execute(select(OutboxEvent).where(OutboxEvent.tenant_id == tenant_id)))
                .scalars()
                .all()
            )
            return records_count, observations_count, exceptions_count, repairs_count, outbox_count

    pipeline_preview_baseline = asyncio.run(count_control_tower_rows())

    pipeline_response = client.post(
        f"/tenants/{tenant_id}/business-intake-pipeline/preview",
        json={
            "role": "accountant",
            "events": [
                {
                    "provider_key": "crm.bitrix24.mock",
                    "source_type": "crm_deal",
                    "subject_type": "deal",
                    "subject_id": "DEAL-2026-001",
                    "external_ref": "crm-deal-001",
                    "provider_payload": {
                        "stage": "invoice_sent",
                        "amount": 1500,
                        "owner_role": "sales",
                        "full_name": "Synthetic Customer",
                        "phone": "+70000000000",
                        "access_token": "never-return-this",
                    },
                },
                {
                    "provider_key": "bank.statement.mock",
                    "source_type": "bank_payment",
                    "subject_type": "deal",
                    "subject_id": "DEAL-2026-001",
                    "external_ref": "bank-payment-001",
                    "provider_payload": {
                        "status": "captured",
                        "amount": 1500,
                        "matched_by": "payment_reference",
                        "payer_phone": "+70000000000",
                    },
                },
                {
                    "provider_key": "accounting.export.mock",
                    "source_type": "accounting_export",
                    "subject_type": "deal",
                    "subject_id": "DEAL-2026-001",
                    "external_ref": "accounting-export-001",
                    "provider_payload": {
                        "export_status": "not_exported",
                        "export_batch_id": "batch-001",
                        "reason": "waiting_for_crm_status",
                        "session_secret": "never-return-this",
                    },
                },
            ],
        },
        headers=owner_headers,
    )
    assert pipeline_response.status_code == 200
    pipeline = pipeline_response.json()
    assert pipeline["status"] == "previewed"
    assert pipeline["role"] == "accountant"
    assert pipeline["source_systems"] == [
        "accounting.export.mock",
        "bank.statement.mock",
        "crm.bitrix24.mock",
    ]
    assert "processed 3 event" in pipeline["summary"]
    assert len(pipeline["intake_previews"]) == 3
    assert {item["provider_key"] for item in pipeline["intake_previews"]} == {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }
    serialized_pipeline = json.dumps(pipeline, ensure_ascii=False, sort_keys=True).lower()
    for leaked in ["never-return-this", "+70000000000", "synthetic customer"]:
        assert leaked not in serialized_pipeline
    assert {"access_token", "full_name", "phone"} <= set(pipeline["intake_previews"][0]["dropped_keys"])
    assert "payer_phone" in pipeline["intake_previews"][1]["dropped_keys"]
    assert "session_secret" in pipeline["intake_previews"][2]["dropped_keys"]
    assert {item["system_family"] for item in pipeline["workbench_context"]["context_cards"]} == {
        "accounting",
        "bank",
        "crm",
    }
    assert {item["raw_payload_included"] for item in pipeline["workbench_context"]["context_cards"]} == {False}
    assert {item["pii_included"] for item in pipeline["workbench_context"]["context_cards"]} == {False}
    assert {item["external_fetch"] for item in pipeline["workbench_context"]["context_cards"]} == {False}
    assert {item["external_mutation"] for item in pipeline["workbench_context"]["context_cards"]} == {False}
    assert pipeline["detections"]["status"] == "detected"
    assert len(pipeline["detections"]["detected_exceptions"]) == 1
    assert pipeline["detections"]["detected_exceptions"][0]["exception_type"] == "crm_payment_mismatch"
    assert pipeline["detections"]["suggested_repair_actions"][0]["requires_approval"] is True
    assert pipeline["detections"]["suggested_repair_actions"][0]["external_mutation"] is False
    assert [item["lane"] for item in pipeline["action_plan"]["lanes"]] == [
        "intake",
        "context",
        "exceptions",
        "repair",
    ]
    assert {item["step"] for item in pipeline["action_plan"]["steps"]} >= {
        "normalize_provider_events",
        "open_role_workbench",
        "review_detected_exceptions",
        "prepare_approval_gated_repair",
    }
    assert {item["external_mutation"] for item in pipeline["action_plan"]["steps"]} == {False}
    assert {item["gate"] for item in pipeline["action_plan"]["approval_gates"]} == {
        "external_write_gate",
        "notification_delivery_gate",
    }
    assert any(
        item["candidate"] == "send_external_notification" and item["safe_to_auto_run"] is False
        for item in pipeline["action_plan"]["automation_candidates"]
    )
    assert pipeline["notification_preview"]["summary"].startswith("Draft-only notification preview")
    assert {item["external_delivery"] for item in pipeline["notification_preview"]["channels"]} == {False}
    assert {item["external_delivery"] for item in pipeline["notification_preview"]["drafts"]} == {False}
    assert {item["name"] for item in pipeline["data_boundaries"]} == {
        "no_external_calls",
        "no_persistence",
        "secret_and_pii_boundary",
    }
    assert {item.get("external_mutation") for item in pipeline["data_boundaries"] if "external_mutation" in item} == {
        False
    }
    assert pipeline["evidence"][0]["event"] == "business_intake_pipeline.previewed"
    assert pipeline["api"]["preview"] == "POST /tenants/{tenant_id}/business-intake-pipeline/preview"
    assert pipeline["api"]["provider_intake"] == "POST /tenants/{tenant_id}/business-provider-intake/preview"

    assert asyncio.run(count_control_tower_rows()) == pipeline_preview_baseline

    handoff_baseline = asyncio.run(count_control_tower_rows())
    handoff_response = client.post(
        f"/tenants/{tenant_id}/business-task-handoffs/preview",
        json={
            "role": "accountant",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "action_plan_steps": [
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
            ],
        },
        headers=owner_headers,
    )
    assert handoff_response.status_code == 200
    handoff = handoff_response.json()
    assert handoff["status"] == "previewed"
    assert handoff["handoff_kind"] == "action_plan_task_handoff"
    assert handoff["role"] == "accountant"
    assert handoff["subject_type"] == "deal"
    assert handoff["subject_id"] == "DEAL-2026-001"
    assert "prepared 2 internal task" in handoff["summary"]
    assert len(handoff["task_cards"]) == 2
    assert {item["status"] for item in handoff["task_cards"]} == {"would_create"}
    assert {item["would_create"] for item in handoff["task_cards"]} == {"BusinessRecord(type=task)"}
    assert {item["assignee_role"] for item in handoff["task_cards"]} == {"accountant"}
    assert {item["contains_pii"] for item in handoff["task_cards"]} == {False}
    assert {item["raw_payload_included"] for item in handoff["task_cards"]} == {False}
    assert {item["external_mutation"] for item in handoff["task_cards"]} == {False}
    assert any(item["requires_approval"] is True for item in handoff["task_cards"])
    assert len(handoff["outbox_candidates"]) == 2
    assert {item["event_type"] for item in handoff["outbox_candidates"]} == {"task.created"}
    assert {item["adapter_key"] for item in handoff["outbox_candidates"]} == {"internal.noop"}
    assert {item["status"] for item in handoff["outbox_candidates"]} == {"would_enqueue"}
    assert {item["contains_pii"] for item in handoff["outbox_candidates"]} == {False}
    assert {item["external_mutation"] for item in handoff["outbox_candidates"]} == {False}
    assert len(handoff["notification_drafts"]) == 2
    assert {item["status"] for item in handoff["notification_drafts"]} == {"draft_only"}
    assert {item["external_delivery"] for item in handoff["notification_drafts"]} == {False}
    assert {item["contains_pii"] for item in handoff["notification_drafts"]} == {False}
    assert {item["gate"] for item in handoff["approval_gates"]} == {
        "task_creation_review",
        "external_write_gate",
        "repair_action_approval",
    }
    assert {item["name"] for item in handoff["data_boundaries"]} == {
        "preview_only_no_persistence",
        "internal_only_outbox",
        "safe_task_payload",
    }
    assert {item.get("external_mutation") for item in handoff["data_boundaries"] if "external_mutation" in item} == {
        False
    }
    assert handoff["evidence"][0]["event"] == "business_task_handoff.previewed"
    assert handoff["api"]["preview"] == "POST /tenants/{tenant_id}/business-task-handoffs/preview"
    serialized_handoff = json.dumps(handoff, ensure_ascii=False, sort_keys=True).lower()
    for leaked in ["never-return-this", "+70000000000", "synthetic customer", "password", "authorization"]:
        assert leaked not in serialized_handoff
    assert asyncio.run(count_control_tower_rows()) == handoff_baseline

    notification_matrix_baseline = asyncio.run(count_control_tower_rows())
    notification_matrix_response = client.post(
        f"/tenants/{tenant_id}/business-notification-channels/preview",
        json={
            "role": "accountant",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "channels": ["in_app", "telegram", "email", "sms", "webhook"],
            "include_delivery_drafts": True,
        },
        headers=owner_headers,
    )
    assert notification_matrix_response.status_code == 200
    notification_matrix = notification_matrix_response.json()
    assert notification_matrix["status"] == "previewed"
    assert notification_matrix["matrix_kind"] == "operator_channel_readiness"
    assert notification_matrix["role"] == "accountant"
    assert notification_matrix["subject_type"] == "deal"
    assert notification_matrix["subject_id"] == "DEAL-2026-001"
    assert "evaluated 5 channel" in notification_matrix["summary"]
    channel_by_key = {item["channel"]: item for item in notification_matrix["channels"]}
    assert set(channel_by_key) == {"in_app", "telegram", "email", "sms", "webhook"}
    assert channel_by_key["in_app"]["status"] == "ready"
    assert channel_by_key["in_app"]["configured"] is True
    assert channel_by_key["in_app"]["requires_secret"] is False
    assert channel_by_key["in_app"]["requires_private_connector"] is False
    assert {
        channel_by_key[channel]["requires_secret"]
        for channel in ["telegram", "email", "sms", "webhook"]
    } == {True}
    assert {
        channel_by_key[channel]["requires_private_connector"]
        for channel in ["telegram", "email", "sms", "webhook"]
    } == {True}
    assert {item["external_delivery"] for item in notification_matrix["channels"]} == {False}
    assert {item["contains_pii"] for item in notification_matrix["channels"]} == {False}
    assert {item["raw_payload_included"] for item in notification_matrix["channels"]} == {False}
    assert {item["rule"] for item in notification_matrix["routing_rules"]} == {
        "prefer_internal_in_app",
        "external_channels_require_private_connector",
        "safe_payload_only",
    }
    assert len(notification_matrix["delivery_drafts"]) == 5
    assert {item["would_enqueue_event"] for item in notification_matrix["delivery_drafts"]} == {
        "notification.delivery.requested"
    }
    assert {item["external_delivery"] for item in notification_matrix["delivery_drafts"]} == {False}
    assert {item["contains_pii"] for item in notification_matrix["delivery_drafts"]} == {False}
    assert {item["raw_payload_included"] for item in notification_matrix["delivery_drafts"]} == {False}
    assert {item["gate"] for item in notification_matrix["approval_gates"]} == {
        "notification_content_review",
        "private_channel_secret_setup",
        "external_delivery_gate",
    }
    assert {item["name"] for item in notification_matrix["data_boundaries"]} == {
        "preview_only_no_delivery",
        "server_secret_store_boundary",
        "safe_notification_payload",
    }
    assert notification_matrix["evidence"][0]["event"] == "business_notification_channel_matrix.previewed"
    assert (
        notification_matrix["api"]["preview"]
        == "POST /tenants/{tenant_id}/business-notification-channels/preview"
    )
    serialized_matrix = json.dumps(notification_matrix, ensure_ascii=False, sort_keys=True).lower()
    for leaked in ["never-return-this", "+70000000000", "synthetic customer", "password", "authorization"]:
        assert leaked not in serialized_matrix
    assert asyncio.run(count_control_tower_rows()) == notification_matrix_baseline

    observation_payloads = [
        {
            "system_key": "crm.bitrix24.mock",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "external_ref": "crm-deal-001",
            "state": "invoice_sent",
            "payload": {"amount_bucket": "1000-2000", "owner_role": "sales"},
        },
        {
            "system_key": "bank.statement.mock",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "external_ref": "bank-payment-001",
            "state": "paid",
            "payload": {"amount_bucket": "1000-2000", "matched_by": "payment_reference"},
        },
        {
            "system_key": "accounting.export.mock",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "external_ref": "accounting-export-001",
            "state": "not_exported",
            "payload": {"export_batch_id": "batch-001", "reason": "waiting_for_crm_status"},
        },
    ]
    observation_ids: list[str] = []
    for payload in observation_payloads:
        response = client.post(
            f"/tenants/{tenant_id}/business-state/observations",
            json=payload,
            headers=owner_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["tenant_id"] == tenant_id
        assert body["system_key"] == payload["system_key"]
        assert body["subject_id"] == "DEAL-2026-001"
        observation_ids.append(body["id"])

    observations_response = client.get(
        f"/tenants/{tenant_id}/business-state/observations?subject_id=DEAL-2026-001",
        headers=owner_headers,
    )
    assert observations_response.status_code == 200
    assert {item["system_key"] for item in observations_response.json()} == {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }

    detection_response = client.post(
        f"/tenants/{tenant_id}/business-detections/preview",
        json={
            "rule_set": "payment_reconciliation",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
        },
        headers=owner_headers,
    )
    assert detection_response.status_code == 200
    detection = detection_response.json()
    assert detection["rule_set"] == "payment_reconciliation"
    assert detection["subject_type"] == "deal"
    assert detection["subject_id"] == "DEAL-2026-001"
    assert detection["source_systems"] == [
        "accounting.export.mock",
        "bank.statement.mock",
        "crm.bitrix24.mock",
    ]
    assert "found 1 exception candidate" in detection["summary"]
    assert len(detection["detected_exceptions"]) == 1
    detected_exception = detection["detected_exceptions"][0]
    assert detected_exception["exception_type"] == "crm_payment_mismatch"
    assert detected_exception["severity"] == "warning"
    assert detected_exception["confidence"] == "high"
    assert detected_exception["would_create"] == "BusinessException"
    assert {item["system_family"] for item in detected_exception["evidence"]} == {
        "accounting",
        "bank",
        "crm",
    }
    assert len(detection["suggested_repair_actions"]) == 1
    suggested_repair = detection["suggested_repair_actions"][0]
    assert suggested_repair["action_type"] == "sync_status"
    assert suggested_repair["requires_approval"] is True
    assert suggested_repair["payload"]["external_mutation"] is False
    assert suggested_repair["would_create"] == "RepairAction"
    assert detection["api"]["preview"] == "POST /tenants/{tenant_id}/business-detections/preview"
    assert detection["api"]["briefing"] == "POST /tenants/{tenant_id}/business-briefings/preview"

    business_exception_response = client.post(
        f"/tenants/{tenant_id}/business-exceptions",
        json={
            "exception_type": "crm_payment_mismatch",
            "severity": "warning",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "title": "Payment received but CRM and accounting lag behind",
            "summary": "Bank shows a paid deal while CRM is still invoice_sent and accounting is not_exported.",
            "impact": {
                "cash_state": "received",
                "operational_risk": "manual follow-up required",
                "customer_visible": False,
            },
            "evidence": {"detector": "synthetic_business_rule"},
            "observation_ids": observation_ids,
        },
        headers=owner_headers,
    )
    assert business_exception_response.status_code == 201
    business_exception = business_exception_response.json()
    assert business_exception["exception_type"] == "crm_payment_mismatch"
    assert business_exception["status"] == "open"
    assert business_exception["severity"] == "warning"
    exception_evidence = json.loads(business_exception["evidence_json"])
    assert set(exception_evidence["observation_ids"]) == set(observation_ids)
    assert {item["system_key"] for item in exception_evidence["observations"]} == {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }

    repair_response = client.post(
        f"/tenants/{tenant_id}/business-exceptions/{business_exception['id']}/repair-actions",
        json={
            "action_type": "sync_status",
            "safety_level": "medium",
            "requires_approval": True,
            "payload": {
                "target_adapter_key": "crm.bitrix24.mock",
                "desired_state": "paid",
                "source_evidence": "bank.statement.mock",
            },
        },
        headers=owner_headers,
    )
    assert repair_response.status_code == 201
    repair_action = repair_response.json()
    assert repair_action["status"] == "proposed"
    assert repair_action["requires_approval"] is True
    assert repair_action["safety_level"] == "medium"

    blocked_execute_response = client.post(
        f"/tenants/{tenant_id}/repair-actions/{repair_action['id']}/execute",
        json={"mode": "dry_run"},
        headers=owner_headers,
    )
    assert blocked_execute_response.status_code == 409
    assert blocked_execute_response.json()["detail"] == "repair action approval required"

    approved_response = client.post(
        f"/tenants/{tenant_id}/repair-actions/{repair_action['id']}/approve",
        headers=owner_headers,
    )
    assert approved_response.status_code == 200
    assert approved_response.json()["status"] == "approved"

    escalation_response = client.post(
        f"/tenants/{tenant_id}/business-escalations/preview",
        json={
            "policy": "exception_triage",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
        },
        headers=owner_headers,
    )
    assert escalation_response.status_code == 200
    escalation = escalation_response.json()
    assert escalation["policy"] == "exception_triage"
    assert escalation["risk_level"] == "attention"
    assert "routed 1 open exception" in escalation["summary"]
    assert escalation["queues"] == [
        {
            "queue": "finance_reconciliation",
            "owner_role": "accountant",
            "open_items": 1,
            "highest_severity": "warning",
            "min_sla_minutes": 120,
            "status": "active",
        }
    ]
    assert len(escalation["escalation_items"]) == 1
    escalation_item = escalation["escalation_items"][0]
    assert escalation_item["business_exception_id"] == business_exception["id"]
    assert escalation_item["exception_type"] == "crm_payment_mismatch"
    assert escalation_item["owner_role"] == "accountant"
    assert escalation_item["queue"] == "finance_reconciliation"
    assert escalation_item["sla_minutes"] == 120
    assert escalation_item["next_action"] == "execute_repair_dry_run"
    assert escalation_item["next_action_status"] == "ready"
    assert escalation_item["external_mutation"] is False
    assert {item["action"] for item in escalation["suggested_actions"]} == {"execute_repair_dry_run"}
    assert escalation["suggested_actions"][0]["endpoint"] == (
        f"POST /tenants/{tenant_id}/repair-actions/{repair_action['id']}/execute"
    )
    assert escalation["suggested_actions"][0]["external_mutation"] is False
    assert {item["name"] for item in escalation["review_points"]} == {
        "write_boundary",
        "owner_routing",
        "repair_handoff",
    }
    assert {item["type"] for item in escalation["evidence"]} >= {"business_exception", "repair_action"}
    assert escalation["api"]["preview"] == "POST /tenants/{tenant_id}/business-escalations/preview"

    action_plan_response = client.post(
        f"/tenants/{tenant_id}/business-action-plans/preview",
        json={
            "plan_kind": "exception_resolution",
            "role": "accountant",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
        },
        headers=owner_headers,
    )
    assert action_plan_response.status_code == 200
    action_plan = action_plan_response.json()
    assert action_plan["plan_kind"] == "exception_resolution"
    assert action_plan["role"] == "accountant"
    assert action_plan["risk_level"] == "attention"
    assert "3 step" in action_plan["summary"]
    assert action_plan["lanes"] == [
        {
            "lane": "finance_reconciliation",
            "owner_role": "accountant",
            "sla_minutes": 120,
            "work_items": 1,
            "status": "active",
        }
    ]
    assert [item["step"] for item in action_plan["steps"]] == [
        "verify_source_evidence",
        "execute_repair_dry_run",
        "close_or_acknowledge_exception",
    ]
    assert action_plan["steps"][0]["source_systems"] == [
        "accounting.export.mock",
        "bank.statement.mock",
        "crm.bitrix24.mock",
    ]
    assert action_plan["steps"][1]["endpoint"] == (
        f"POST /tenants/{tenant_id}/repair-actions/{repair_action['id']}/execute"
    )
    assert action_plan["steps"][1]["external_mutation"] is False
    assert action_plan["steps"][2]["status"] == "waiting_for_repair"
    assert {item["name"] for item in action_plan["automation_candidates"]} >= {
        "queue_repair_execution",
        "recheck_accounting_export",
    }
    assert action_plan["approval_gates"] == [
        {
            "name": "repair_action_approval",
            "repair_action_id": repair_action["id"],
            "status": "satisfied",
            "requires_approval": True,
            "external_mutation": False,
            "evidence": "repair_action.approved",
        }
    ]
    assert {item["name"] for item in action_plan["review_points"]} == {
        "single_work_surface",
        "approval_boundary",
        "automation_boundary",
    }
    assert {item["type"] for item in action_plan["evidence"]} >= {
        "observation",
        "business_exception",
        "repair_action",
    }
    assert action_plan["api"]["preview"] == "POST /tenants/{tenant_id}/business-action-plans/preview"

    notification_response = client.post(
        f"/tenants/{tenant_id}/business-notifications/preview",
        json={
            "notification_kind": "action_plan_updates",
            "role": "accountant",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
            "channels": ["in_app", "telegram"],
        },
        headers=owner_headers,
    )
    assert notification_response.status_code == 200
    notification = notification_response.json()
    assert notification["notification_kind"] == "action_plan_updates"
    assert notification["role"] == "accountant"
    assert notification["risk_level"] == "attention"
    assert "prepared 2 draft" in notification["summary"]
    assert {item["channel"] for item in notification["channels"]} == {"in_app", "telegram"}
    assert {item["external_delivery"] for item in notification["channels"]} == {False}
    assert {item["requires_secret"] for item in notification["channels"]} == {False, True}
    assert {item["recipient_role"] for item in notification["drafts"]} == {"accountant"}
    assert {item["pii_included"] for item in notification["drafts"]} == {False}
    assert {item["external_delivery"] for item in notification["drafts"]} == {False}
    assert {item["status"] for item in notification["drafts"]} == {"ready", "preview_only"}
    assert {item["send_mode"] for item in notification["delivery_plan"]} == {"preview_only"}
    assert {item["would_enqueue_event"] for item in notification["delivery_plan"]} == {
        "notification.delivery.requested"
    }
    assert {item["name"] for item in notification["approval_gates"]} >= {
        "notification_content_review",
        "repair_action_approval",
    }
    assert {item["name"] for item in notification["review_points"]} == {
        "no_external_send",
        "pii_boundary",
        "action_plan_link",
    }
    assert {item["type"] for item in notification["evidence"]} >= {
        "action_plan",
        "observation",
        "business_exception",
        "repair_action",
    }
    assert notification["api"]["preview"] == "POST /tenants/{tenant_id}/business-notifications/preview"
    assert notification["api"]["action_plan"] == "POST /tenants/{tenant_id}/business-action-plans/preview"

    context_response = client.post(
        f"/tenants/{tenant_id}/business-workbench-context/preview",
        json={
            "context_kind": "role_assist",
            "role": "accountant",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
        },
        headers=owner_headers,
    )
    assert context_response.status_code == 200
    context = context_response.json()
    assert context["context_kind"] == "role_assist"
    assert context["role"] == "accountant"
    assert context["risk_level"] == "attention"
    assert context["source_systems"] == [
        "accounting.export.mock",
        "bank.statement.mock",
        "crm.bitrix24.mock",
    ]
    assert {item["system_family"] for item in context["context_cards"]} == {
        "accounting",
        "bank",
        "crm",
    }
    assert {item["status"] for item in context["context_cards"]} == {
        "action_required",
        "confirmed",
        "needs_cross_check",
    }
    assert {item["pii_included"] for item in context["context_cards"]} == {False}
    assert {item["raw_payload_included"] for item in context["context_cards"]} == {False}
    assert {item["external_fetch"] for item in context["context_cards"]} == {False}
    assert {item["external_mutation"] for item in context["context_cards"]} == {False}
    assert {item["action"] for item in context["suggested_actions"]} >= {
        "reconcile_crm_payment_status",
        "review_accounting_export",
        "open_action_plan_preview",
    }
    assert {item["external_mutation"] for item in context["suggested_actions"]} == {False}
    assert {item["name"] for item in context["data_boundaries"]} == {
        "read_only_source_context",
        "pii_redaction",
        "secret_boundary",
    }
    assert {item["status"] for item in context["data_boundaries"]} >= {"clean", "preview_only"}
    assert {item["type"] for item in context["evidence"]} >= {"observation", "business_exception"}
    assert context["api"]["preview"] == "POST /tenants/{tenant_id}/business-workbench-context/preview"
    assert context["api"]["action_plan"] == "POST /tenants/{tenant_id}/business-action-plans/preview"

    briefing_response = client.post(
        f"/tenants/{tenant_id}/business-briefings/preview",
        json={
            "role": "accountant",
            "subject_type": "deal",
            "subject_id": "DEAL-2026-001",
        },
        headers=owner_headers,
    )
    assert briefing_response.status_code == 200
    briefing = briefing_response.json()
    assert briefing["role"] == "accountant"
    assert briefing["risk_level"] == "attention"
    assert briefing["subject_type"] == "deal"
    assert briefing["subject_id"] == "DEAL-2026-001"
    assert briefing["source_systems"] == [
        "accounting.export.mock",
        "bank.statement.mock",
        "crm.bitrix24.mock",
    ]
    assert "1 open exception" in briefing["summary"]
    assert {item["type"] for item in briefing["highlights"]} >= {
        "business_exception",
        "state_observation",
    }
    assert {item.get("system") for item in briefing["highlights"] if item["type"] == "state_observation"} >= {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }
    assert {item["action"] for item in briefing["recommended_actions"]} == {"execute_repair_dry_run"}
    assert briefing["recommended_actions"][0]["status"] == "ready"
    assert briefing["review_points"][1]["name"] == "external_mutation"
    assert briefing["review_points"][1]["status"] == "review_required"
    assert {item["type"] for item in briefing["evidence"]} >= {
        "observation",
        "exception",
        "repair_action",
    }
    assert briefing["api"]["preview"] == "POST /tenants/{tenant_id}/business-briefings/preview"

    executed_response = client.post(
        f"/tenants/{tenant_id}/repair-actions/{repair_action['id']}/execute",
        json={"mode": "dry_run", "note": "public-safe repair drill"},
        headers=owner_headers,
    )
    assert executed_response.status_code == 200
    executed_repair_action = executed_response.json()
    assert executed_repair_action["status"] == "executed"
    repair_result = json.loads(executed_repair_action["result_json"])
    assert repair_result["dry_run"] is True
    assert repair_result["external_mutation"] is False
    assert repair_result["queued_event_type"] == "repair_action.execution_requested"

    repair_actions_response = client.get(
        f"/tenants/{tenant_id}/repair-actions?business_exception_id={business_exception['id']}",
        headers=owner_headers,
    )
    assert repair_actions_response.status_code == 200
    assert [item["id"] for item in repair_actions_response.json()] == [repair_action["id"]]

    acknowledged_response = client.post(
        f"/tenants/{tenant_id}/business-exceptions/{business_exception['id']}/status",
        json={"status": "acknowledged", "note": "operator reviewed repair evidence"},
        headers=owner_headers,
    )
    assert acknowledged_response.status_code == 200
    assert acknowledged_response.json()["status"] == "acknowledged"

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_business_state_observations{state="paid",system_key="bank.statement.mock"} 1' in metrics_response.text
    assert (
        'drivedesk_business_exceptions{exception_type="crm_payment_mismatch",'
        'severity="warning",status="acknowledged"} 1'
    ) in metrics_response.text
    assert 'drivedesk_repair_actions{action_type="sync_status",status="executed"} 1' in metrics_response.text
    assert "DEAL-2026-001" not in metrics_response.text
    assert "bank-payment-001" not in metrics_response.text

    async def inspect_control_tower_state() -> tuple[
        list[BusinessStateObservation],
        list[BusinessException],
        list[RepairAction],
        list[str],
        list[tuple[str, str, str]],
    ]:
        async with session_factory() as session:
            observations_result = await session.execute(
                select(BusinessStateObservation).where(BusinessStateObservation.tenant_id == tenant_id)
            )
            exceptions_result = await session.execute(
                select(BusinessException).where(BusinessException.tenant_id == tenant_id)
            )
            repairs_result = await session.execute(select(RepairAction).where(RepairAction.tenant_id == tenant_id))
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(
                    AuditEvent.tenant_id == tenant_id,
                    AuditEvent.event_type.in_(
                        [
                            "business_state.observation.recorded",
                            "business_exception.created",
                            "business_exception.status_changed",
                            "repair_action.proposed",
                            "repair_action.approved",
                            "repair_action.executed",
                        ]
                    ),
                )
                .order_by(AuditEvent.created_at)
            )
            outbox_result = await session.execute(
                select(OutboxEvent.event_type, OutboxEvent.adapter_key, OutboxEvent.payload_json)
                .where(
                    OutboxEvent.tenant_id == tenant_id,
                    OutboxEvent.event_type.in_(
                        [
                            "business_state.observation.recorded",
                            "business_exception.created",
                            "repair_action.proposed",
                            "repair_action.execution_requested",
                        ]
                    ),
                )
                .order_by(OutboxEvent.created_at)
            )
            return (
                list(observations_result.scalars().all()),
                list(exceptions_result.scalars().all()),
                list(repairs_result.scalars().all()),
                list(audit_result.scalars().all()),
                [(row.event_type, row.adapter_key, row.payload_json) for row in outbox_result.all()],
            )

    observations, exceptions, repairs, audit_events, outbox_rows = asyncio.run(inspect_control_tower_state())
    assert len(observations) == 3
    assert len(exceptions) == 1
    assert len(repairs) == 1
    assert exceptions[0].status == "acknowledged"
    assert repairs[0].status == "executed"
    assert Counter(audit_events) == Counter(
        {
            "business_state.observation.recorded": 3,
            "business_exception.created": 1,
            "repair_action.proposed": 1,
            "repair_action.approved": 1,
            "repair_action.executed": 1,
            "business_exception.status_changed": 1,
        }
    )
    assert Counter(row[0] for row in outbox_rows) == Counter(
        {
            "business_state.observation.recorded": 3,
            "business_exception.created": 1,
            "repair_action.proposed": 1,
            "repair_action.execution_requested": 1,
        }
    )
    execution_payload = json.loads(
        next(payload for event_type, _, payload in outbox_rows if event_type == "repair_action.execution_requested")
    )
    assert execution_payload["mode"] == "dry_run"
    assert execution_payload["external_mutation"] is False
    assert execution_payload["payload"]["target_adapter_key"] == "crm.bitrix24.mock"


def test_identity_rbac_audit_and_outbox_flow(api_client: tuple[TestClient, async_sessionmaker[AsyncSession]]) -> None:
    client, session_factory = api_client

    default_forbidden_response = client.post(
        "/tenants",
        json={"slug": "no-header", "name": "No Header"},
    )
    assert default_forbidden_response.status_code == 403
    assert default_forbidden_response.json()["detail"] == "permission required: tenant:write"

    tenant_response = client.post(
        "/tenants",
        json={"slug": "drive-test", "name": "Drive Test"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    forbidden_response = client.post(
        "/users",
        json={"email": "viewer@example.com", "display_name": "Viewer"},
        headers={"X-Actor-Id": "viewer_1", "X-Actor-Role": "viewer"},
    )
    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["detail"] == "permission required: user:write"

    user_response = client.post(
        "/users",
        json={"email": "manager@example.com", "display_name": "Manager User", "password": "correct-horse-1"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert user_response.status_code == 201
    assert "password" not in user_response.json()
    user_id = user_response.json()["id"]

    membership_response = client.post(
        f"/tenants/{tenant_id}/memberships",
        json={"user_id": user_id, "role": "manager"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert membership_response.status_code == 201
    assert membership_response.json()["role"] == "manager"

    bad_login_response = client.post(
        "/auth/login",
        json={"email": "manager@example.com", "password": "wrong-secret"},
    )
    assert bad_login_response.status_code == 401
    assert bad_login_response.json()["detail"] == "invalid credentials"

    login_response = client.post(
        "/auth/login",
        json={"email": "manager@example.com", "password": "correct-horse-1"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["token_type"] == "bearer"
    assert login_payload["access_token"]
    assert login_payload["user"]["email"] == "manager@example.com"
    assert "password" not in login_payload["user"]
    auth_headers = {"Authorization": f"Bearer {login_payload['access_token']}"}

    me_response = client.get("/auth/me", headers=auth_headers)
    assert me_response.status_code == 200
    assert me_response.json()["user"]["id"] == user_id
    assert me_response.json()["memberships"][0]["tenant_id"] == tenant_id

    tenants_response = client.get("/tenants", headers=auth_headers)
    assert tenants_response.status_code == 200
    assert tenants_response.json()[0]["slug"] == "drive-test"

    memberships_response = client.get(
        f"/tenants/{tenant_id}/memberships",
        headers=auth_headers,
    )
    assert memberships_response.status_code == 200
    assert memberships_response.json()[0]["user_id"] == user_id

    audit_response = client.get(
        f"/tenants/{tenant_id}/audit-events",
        headers=auth_headers,
    )
    assert audit_response.status_code == 200
    event_types = {event["event_type"] for event in audit_response.json()}
    assert {"tenant.created", "membership.created"}.issubset(event_types)

    second_tenant_response = client.post(
        "/tenants",
        json={"slug": "other-tenant", "name": "Other Tenant"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert second_tenant_response.status_code == 201
    forbidden_tenant_response = client.get(f"/tenants/{second_tenant_response.json()['id']}", headers=auth_headers)
    assert forbidden_tenant_response.status_code == 403
    assert forbidden_tenant_response.json()["detail"] == "tenant membership required"

    write_forbidden_response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "source_name": "manager-write",
            "source_format": "json",
            "records": [{"external_id": "lead_write", "display_name": "Write Demo"}],
        },
        headers=auth_headers,
    )
    assert write_forbidden_response.status_code == 403
    assert write_forbidden_response.json()["detail"] == "permission required: tenant:write"

    logout_response = client.post("/auth/logout", headers=auth_headers)
    assert logout_response.status_code == 200
    assert logout_response.json()["revoked"] is True
    assert logout_response.json()["status"] == "revoked"

    revoked_me_response = client.get("/auth/me", headers=auth_headers)
    assert revoked_me_response.status_code == 401
    assert revoked_me_response.json()["detail"] == "invalid or expired access token"

    outbox_response = client.get(
        f"/tenants/{tenant_id}/outbox-events",
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert outbox_response.status_code == 200
    assert {event["status"] for event in outbox_response.json()} == {"pending"}

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed == 4

    async def outbox_statuses() -> list[str]:
        async with session_factory() as session:
            result = await session.execute(select(OutboxEvent.status).order_by(OutboxEvent.created_at))
            return list(result.scalars().all())

    assert asyncio.run(outbox_statuses()) == ["processed", "processed", "processed", "processed"]

    async def auth_state() -> tuple[list[str], list[str], list[str]]:
        async with session_factory() as session:
            attempt_result = await session.execute(select(AuthAttempt.outcome).order_by(AuthAttempt.created_at))
            token_result = await session.execute(select(AccessToken.status).order_by(AccessToken.created_at))
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(AuditEvent.tenant_id == "platform", AuditEvent.event_type.like("auth.%"))
                .order_by(AuditEvent.created_at)
            )
            return (
                list(attempt_result.scalars().all()),
                list(token_result.scalars().all()),
                list(audit_result.scalars().all()),
            )

    attempt_outcomes, token_statuses, auth_event_types = asyncio.run(auth_state())
    assert attempt_outcomes == ["failure", "success"]
    assert token_statuses == ["revoked"]
    assert {
        "auth.login.failed",
        "auth.login.succeeded",
        "auth.token.revoked",
    }.issubset(set(auth_event_types))


def test_login_attempt_guard_records_and_locks_email(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client

    for _ in range(5):
        response = client.post(
            "/auth/login",
            json={"email": "missing@example.com", "password": "wrong-secret"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid credentials"

    locked_response = client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "wrong-secret"},
    )
    assert locked_response.status_code == 429
    assert locked_response.json()["detail"] == "too many failed login attempts"

    async def auth_attempts() -> tuple[list[str], list[str | None], list[str]]:
        async with session_factory() as session:
            attempt_result = await session.execute(
                select(AuthAttempt.outcome, AuthAttempt.reason)
                .where(AuthAttempt.email == "missing@example.com")
                .order_by(AuthAttempt.created_at)
            )
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(AuditEvent.tenant_id == "platform", AuditEvent.event_type.like("auth.login.%"))
                .order_by(AuditEvent.created_at)
            )
            attempts = list(attempt_result.all())
            return (
                [row.outcome for row in attempts],
                [row.reason for row in attempts],
                list(audit_result.scalars().all()),
            )

    outcomes, reasons, audit_events = asyncio.run(auth_attempts())
    assert outcomes == ["failure", "failure", "failure", "failure", "failure", "locked"]
    assert reasons[-1] == "too_many_failed_attempts"
    assert audit_events.count("auth.login.failed") == 5
    assert audit_events.count("auth.login.locked") == 1


def test_auth_session_listing_is_tenant_admin_scoped_and_redacted(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_a_response = client.post(
        "/tenants",
        json={"slug": "auth-sessions-a", "name": "Auth Sessions A"},
        headers=owner_headers,
    )
    assert tenant_a_response.status_code == 201
    tenant_a_id = tenant_a_response.json()["id"]

    tenant_b_response = client.post(
        "/tenants",
        json={"slug": "auth-sessions-b", "name": "Auth Sessions B"},
        headers=owner_headers,
    )
    assert tenant_b_response.status_code == 201
    tenant_b_id = tenant_b_response.json()["id"]

    owner_a_response = client.post(
        "/users",
        json={"email": "session-owner-a@example.com", "display_name": "Session Owner A", "password": "correct-horse-a"},
        headers=owner_headers,
    )
    assert owner_a_response.status_code == 201
    owner_a_id = owner_a_response.json()["id"]

    viewer_a_response = client.post(
        "/users",
        json={"email": "session-viewer-a@example.com", "display_name": "Session Viewer A", "password": "correct-horse-b"},
        headers=owner_headers,
    )
    assert viewer_a_response.status_code == 201
    viewer_a_id = viewer_a_response.json()["id"]

    owner_b_response = client.post(
        "/users",
        json={"email": "session-owner-b@example.com", "display_name": "Session Owner B", "password": "correct-horse-c"},
        headers=owner_headers,
    )
    assert owner_b_response.status_code == 201
    owner_b_id = owner_b_response.json()["id"]

    assert client.post(
        f"/tenants/{tenant_a_id}/memberships",
        json={"user_id": owner_a_id, "role": "owner"},
        headers=owner_headers,
    ).status_code == 201
    assert client.post(
        f"/tenants/{tenant_a_id}/memberships",
        json={"user_id": viewer_a_id, "role": "viewer"},
        headers=owner_headers,
    ).status_code == 201
    assert client.post(
        f"/tenants/{tenant_b_id}/memberships",
        json={"user_id": owner_b_id, "role": "owner"},
        headers=owner_headers,
    ).status_code == 201

    owner_a_login = client.post(
        "/auth/login",
        json={"email": "session-owner-a@example.com", "password": "correct-horse-a"},
    )
    assert owner_a_login.status_code == 200
    owner_a_token = owner_a_login.json()["access_token"]

    viewer_a_login = client.post(
        "/auth/login",
        json={"email": "session-viewer-a@example.com", "password": "correct-horse-b"},
    )
    assert viewer_a_login.status_code == 200
    viewer_a_token = viewer_a_login.json()["access_token"]

    owner_b_login = client.post(
        "/auth/login",
        json={"email": "session-owner-b@example.com", "password": "correct-horse-c"},
    )
    assert owner_b_login.status_code == 200
    owner_b_token = owner_b_login.json()["access_token"]

    viewer_sessions_response = client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {viewer_a_token}"},
    )
    assert viewer_sessions_response.status_code == 403
    assert viewer_sessions_response.json()["detail"] == "permission required: auth_session:read"

    pre_revoke_sessions_response = client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {owner_a_token}"},
    )
    assert pre_revoke_sessions_response.status_code == 200
    pre_revoke_sessions = pre_revoke_sessions_response.json()
    viewer_a_session = next(
        session for session in pre_revoke_sessions if session["user_email"] == "session-viewer-a@example.com"
    )

    viewer_revoke_response = client.post(
        f"/auth/sessions/{viewer_a_session['token_id']}/revoke",
        headers={"Authorization": f"Bearer {viewer_a_token}"},
    )
    assert viewer_revoke_response.status_code == 403
    assert viewer_revoke_response.json()["detail"] == "permission required: auth_session:write"

    async def token_id_for_user(user_id: str) -> str:
        async with session_factory() as session:
            result = await session.execute(select(AccessToken.id).where(AccessToken.user_id == user_id))
            return result.scalar_one()

    owner_b_token_id = asyncio.run(token_id_for_user(owner_b_id))
    cross_tenant_revoke_response = client.post(
        f"/auth/sessions/{owner_b_token_id}/revoke",
        headers={"Authorization": f"Bearer {owner_a_token}"},
    )
    assert cross_tenant_revoke_response.status_code == 404
    assert cross_tenant_revoke_response.json()["detail"] == "auth session not found"

    revoke_viewer_response = client.post(
        f"/auth/sessions/{viewer_a_session['token_id']}/revoke",
        headers={"Authorization": f"Bearer {owner_a_token}"},
    )
    assert revoke_viewer_response.status_code == 200
    assert revoke_viewer_response.json()["revoked"] is True
    assert revoke_viewer_response.json()["token_id"] == viewer_a_session["token_id"]
    assert revoke_viewer_response.json()["status"] == "revoked"

    revoked_viewer_me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {viewer_a_token}"},
    )
    assert revoked_viewer_me_response.status_code == 401

    sessions_response = client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {owner_a_token}"},
    )
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()

    statuses_by_email: dict[str, set[str]] = {}
    tenant_ids_by_email: dict[str, set[str]] = {}
    for session in sessions:
        statuses_by_email.setdefault(session["user_email"], set()).add(session["status"])
        tenant_ids_by_email.setdefault(session["user_email"], set()).update(session["tenant_ids"])

    assert "active" in statuses_by_email["session-owner-a@example.com"]
    assert "revoked" in statuses_by_email["session-viewer-a@example.com"]
    assert "session-owner-b@example.com" not in statuses_by_email
    assert tenant_ids_by_email["session-owner-a@example.com"] == {tenant_a_id}
    assert tenant_ids_by_email["session-viewer-a@example.com"] == {tenant_a_id}

    serialized = json.dumps(sessions).lower()
    assert "access_token" not in serialized
    assert "token_hash" not in serialized
    assert owner_a_token.lower() not in serialized
    assert viewer_a_token.lower() not in serialized
    assert owner_b_token.lower() not in serialized

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_auth_sessions{status="active"} 2' in metrics_response.text
    assert 'drivedesk_auth_sessions{status="revoked"} 1' in metrics_response.text
    assert 'drivedesk_auth_attempts_total{outcome="success"} 3' in metrics_response.text
    assert "session-owner-a@example.com" not in metrics_response.text
    assert "token_id" not in metrics_response.text
    assert "token_hash" not in metrics_response.text

    async def admin_revoke_audit() -> list[str]:
        async with session_factory() as session:
            result = await session.execute(
                select(AuditEvent.event_type)
                .where(AuditEvent.tenant_id == "platform", AuditEvent.event_type == "auth.token.admin_revoked")
                .order_by(AuditEvent.created_at)
            )
            return list(result.scalars().all())

    assert asyncio.run(admin_revoke_audit()) == ["auth.token.admin_revoked"]


def test_bearer_token_is_limited_to_member_tenants(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_a_response = client.post(
        "/tenants",
        json={"slug": "tenant-a", "name": "Tenant A"},
        headers=owner_headers,
    )
    assert tenant_a_response.status_code == 201
    tenant_a_id = tenant_a_response.json()["id"]

    tenant_b_response = client.post(
        "/tenants",
        json={"slug": "tenant-b", "name": "Tenant B"},
        headers=owner_headers,
    )
    assert tenant_b_response.status_code == 201
    tenant_b_id = tenant_b_response.json()["id"]

    user_a_response = client.post(
        "/users",
        json={"email": "owner-a@example.com", "display_name": "Owner A", "password": "correct-horse-a"},
        headers=owner_headers,
    )
    assert user_a_response.status_code == 201
    user_a_id = user_a_response.json()["id"]

    user_b_response = client.post(
        "/users",
        json={"email": "viewer-b@example.com", "display_name": "Viewer B", "password": "correct-horse-b"},
        headers=owner_headers,
    )
    assert user_b_response.status_code == 201
    user_b_id = user_b_response.json()["id"]

    membership_a_response = client.post(
        f"/tenants/{tenant_a_id}/memberships",
        json={"user_id": user_a_id, "role": "owner"},
        headers=owner_headers,
    )
    assert membership_a_response.status_code == 201

    membership_b_response = client.post(
        f"/tenants/{tenant_b_id}/memberships",
        json={"user_id": user_b_id, "role": "viewer"},
        headers=owner_headers,
    )
    assert membership_b_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": "owner-a@example.com", "password": "correct-horse-a"},
    )
    assert login_response.status_code == 200
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    tenants_response = client.get("/tenants", headers=auth_headers)
    assert tenants_response.status_code == 200
    assert [tenant["id"] for tenant in tenants_response.json()] == [tenant_a_id]

    users_response = client.get("/users", headers=auth_headers)
    assert users_response.status_code == 200
    assert {user["id"] for user in users_response.json()} == {user_a_id}

    tenant_b_read_response = client.get(f"/tenants/{tenant_b_id}", headers=auth_headers)
    assert tenant_b_read_response.status_code == 403
    assert tenant_b_read_response.json()["detail"] == "tenant membership required"

    tenant_b_memberships_response = client.get(f"/tenants/{tenant_b_id}/memberships", headers=auth_headers)
    assert tenant_b_memberships_response.status_code == 403
    assert tenant_b_memberships_response.json()["detail"] == "tenant membership required"

    create_tenant_response = client.post(
        "/tenants",
        json={"slug": "bearer-created", "name": "Bearer Created"},
        headers=auth_headers,
    )
    assert create_tenant_response.status_code == 403
    assert create_tenant_response.json()["detail"] == "platform bootstrap context required"

    create_user_response = client.post(
        "/users",
        json={"email": "global@example.com", "display_name": "Global User", "password": "correct-horse-c"},
        headers=auth_headers,
    )
    assert create_user_response.status_code == 403
    assert create_user_response.json()["detail"] == "platform bootstrap context required"


def test_platform_admin_grant_enables_bearer_platform_operations(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_response = client.post(
        "/tenants",
        json={"slug": "platform-admin-seed", "name": "Platform Admin Seed"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    tenant_owner_response = client.post(
        "/users",
        json={"email": "tenant-owner@example.com", "display_name": "Tenant Owner", "password": "correct-horse-a"},
        headers=owner_headers,
    )
    assert tenant_owner_response.status_code == 201
    tenant_owner_id = tenant_owner_response.json()["id"]

    platform_user_response = client.post(
        "/users",
        json={
            "email": "platform-admin@example.com",
            "display_name": "Platform Admin",
            "password": "correct-horse-b",
        },
        headers=owner_headers,
    )
    assert platform_user_response.status_code == 201
    platform_user_id = platform_user_response.json()["id"]

    assert client.post(
        f"/tenants/{tenant_id}/memberships",
        json={"user_id": tenant_owner_id, "role": "owner"},
        headers=owner_headers,
    ).status_code == 201

    tenant_owner_login = client.post(
        "/auth/login",
        json={"email": "tenant-owner@example.com", "password": "correct-horse-a"},
    )
    assert tenant_owner_login.status_code == 200
    tenant_owner_headers = {"Authorization": f"Bearer {tenant_owner_login.json()['access_token']}"}

    forbidden_grant_response = client.post(
        "/platform/admins",
        json={"user_id": platform_user_id},
        headers=tenant_owner_headers,
    )
    assert forbidden_grant_response.status_code == 403
    assert forbidden_grant_response.json()["detail"] == "platform bootstrap context required"

    grant_response = client.post(
        "/platform/admins",
        json={"user_id": platform_user_id},
        headers=owner_headers,
    )
    assert grant_response.status_code == 201
    assert grant_response.json()["role"] == "platform_admin"
    assert grant_response.json()["status"] == "active"

    platform_login = client.post(
        "/auth/login",
        json={"email": "platform-admin@example.com", "password": "correct-horse-b"},
    )
    assert platform_login.status_code == 200
    platform_headers = {"Authorization": f"Bearer {platform_login.json()['access_token']}"}

    me_response = client.get("/auth/me", headers=platform_headers)
    assert me_response.status_code == 200
    assert me_response.json()["platform_roles"] == ["platform_admin"]

    platform_sessions_response = client.get("/auth/sessions", headers=platform_headers)
    assert platform_sessions_response.status_code == 200
    tenant_owner_session = next(
        session for session in platform_sessions_response.json() if session["user_email"] == "tenant-owner@example.com"
    )

    platform_revoke_response = client.post(
        f"/auth/sessions/{tenant_owner_session['token_id']}/revoke",
        headers=platform_headers,
    )
    assert platform_revoke_response.status_code == 200
    assert platform_revoke_response.json()["token_id"] == tenant_owner_session["token_id"]

    revoked_tenant_owner_me_response = client.get("/auth/me", headers=tenant_owner_headers)
    assert revoked_tenant_owner_me_response.status_code == 401

    bearer_grants_response = client.get("/platform/admins", headers=platform_headers)
    assert bearer_grants_response.status_code == 200
    assert [grant["user_id"] for grant in bearer_grants_response.json()] == [platform_user_id]

    created_tenant_response = client.post(
        "/tenants",
        json={"slug": "platform-created", "name": "Platform Created"},
        headers=platform_headers,
    )
    assert created_tenant_response.status_code == 201

    created_user_response = client.post(
        "/users",
        json={
            "email": "platform-created@example.com",
            "display_name": "Platform Created User",
            "password": "correct-horse-c",
        },
        headers=platform_headers,
    )
    assert created_user_response.status_code == 201

    platform_tenants_response = client.get("/tenants", headers=platform_headers)
    assert platform_tenants_response.status_code == 200
    assert {tenant["slug"] for tenant in platform_tenants_response.json()} >= {
        "platform-admin-seed",
        "platform-created",
    }

    platform_users_response = client.get("/users", headers=platform_headers)
    assert platform_users_response.status_code == 200
    assert {user["email"] for user in platform_users_response.json()} >= {
        "tenant-owner@example.com",
        "platform-admin@example.com",
        "platform-created@example.com",
    }

    async def platform_admin_state() -> tuple[list[str], list[str], list[str]]:
        async with session_factory() as session:
            admin_result = await session.execute(select(PlatformAdmin.role).order_by(PlatformAdmin.created_at))
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(AuditEvent.tenant_id == "platform")
                .order_by(AuditEvent.created_at)
            )
            outbox_result = await session.execute(
                select(OutboxEvent.event_type)
                .where(OutboxEvent.tenant_id == "platform")
                .order_by(OutboxEvent.created_at)
            )
            return (
                list(admin_result.scalars().all()),
                list(audit_result.scalars().all()),
                list(outbox_result.scalars().all()),
            )

    platform_roles, platform_audit_events, platform_outbox_events = asyncio.run(platform_admin_state())
    assert platform_roles == ["platform_admin"]
    assert "platform_admin.granted" in platform_audit_events
    assert "auth.token.admin_revoked" in platform_audit_events
    assert "platform_admin.granted" in platform_outbox_events


def test_public_demo_endpoint_is_read_only_synthetic_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    response = client.get("/demo/public")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["cache-control"] == "public, max-age=60"
    payload = response.json()
    assert payload["schemaVersion"] == 1
    assert payload["dataSource"] == "api.synthetic"
    assert payload["apiContract"]["path"] == "/demo/public"
    assert payload["apiContract"]["data_profile"] == "synthetic_demo_data"
    assert payload["tenant"]["slug"] == "demo-academy"
    assert payload["workflow"]["id"] == "wf-demo-lead-to-student"
    assert payload["workflow"]["currentStage"] == "student_sync"
    assert len(payload["workflow"]["stages"]) >= 5
    assert len(payload["timeline"]) >= 5
    assert len(payload["domainEvents"]) >= 4
    assert {event["event"] for event in payload["domainEvents"]} >= {
        "lead.created",
        "student.created",
        "contract.generated",
        "student.sync.requested",
    }
    assert len(payload["metrics"]) >= 4
    assert len(payload["workQueue"]) >= 4
    assert len(payload["adapterScenarios"]) >= 4
    adapter_scenario_by_id = {scenario["id"]: scenario for scenario in payload["adapterScenarios"]}
    assert set(adapter_scenario_by_id) >= {
        "adapter-file-import-preview",
        "adapter-file-import-execute",
        "adapter-accounting-export-retry",
        "adapter-dead-letter-review",
    }
    assert {scenario["phase"] for scenario in payload["adapterScenarios"]} >= {
        "preview",
        "execute",
        "retry",
        "operator_review",
    }
    assert {scenario["requiredScope"] for scenario in payload["adapterScenarios"]} >= {
        "file_import:preview",
        "file_import:execute",
        "accounting:export",
    }
    assert len(payload["integrationJobs"]) >= 3
    assert len(payload["integrationHealth"]) >= 4
    assert payload["businessScenarioReplay"]["status"] == "validated"
    assert payload["businessScenarioReplay"]["command"] == (
        "bash scripts/check_public_business_scenario_replay.sh"
    )
    assert {item["id"] for item in payload["businessScenarioReplay"]["scenarios"]} == {
        "crm-bank-payment-mismatch",
        "support-sla-risk",
        "procurement-delay-risk",
    }
    assert {route["name"] for route in payload["alertRouting"]["routes"]} >= {
        "platform-critical-page",
        "platform-warning-ticket",
        "scheduled-validation-notice",
    }
    assert {binding["alert"] for binding in payload["alertRouting"]["bindings"]} >= {
        "DriveDeskApiTargetDown",
        "DriveDeskIntegrationDeadLetters",
        "DriveDeskScheduledValidationMissed",
    }
    assert {binding["state"] for binding in payload["alertRouting"]["bindings"]} == {"routed"}
    assert {incident["status"] for incident in payload["incidentResponse"]["incidents"]} >= {
        "open",
        "acknowledged",
        "resolved",
    }
    assert {incident["alert"] for incident in payload["incidentResponse"]["incidents"]} >= {
        "DriveDeskApiHighLatencyP95",
        "DriveDeskIntegrationDeadLetters",
        "DriveDeskScheduledValidationMissed",
    }
    assert {event["event"] for event in payload["incidentResponse"]["timeline"]} >= {
        "alert.fired",
        "integration.incident.status_changed",
        "incident.resolved",
    }
    assert payload["engineeringProof"]["milestone"] == "engineering_70"
    assert payload["engineeringProof"]["status"] == "validated"
    assert len(payload["engineeringProof"]["summary"]) >= 4
    assert {gate["name"] for gate in payload["engineeringProof"]["gates"]} >= {
        "Core smoke",
        "Public demo API",
        "Backup and restore",
        "Release safety",
        "GitOps and IaC",
    }
    gate_by_name = {gate["name"]: gate for gate in payload["engineeringProof"]["gates"]}
    assert gate_by_name["Core smoke"]["command"] == "bash scripts/ci_smoke_public.sh"
    assert any(
        item["path"] == "docs/public/SYSTEM_REVIEW_PATH.md"
        for item in payload["engineeringProof"]["evidence"]
    )
    assert {job["status"] for job in payload["integrationJobs"]} >= {"processed", "retry", "dead_letter"}

    serialized = json.dumps(payload).lower()
    assert "land" "vps" not in serialized
    assert "auto" "school54" not in serialized
    assert "password" not in serialized


def test_connector_fixture_replay_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    replay_response = client.get("/demo/connector-fixture-replay")

    assert replay_response.status_code == 200
    assert replay_response.headers["access-control-allow-origin"] == "*"
    assert replay_response.headers["cache-control"] == "public, max-age=60"
    replay_payload = replay_response.json()
    assert replay_payload == public_response.json()["connectorFixtureReplay"]
    assert replay_payload["status"] == "validated"
    assert replay_payload["command"] == "bash scripts/check_public_connector_fixture_replay.sh"
    assert replay_payload["fixtureFile"] == "examples/connector-fixtures/replay-fixtures.sanitized.json"
    assert replay_payload["evidenceFile"] == (
        "docs/public/evidence/connector-fixture-replay.sanitized.json"
    )
    assert {item["group"] for item in replay_payload["outcomes"]} == {
        "happy_path_preview",
        "sensitive_payload_redaction",
        "invalid_payload",
        "retryable_provider_failure",
        "dead_letter_provider_failure",
        "reconciliation_mismatch",
    }
    assert {item["name"] for item in replay_payload["boundaries"]} >= {
        "raw payload",
        "credentials",
        "external calls",
        "persistence",
    }


def test_connector_certification_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    certification_response = client.get("/demo/connector-certification")

    assert certification_response.status_code == 200
    assert certification_response.headers["access-control-allow-origin"] == "*"
    assert certification_response.headers["cache-control"] == "public, max-age=60"
    certification_payload = certification_response.json()
    assert certification_payload == public_response.json()["connectorCertification"]
    assert certification_payload["status"] == "validated"
    assert certification_payload["command"] == "GET /demo/connector-certification"
    assert certification_payload["certificationLevel"] == "public_contract_certified"
    assert certification_payload["adapterCount"] >= 3
    assert certification_payload["privateReadyCount"] >= 2
    providers = {item["adapterKey"]: item for item in certification_payload["providerProfiles"]}
    assert {"crm.bitrix24.mock", "accounting.export.mock", "file.import.fake"}.issubset(providers)
    assert providers["crm.bitrix24.mock"]["serverSecretBoundary"] is True
    assert providers["crm.bitrix24.mock"]["readyForPrivateConnector"] is True
    assert {item["gate"] for item in certification_payload["certificationGates"]} == {
        "no_real_provider_call",
        "no_secret_value",
        "no_raw_payload",
        "idempotent_execution",
        "operator_review",
    }
    assert {item["externalMutation"] for item in certification_payload["certificationGates"]} == {
        False
    }


def test_provider_onboarding_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    onboarding_response = client.get("/demo/provider-onboarding")

    assert onboarding_response.status_code == 200
    assert onboarding_response.headers["access-control-allow-origin"] == "*"
    assert onboarding_response.headers["cache-control"] == "public, max-age=60"
    onboarding_payload = onboarding_response.json()
    assert onboarding_payload == public_response.json()["providerOnboarding"]
    assert onboarding_payload["status"] == "previewed"
    assert onboarding_payload["command"] == "GET /demo/provider-onboarding"
    assert onboarding_payload["onboardingLevel"] == "sandbox_onboarding_ready"
    assert onboarding_payload["providerKey"] == "crm.bitrix24.mock"
    assert onboarding_payload["providerCategory"] == "crm"
    assert set(onboarding_payload["providerProfile"]["operationKeys"]) >= {
        "crm_deal_intake_preview",
        "crm_deal_ingest_execute",
    }
    assert onboarding_payload["mappingPreview"]["recordsAccepted"] == 2
    assert onboarding_payload["mappingPreview"]["recordsRejected"] == 0
    assert onboarding_payload["mappingPreview"]["rawPayloadIncluded"] is False
    assert onboarding_payload["mappingPreview"]["containsPii"] is False
    assert set(onboarding_payload["mappingPreview"]["droppedSensitiveKeys"]) >= {
        "ACCESS_TOKEN",
        "CLIENT_NAME",
        "EMAIL",
        "PHONE",
        "SECRET",
    }
    assert {item["check"] for item in onboarding_payload["preflightChecks"]} >= {
        "adapter_registered",
        "connection_scopes_available",
        "mapping_profile_valid",
        "secret_refs_server_side",
        "provider_call_disabled",
    }
    assert onboarding_payload["sandboxContract"]["providerCallEnabled"] is False
    assert onboarding_payload["sandboxContract"]["externalMutation"] is False
    assert {item["step"] for item in onboarding_payload["rolloutPlan"]} == {
        "create_tenant_connection",
        "run_mapping_preview",
        "run_fixture_replay",
        "enable_private_dry_run",
        "request_write_unlock",
        "monitor_and_reconcile",
    }
    assert {item["name"] for item in onboarding_payload["dataBoundaries"]} == {
        "public_onboarding_payload",
        "server_secret_store",
        "browser_session",
        "private_provider_runtime",
    }


def test_business_scenario_replay_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    replay_response = client.get("/demo/business-scenario-replay")

    assert replay_response.status_code == 200
    assert replay_response.headers["access-control-allow-origin"] == "*"
    assert replay_response.headers["cache-control"] == "public, max-age=60"
    replay_payload = replay_response.json()
    assert replay_payload == public_response.json()["businessScenarioReplay"]
    assert replay_payload["status"] == "validated"
    assert replay_payload["command"] == "bash scripts/check_public_business_scenario_replay.sh"
    assert {item["id"] for item in replay_payload["scenarios"]} == {
        "crm-bank-payment-mismatch",
        "support-sla-risk",
        "procurement-delay-risk",
    }
    assert {item["stage"] for item in replay_payload["flow"]} == {
        "signal",
        "normalize",
        "detect",
        "plan",
        "execute",
    }
    assert any(
        item["path"] == "docs/public/BUSINESS_SCENARIO_REPLAY.md"
        for item in replay_payload["docs"]
    )


def test_business_intake_pipeline_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    pipeline_response = client.get("/demo/business-intake-pipeline")

    assert pipeline_response.status_code == 200
    assert pipeline_response.headers["access-control-allow-origin"] == "*"
    assert pipeline_response.headers["cache-control"] == "public, max-age=60"
    pipeline_payload = pipeline_response.json()
    assert pipeline_payload == public_response.json()["businessIntakePipeline"]
    assert pipeline_payload["status"] == "previewed"
    assert pipeline_payload["command"] == "POST /tenants/{tenant_id}/business-intake-pipeline/preview"
    assert pipeline_payload["sourceSystems"] == [
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    ]
    assert {item["providerKey"] for item in pipeline_payload["intakePreviews"]} == {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
    }
    assert pipeline_payload["detections"]["status"] == "detected"
    assert pipeline_payload["detections"]["detectedExceptions"][0]["exceptionType"] == "crm_payment_mismatch"
    assert {item["name"] for item in pipeline_payload["dataBoundaries"]} == {
        "no_external_calls",
        "no_persistence",
        "secret_and_pii_boundary",
    }
    assert any(
        item["path"] == "docs/public/BUSINESS_INTAKE_PIPELINE.md"
        for item in pipeline_payload["docs"]
    )


def test_business_task_handoff_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    handoff_response = client.get("/demo/business-task-handoff")

    assert handoff_response.status_code == 200
    assert handoff_response.headers["access-control-allow-origin"] == "*"
    assert handoff_response.headers["cache-control"] == "public, max-age=60"
    handoff_payload = handoff_response.json()
    assert handoff_payload == public_response.json()["businessTaskHandoff"]
    assert handoff_payload["status"] == "previewed"
    assert handoff_payload["command"] == "POST /tenants/{tenant_id}/business-task-handoffs/preview"
    assert handoff_payload["role"] == "accountant"
    assert handoff_payload["subject"] == "deal:DEAL-2026-001"
    assert {item["status"] for item in handoff_payload["taskCards"]} == {"would_create"}
    assert {item["wouldCreate"] for item in handoff_payload["taskCards"]} == {"BusinessRecord(type=task)"}
    assert {item["externalMutation"] for item in handoff_payload["taskCards"]} == {False}
    assert {item["containsPii"] for item in handoff_payload["taskCards"]} == {False}
    assert {item["eventType"] for item in handoff_payload["outboxCandidates"]} == {"task.created"}
    assert {item["adapterKey"] for item in handoff_payload["outboxCandidates"]} == {"internal.noop"}
    assert {item["status"] for item in handoff_payload["outboxCandidates"]} == {"would_enqueue"}
    assert {item["externalMutation"] for item in handoff_payload["outboxCandidates"]} == {False}
    assert {item["status"] for item in handoff_payload["notificationDrafts"]} == {"draft_only"}
    assert {item["externalDelivery"] for item in handoff_payload["notificationDrafts"]} == {False}
    assert {item["gate"] for item in handoff_payload["approvalGates"]} == {
        "task_creation_review",
        "external_write_gate",
        "repair_action_approval",
    }
    assert {item["name"] for item in handoff_payload["dataBoundaries"]} == {
        "preview_only_no_persistence",
        "internal_only_outbox",
        "safe_task_payload",
    }
    assert any(
        item["path"] == "docs/public/BUSINESS_TASK_HANDOFF.md"
        for item in handoff_payload["docs"]
    )


def test_business_notification_channels_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    matrix_response = client.get("/demo/business-notification-channels")

    assert matrix_response.status_code == 200
    assert matrix_response.headers["access-control-allow-origin"] == "*"
    assert matrix_response.headers["cache-control"] == "public, max-age=60"
    matrix_payload = matrix_response.json()
    assert matrix_payload == public_response.json()["businessNotificationChannels"]
    assert matrix_payload["status"] == "previewed"
    assert (
        matrix_payload["command"]
        == "POST /tenants/{tenant_id}/business-notification-channels/preview"
    )
    assert matrix_payload["role"] == "accountant"
    assert matrix_payload["subject"] == "deal:DEAL-2026-001"
    channel_by_key = {item["channel"]: item for item in matrix_payload["channels"]}
    assert set(channel_by_key) == {"in_app", "telegram", "email", "sms", "webhook"}
    assert channel_by_key["in_app"]["status"] == "ready"
    assert channel_by_key["in_app"]["configured"] is True
    assert channel_by_key["in_app"]["externalDelivery"] is False
    assert {
        channel_by_key[channel]["requiresSecret"]
        for channel in ["telegram", "email", "sms", "webhook"]
    } == {True}
    assert {
        channel_by_key[channel]["requiresPrivateConnector"]
        for channel in ["telegram", "email", "sms", "webhook"]
    } == {True}
    assert {item["externalDelivery"] for item in matrix_payload["channels"]} == {False}
    assert {item["containsPii"] for item in matrix_payload["channels"]} == {False}
    assert len(matrix_payload["deliveryDrafts"]) == 5
    assert {item["wouldEnqueueEvent"] for item in matrix_payload["deliveryDrafts"]} == {
        "notification.delivery.requested"
    }
    assert {item["externalDelivery"] for item in matrix_payload["deliveryDrafts"]} == {False}
    assert {item["gate"] for item in matrix_payload["approvalGates"]} == {
        "notification_content_review",
        "private_channel_secret_setup",
        "external_delivery_gate",
    }
    assert {item["name"] for item in matrix_payload["dataBoundaries"]} == {
        "preview_only_no_delivery",
        "server_secret_store_boundary",
        "safe_notification_payload",
    }
    assert any(
        item["path"] == "docs/public/BUSINESS_NOTIFICATION_CHANNELS.md"
        for item in matrix_payload["docs"]
    )


def test_notification_delivery_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    delivery_response = client.get("/demo/notification-delivery")

    assert delivery_response.status_code == 200
    assert delivery_response.headers["access-control-allow-origin"] == "*"
    assert delivery_response.headers["cache-control"] == "public, max-age=60"
    delivery_payload = delivery_response.json()
    assert delivery_payload == public_response.json()["notificationDelivery"]
    assert delivery_payload["status"] == "validated"
    assert delivery_payload["command"] == "GET /demo/notification-delivery"
    assert delivery_payload["deliveryLevel"] == "delivery_runtime_ready"
    assert delivery_payload["deliveryRuntime"] == "outbox_worker_provider_gate"
    assert {item["channel"] for item in delivery_payload["adapterProfiles"]} == {
        "in_app",
        "telegram",
        "email",
        "sms",
        "webhook",
    }
    assert {item["providerCallEnabled"] for item in delivery_payload["adapterProfiles"]} == {False}
    assert {item["externalDelivery"] for item in delivery_payload["adapterProfiles"]} == {False}
    assert {item["eventType"] for item in delivery_payload["outboxEvents"]} == {
        "notification.delivery.requested"
    }
    assert {item["providerCallEnabled"] for item in delivery_payload["outboxEvents"]} == {False}
    assert {item["containsPii"] for item in delivery_payload["outboxEvents"]} == {False}
    assert {item["name"] for item in delivery_payload["retryPolicy"]} == {
        "short_retry",
        "dead_letter_after_exhaustion",
        "operator_review",
    }
    assert {item["name"] for item in delivery_payload["observability"]} >= {
        "drivedesk_notification_delivery_attempts_total",
        "DriveDeskNotificationDeadLetters",
    }
    assert delivery_payload["api"]["standalone"] == "GET /demo/notification-delivery"
    assert any(item["path"] == "docs/public/NOTIFICATION_DELIVERY.md" for item in delivery_payload["docs"])


def test_business_context_assistant_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    context_response = client.get("/demo/business-context-assistant")

    assert context_response.status_code == 200
    assert context_response.headers["access-control-allow-origin"] == "*"
    assert context_response.headers["cache-control"] == "public, max-age=60"
    context_payload = context_response.json()
    assert context_payload == public_response.json()["businessContextAssistant"]
    assert context_payload["status"] == "previewed"
    assert (
        context_payload["command"]
        == "POST /tenants/{tenant_id}/business-workbench-context/preview"
    )
    assert context_payload["role"] == "accountant"
    assert context_payload["subject"] == "deal:DEAL-2026-001"
    assert set(context_payload["sourceSystems"]) == {
        "crm.bitrix24.mock",
        "bank.statement.mock",
        "accounting.export.mock",
        "legal.reference.mock",
    }
    assert {item["systemFamily"] for item in context_payload["contextCards"]} == {
        "crm",
        "bank",
        "accounting",
        "legal",
    }
    assert {item["externalFetch"] for item in context_payload["contextCards"]} == {False}
    assert {item["externalMutation"] for item in context_payload["contextCards"]} == {False}
    assert {item["containsPii"] for item in context_payload["contextCards"]} == {False}
    assert {item["rawPayloadIncluded"] for item in context_payload["contextCards"]} == {False}
    assert {item["rule"] for item in context_payload["insightRules"]} == {
        "correlate_payment_evidence",
        "detect_accounting_export_gap",
        "attach_policy_reference",
    }
    assert {item["externalMutation"] for item in context_payload["insightRules"]} == {False}
    assert {item["action"] for item in context_payload["suggestedActions"]} == {
        "open_reconciliation_plan",
        "queue_accounting_export_after_review",
        "attach_policy_reference",
        "prepare_internal_notification",
    }
    assert {item["externalMutation"] for item in context_payload["suggestedActions"]} == {
        False
    }
    assert {item["name"] for item in context_payload["dataBoundaries"]} == {
        "read_only_context_preview",
        "no_raw_provider_payload",
        "secret_boundary",
        "legal_reference_link_only",
    }
    assert context_payload["api"]["standalone"] == "GET /demo/business-context-assistant"
    assert any(
        item["path"] == "docs/public/BUSINESS_CONTEXT_ASSISTANT.md"
        for item in context_payload["docs"]
    )


def test_business_action_execution_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    execution_response = client.get("/demo/business-action-execution")

    assert execution_response.status_code == 200
    assert execution_response.headers["access-control-allow-origin"] == "*"
    assert execution_response.headers["cache-control"] == "public, max-age=60"
    execution_payload = execution_response.json()
    assert execution_payload == public_response.json()["businessActionExecution"]
    assert execution_payload["status"] == "previewed"
    assert (
        execution_payload["command"]
        == "POST /tenants/{tenant_id}/business-action-executions/preview"
    )
    assert execution_payload["role"] == "accountant"
    assert execution_payload["subject"] == "deal:DEAL-2026-001"
    assert {item["action"] for item in execution_payload["executionPlan"]} == {
        "open_reconciliation_plan",
        "queue_accounting_export_after_review",
        "prepare_internal_notification",
    }
    assert {item["dryRun"] for item in execution_payload["executionPlan"]} == {True}
    assert {item["externalMutation"] for item in execution_payload["executionPlan"]} == {
        False
    }
    assert {item["containsPii"] for item in execution_payload["executionPlan"]} == {False}
    assert {item["rawPayloadIncluded"] for item in execution_payload["executionPlan"]} == {
        False
    }
    assert any(item["commitWouldMutateProvider"] for item in execution_payload["executionPlan"])
    assert any(item["safeToAutoRun"] is False for item in execution_payload["executionPlan"])
    assert {item["check"] for item in execution_payload["preflightChecks"]} == {
        "safe_payload_profile",
        "idempotency_key_ready",
        "approval_gate_attached",
        "connector_secret_boundary",
    }
    assert {item["wouldRecord"] for item in execution_payload["dryRunResults"]} == {
        "WorkflowActionRun"
    }
    assert {item["gate"] for item in execution_payload["approvalGates"]} == {
        "operator_review_gate",
        "external_write_gate",
        "idempotent_outbox_gate",
    }
    assert {item["step"] for item in execution_payload["rollbackPlan"]} == {
        "preview_has_no_rollback",
        "commit_uses_outbox_recovery",
    }
    assert {item["name"] for item in execution_payload["dataBoundaries"]} == {
        "dry_run_only",
        "no_provider_write",
        "safe_execution_payload",
        "audit_and_outbox_contract",
    }
    assert execution_payload["api"]["standalone"] == "GET /demo/business-action-execution"
    assert any(
        item["path"] == "docs/public/BUSINESS_ACTION_EXECUTION.md"
        for item in execution_payload["docs"]
    )


def test_business_approval_gateway_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    gateway_response = client.get("/demo/business-approval-gateway")

    assert gateway_response.status_code == 200
    assert gateway_response.headers["access-control-allow-origin"] == "*"
    assert gateway_response.headers["cache-control"] == "public, max-age=60"
    gateway_payload = gateway_response.json()
    assert gateway_payload == public_response.json()["businessApprovalGateway"]
    assert gateway_payload["status"] == "previewed"
    assert (
        gateway_payload["command"]
        == "POST /tenants/{tenant_id}/business-approval-gateway/preview"
    )
    assert gateway_payload["role"] == "accountant"
    assert gateway_payload["subject"] == "deal:DEAL-2026-001"
    assert {item["action"] for item in gateway_payload["approvalRequests"]} == {
        "queue_accounting_export_after_review",
    }
    assert {item["requesterRole"] for item in gateway_payload["approvalRequests"]} == {
        "accountant"
    }
    assert {item["approverRole"] for item in gateway_payload["approvalRequests"]} == {
        "owner"
    }
    assert {item["requiresDualControl"] for item in gateway_payload["approvalRequests"]} == {
        True
    }
    assert {
        item["commitWouldMutateProvider"] for item in gateway_payload["approvalRequests"]
    } == {True}
    assert {item["externalMutation"] for item in gateway_payload["approvalRequests"]} == {
        False
    }
    assert {item["check"] for item in gateway_payload["policyChecks"]} == {
        "rbac_approver_role",
        "dual_control_required",
        "idempotency_preserved",
        "provider_write_closed_until_approval",
    }
    assert {item["route"] for item in gateway_payload["approverRouting"]} == {
        "owner_or_accountant_review",
        "escalate_if_sla_missed",
    }
    assert {item["wouldRecord"] for item in gateway_payload["commitUnlocks"]} == {
        "WorkflowActionRun"
    }
    assert {item["providerWriteUnlocked"] for item in gateway_payload["commitUnlocks"]} == {
        False
    }
    assert {item["event"] for item in gateway_payload["auditTrail"]} == {
        "business_approval.requested",
        "business_approval.policy_checked",
        "business_approval.commit_unlocked",
    }
    assert {item["name"] for item in gateway_payload["dataBoundaries"]} == {
        "preview_only_no_approval_record",
        "provider_write_locked",
        "rbac_dual_control",
        "safe_approval_payload",
    }
    assert gateway_payload["api"]["standalone"] == "GET /demo/business-approval-gateway"
    assert any(
        item["path"] == "docs/public/BUSINESS_APPROVAL_GATEWAY.md"
        for item in gateway_payload["docs"]
    )


def test_integration_runtime_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    runtime_response = client.get("/demo/integration-runtime")

    assert runtime_response.status_code == 200
    assert runtime_response.headers["access-control-allow-origin"] == "*"
    assert runtime_response.headers["cache-control"] == "public, max-age=60"
    runtime_payload = runtime_response.json()
    assert runtime_payload == public_response.json()["integrationRuntime"]
    assert runtime_payload["status"] == "previewed"
    assert (
        runtime_payload["command"]
        == "POST /tenants/{tenant_id}/integration-runtime/preview"
    )
    assert runtime_payload["adapterKey"] == "accounting.export.mock"
    assert runtime_payload["operationKey"] == "accounting_export_execute"
    assert runtime_payload["executionMode"] == "contract_only"
    assert (
        runtime_payload["operationContract"]["eventType"]
        == "accounting.export.requested"
    )
    assert (
        runtime_payload["operationContract"]["requiredConnectionScope"]
        == "accounting:export"
    )
    assert {item["step"] for item in runtime_payload["runtimeSteps"]} >= {
        "contract_selected",
        "scope_preflight",
        "idempotency_prepared",
        "approval_dependency",
        "outbox_handoff",
        "worker_boundary",
        "reconciliation_plan",
    }
    assert {item["check"] for item in runtime_payload["preflightChecks"]} == {
        "adapter_registered",
        "operation_contract_present",
        "required_scope_available",
        "idempotency_keys_declared",
        "secret_boundary_server_side",
        "provider_write_disabled_in_preview",
    }
    assert runtime_payload["outboxHandoff"]["wouldEnqueueEvent"] == "accounting.export.requested"
    assert runtime_payload["outboxHandoff"]["providerCallEnabled"] is False
    assert runtime_payload["workerBoundary"]["publicRunMode"] == "contract_only"
    assert runtime_payload["workerBoundary"]["providerCallEnabled"] is False
    assert {item["route"] for item in runtime_payload["incidentRoutes"]} == {
        "retry_queue",
        "dead_letter_review",
        "reconciliation_mismatch",
    }
    assert {item["name"] for item in runtime_payload["dataBoundaries"]} == {
        "contract_only_preview",
        "server_side_secret_boundary",
        "safe_payload_boundary",
        "approval_before_provider_write",
    }
    assert runtime_payload["api"]["standalone"] == "GET /demo/integration-runtime"
    assert (
        runtime_payload["api"]["preview"]
        == "POST /tenants/{tenant_id}/integration-runtime/preview"
    )
    assert any(
        item["path"] == "docs/public/INTEGRATION_RUNTIME.md"
        for item in runtime_payload["docs"]
    )


def test_integration_execution_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    execution_response = client.get("/demo/integration-execution")

    assert execution_response.status_code == 200
    assert execution_response.headers["access-control-allow-origin"] == "*"
    assert execution_response.headers["cache-control"] == "public, max-age=60"
    execution_payload = execution_response.json()
    assert execution_payload == public_response.json()["integrationExecution"]
    assert execution_payload["status"] == "previewed"
    assert (
        execution_payload["command"]
        == "POST /tenants/{tenant_id}/integration-executions/preview"
    )
    assert execution_payload["adapterKey"] == "accounting.export.mock"
    assert execution_payload["operationKey"] == "accounting_export_execute"
    assert execution_payload["executionMode"] == "contract_only"
    assert execution_payload["runLedger"]["evidence"] == "integration_execution.run_ledger_prepared"
    assert execution_payload["runLedger"]["wouldCreateWorkflowActionRun"] is True
    assert execution_payload["runLedger"]["wouldCreateOutboxEvent"] is True
    assert execution_payload["runLedger"]["wouldCallProvider"] is False
    assert [item["stage"] for item in execution_payload["timeline"]] == [
        "request_accepted",
        "runtime_preflight",
        "approval_gate",
        "outbox_enqueue",
        "worker_dispatch",
        "provider_call",
        "reconciliation",
        "operator_closure",
    ]
    assert {item["stage"] for item in execution_payload["timeline"] if item["status"] == "blocked_in_public_preview"} == {
        "provider_call"
    }
    assert {(item["from"], item["to"]) for item in execution_payload["stateTransitions"]} >= {
        ("none", "requested"),
        ("requested", "preflight_passed"),
        ("preflight_passed", "queued"),
        ("queued", "awaiting_reconciliation"),
        ("awaiting_reconciliation", "operator_review_ready"),
    }
    assert {item["name"] for item in execution_payload["retryPolicy"]} == {
        "retry_queue",
        "dead_letter_review",
    }
    assert {item["name"] for item in execution_payload["reconciliationLinks"]} == {
        "expected_result",
        "provider_evidence",
        "mismatch_route",
    }
    assert {item["metric"] for item in execution_payload["observability"]} >= {
        "drivedesk_workflow_action_runs",
        "drivedesk_outbox_events",
        "drivedesk_integration_reconciliations",
        "drivedesk_integration_incidents",
    }
    assert {item["name"] for item in execution_payload["dataBoundaries"]} == {
        "preview_only_execution",
        "idempotency_without_payload",
        "provider_result_redaction",
        "operator_review_before_mutation",
    }
    assert execution_payload["api"]["standalone"] == "GET /demo/integration-execution"
    assert (
        execution_payload["api"]["preview"]
        == "POST /tenants/{tenant_id}/integration-executions/preview"
    )
    assert any(
        item["path"] == "docs/public/INTEGRATION_EXECUTION.md"
        for item in execution_payload["docs"]
    )


def test_integration_repair_demo_endpoint_exposes_same_public_contract(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client

    public_response = client.get("/demo/public")
    repair_response = client.get("/demo/integration-repair")

    assert repair_response.status_code == 200
    assert repair_response.headers["access-control-allow-origin"] == "*"
    assert repair_response.headers["cache-control"] == "public, max-age=60"
    repair_payload = repair_response.json()
    assert repair_payload == public_response.json()["integrationRepair"]
    assert repair_payload["status"] == "previewed"
    assert repair_payload["command"] == "GET /demo/integration-repair"
    assert repair_payload["repairLevel"] == "operator_repair_ready"
    assert repair_payload["incidentCount"] == 3
    assert repair_payload["criticalCount"] == 2
    assert repair_payload["safeActionCount"] == 1
    assert {f"{item['sourceType']}:{item['sourceStatus']}" for item in repair_payload["incidentMatrix"]} == {
        "outbox_event:retry",
        "outbox_event:dead_letter",
        "reconciliation:mismatched",
    }
    assert {item["providerCallEnabled"] for item in repair_payload["incidentMatrix"]} == {False}
    assert {item["externalMutation"] for item in repair_payload["incidentMatrix"]} == {False}
    assert {item["runbookKey"] for item in repair_payload["repairRunbooks"]} == {
        "integration.retry_backlog",
        "integration.dead_letter",
        "integration.reconciliation_mismatch",
    }
    assert {item["area"] for item in repair_payload["impactAnalysis"]} == {
        "workflow_delivery",
        "financial_reconciliation",
        "operator_queue",
    }
    assert {item["action"] for item in repair_payload["repairActions"]} == {
        "run_connection_diagnostics",
        "retry_after_diagnostics",
        "fix_mapping_profile",
        "open_reconciliation_review",
    }
    assert [item["action"] for item in repair_payload["repairActions"] if item["safeToAutoRun"] is True] == [
        "run_connection_diagnostics"
    ]
    assert {item["providerCallEnabled"] for item in repair_payload["repairActions"]} == {False}
    assert {item["externalMutation"] for item in repair_payload["repairActions"]} == {False}
    assert {item["step"] for item in repair_payload["safeExecutionPlan"]} == {
        "classify_failure",
        "attach_business_impact",
        "prepare_safe_actions",
        "dry_run_first",
        "approval_before_commit",
        "observe_after_repair",
    }
    assert {item["name"] for item in repair_payload["dataBoundaries"]} == {
        "repair_preview_only",
        "safe_payload_summary",
        "approval_before_retry",
        "private_provider_boundary",
    }
    for field in ("externalMutation", "providerCallEnabled", "rawPayloadIncluded", "containsPii"):
        assert {item[field] for item in repair_payload["dataBoundaries"]} == {False}
    assert repair_payload["api"]["standalone"] == "GET /demo/integration-repair"
    assert any(
        item["path"] == "docs/public/INTEGRATION_REPAIR.md"
        for item in repair_payload["docs"]
    )


def test_integration_repair_preview_endpoint_prepares_safe_action(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_response = client.post(
        "/tenants",
        json={"slug": "repair-preview", "name": "Repair Preview"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    response = client.post(
        f"/tenants/{tenant_id}/integration-repairs/preview",
        json={
            "incident_id": "IR-001",
            "action": "run_connection_diagnostics",
            "operator_role": "operator",
            "include_postchecks": True,
        },
        headers=owner_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant_id
    assert payload["repair_kind"] == "operator_repair_action_preview"
    assert payload["incident_id"] == "IR-001"
    assert payload["action"] == "run_connection_diagnostics"
    assert payload["status"] == "previewed"
    assert payload["selected_incident"]["incident_id"] == "IR-001"
    assert payload["selected_action"]["action"] == "run_connection_diagnostics"
    assert payload["runbook"]["runbook_key"] == "integration.retry_backlog"
    assert {item["name"] for item in payload["preflight_checks"]} == {
        "incident_known",
        "action_matches_incident",
        "raw_payload_not_required",
        "provider_call_blocked",
    }
    assert payload["approval_gate"]["required"] is False
    assert payload["dry_run_result"]["would_run_diagnostics"] is True
    assert payload["dry_run_result"]["would_enqueue_outbox"] is False
    assert {item["name"] for item in payload["postchecks"]} == {
        "recheck_incident_status",
        "refresh_reconciliation",
        "record_operator_evidence",
    }
    assert payload["api"]["preview"] == "POST /tenants/{tenant_id}/integration-repairs/preview"
    for collection in (
        payload["preflight_checks"],
        payload["postchecks"],
        payload["data_boundaries"],
        payload["evidence"],
    ):
        assert {item["external_mutation"] for item in collection} == {False}
        assert {item["provider_call_enabled"] for item in collection} == {False}

    invalid_response = client.post(
        f"/tenants/{tenant_id}/integration-repairs/preview",
        json={"incident_id": "IR-001", "action": "fix_mapping_profile"},
        headers=owner_headers,
    )
    assert invalid_response.status_code == 400
    assert "not available" in invalid_response.json()["detail"]


def test_file_import_adapter_success_flow(api_client: tuple[TestClient, async_sessionmaker[AsyncSession]]) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_response = client.post(
        "/tenants",
        json={"slug": "adapter-success", "name": "Adapter Success"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Demo file import profile",
            "adapter_key": "file.import.fake",
            "config": {"mode": "synthetic"},
            "mapping": {"external_id": "lead_id", "display_name": "full_name"},
        },
        headers=owner_headers,
    )
    assert connection_response.status_code == 201
    connection = connection_response.json()
    assert connection["tenant_id"] == tenant_id
    assert connection["adapter_key"] == "file.import.fake"
    assert connection["status"] == "active"
    assert "lead_id" in connection["mapping_json"]
    assert json.loads(connection["scopes_json"]) == ["file_import:execute", "file_import:preview"]

    preview_response = client.post(
        f"/tenants/{tenant_id}/integration-mapping-preview",
        json={
            "adapter_key": "file.import.fake",
            "integration_connection_id": connection["id"],
            "records": [
                {"lead_id": "lead_preview_1", "full_name": "Preview One"},
                {"lead_id": "lead_preview_2", "full_name": ""},
            ],
        },
        headers={"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"},
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["adapter_key"] == "file.import.fake"
    assert preview["required_mapping_keys"] == ["external_id", "display_name"]
    assert preview["records_received"] == 2
    assert preview["records_accepted"] == 1
    assert preview["records_rejected"] == 1
    assert preview["records"][0]["status"] == "accepted"
    assert preview["records"][0]["normalized"] == {
        "external_id": "lead_preview_1",
        "display_name": "Preview One",
    }
    assert preview["records"][1]["status"] == "rejected"
    assert preview["records"][1]["errors"] == ["missing mapped value: display_name"]

    direct_preview_response = client.post(
        f"/tenants/{tenant_id}/integration-mapping-preview",
        json={
            "adapter_key": "file.import.fake",
            "mapping": {"external_id": "lead_id", "display_name": "full_name"},
            "records": [{"lead_id": "lead_direct_1", "full_name": "Direct Preview"}],
        },
        headers=owner_headers,
    )
    assert direct_preview_response.status_code == 200
    assert direct_preview_response.json()["records_accepted"] == 1

    noop_preview_response = client.post(
        f"/tenants/{tenant_id}/integration-mapping-preview",
        json={
            "adapter_key": "internal.noop",
            "records": [{"event_type": "demo"}],
        },
        headers=owner_headers,
    )
    assert noop_preview_response.status_code == 400
    assert noop_preview_response.json()["detail"] == "Adapter does not support integration mapping preview: internal.noop"

    invalid_scope_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Invalid scope file import profile",
            "adapter_key": "file.import.fake",
            "mapping": {"external_id": "lead_id", "display_name": "full_name"},
            "scopes": ["accounting:export"],
        },
        headers=owner_headers,
    )
    assert invalid_scope_response.status_code == 400
    assert invalid_scope_response.json()["detail"] == (
        "Unsupported connection scopes for file.import.fake: accounting:export"
    )

    preview_only_connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Preview-only file import profile",
            "adapter_key": "file.import.fake",
            "mapping": {"external_id": "lead_id", "display_name": "full_name"},
            "scopes": ["file_import:preview"],
        },
        headers=owner_headers,
    )
    assert preview_only_connection_response.status_code == 201
    preview_only_connection = preview_only_connection_response.json()
    assert json.loads(preview_only_connection["scopes_json"]) == ["file_import:preview"]

    execute_only_connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Execute-only file import profile",
            "adapter_key": "file.import.fake",
            "mapping": {"external_id": "lead_id", "display_name": "full_name"},
            "scopes": ["file_import:execute"],
        },
        headers=owner_headers,
    )
    assert execute_only_connection_response.status_code == 201
    execute_only_connection = execute_only_connection_response.json()
    assert json.loads(execute_only_connection["scopes_json"]) == ["file_import:execute"]

    preview_only_import_response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "integration_connection_id": preview_only_connection["id"],
            "source_name": "preview-only-profile",
            "source_format": "json",
            "records": [{"lead_id": "lead_preview_only", "full_name": "Preview Only"}],
        },
        headers=owner_headers,
    )
    assert preview_only_import_response.status_code == 409
    assert preview_only_import_response.json()["detail"] == (
        "Integration connection for file.import.fake lacks required scope: file_import:execute"
    )

    execute_only_preview_response = client.post(
        f"/tenants/{tenant_id}/integration-mapping-preview",
        json={
            "adapter_key": "file.import.fake",
            "integration_connection_id": execute_only_connection["id"],
            "records": [{"lead_id": "lead_execute_only", "full_name": "Execute Only"}],
        },
        headers=owner_headers,
    )
    assert execute_only_preview_response.status_code == 409
    assert execute_only_preview_response.json()["detail"] == (
        "Integration connection for file.import.fake lacks required scope: file_import:preview"
    )

    connections_response = client.get(
        f"/tenants/{tenant_id}/integration-connections",
        headers={"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"},
    )
    assert connections_response.status_code == 200
    assert {item["id"] for item in connections_response.json()} == {
        connection["id"],
        preview_only_connection["id"],
        execute_only_connection["id"],
    }

    manager_create_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={"name": "Manager cannot create", "adapter_key": "file.import.fake"},
        headers={"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"},
    )
    assert manager_create_response.status_code == 403
    assert manager_create_response.json()["detail"] == "permission required: tenant:write"

    unsupported_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={"name": "Unknown adapter", "adapter_key": "provider.unknown"},
        headers=owner_headers,
    )
    assert unsupported_response.status_code == 400
    assert unsupported_response.json()["detail"] == "Unknown adapter: provider.unknown"

    missing_mapping_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Incomplete file import profile",
            "adapter_key": "file.import.fake",
            "mapping": {"external_id": "lead_id"},
        },
        headers=owner_headers,
    )
    assert missing_mapping_response.status_code == 400
    assert missing_mapping_response.json()["detail"] == "Missing mapping keys for file.import.fake: display_name"

    invalid_mapping_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Invalid file import profile",
            "adapter_key": "file.import.fake",
            "mapping": {"external_id": "lead_id", "display_name": ""},
        },
        headers=owner_headers,
    )
    assert invalid_mapping_response.status_code == 400
    assert invalid_mapping_response.json()["detail"] == "Invalid mapping values for file.import.fake: display_name"

    noop_connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={"name": "Noop profile", "adapter_key": "internal.noop"},
        headers=owner_headers,
    )
    assert noop_connection_response.status_code == 400
    assert noop_connection_response.json()["detail"] == "Adapter does not support integration connections: internal.noop"

    disabled_connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Disabled file import profile",
            "adapter_key": "file.import.fake",
            "status": "disabled",
            "mapping": {"external_id": "lead_id", "display_name": "full_name"},
        },
        headers=owner_headers,
    )
    assert disabled_connection_response.status_code == 201
    disabled_connection = disabled_connection_response.json()

    inactive_response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "integration_connection_id": disabled_connection["id"],
            "source_name": "disabled-profile",
            "source_format": "json",
            "records": [{"external_id": "lead_disabled", "display_name": "Disabled Profile"}],
        },
        headers=owner_headers,
    )
    assert inactive_response.status_code == 409
    assert inactive_response.json()["detail"] == "integration connection is not active"

    async def insert_mismatched_connection() -> str:
        async with session_factory() as session:
            mismatch = IntegrationConnection(
                id="manual-noop-connection",
                tenant_id=tenant_id,
                name="Manual noop profile",
                adapter_key="internal.noop",
                status="active",
                config_json="{}",
                mapping_json="{}",
                scopes_json="[]",
            )
            session.add(mismatch)
            await session.commit()
            return mismatch.id

    noop_connection_id = asyncio.run(insert_mismatched_connection())

    mismatch_response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "integration_connection_id": noop_connection_id,
            "source_name": "wrong-profile",
            "source_format": "json",
            "records": [{"external_id": "lead_wrong", "display_name": "Wrong Profile"}],
        },
        headers=owner_headers,
    )
    assert mismatch_response.status_code == 409
    assert mismatch_response.json()["detail"] == "integration connection adapter mismatch"

    import_response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "integration_connection_id": connection["id"],
            "source_name": "demo-leads-json",
            "source_format": "json",
            "records": [
                {"lead_id": "lead_001", "full_name": "Demo Learner One"},
                {"lead_id": "lead_002", "full_name": "Demo Learner Two"},
                {"lead_id": "", "full_name": "Rejected Demo Row"},
            ],
        },
        headers=owner_headers,
    )
    assert import_response.status_code == 202
    import_event = import_response.json()
    assert import_event["event_type"] == "integration.file_import.requested"
    assert import_event["adapter_key"] == "file.import.fake"
    assert import_event["status"] == "pending"

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed == 2

    outbox_response = client.get(
        f"/tenants/{tenant_id}/outbox-events",
        headers=owner_headers,
    )
    assert outbox_response.status_code == 200
    file_event = next(
        event for event in outbox_response.json() if event["event_type"] == "integration.file_import.requested"
    )
    result = json.loads(file_event["result_json"])
    file_payload = json.loads(file_event["payload_json"])
    assert file_event["status"] == "processed"
    assert file_event["attempts"] == 1
    assert file_event["last_duration_ms"] is not None
    assert result["adapter_key"] == "file.import.fake"
    assert result["status"] == "partial_success"
    assert result["records_received"] == 3
    assert result["records_accepted"] == 2
    assert result["records_rejected"] == 1
    assert result["details"]["accepted_external_ids"] == ["lead_001", "lead_002"]
    assert file_payload["integration_connection_id"] == connection["id"]
    assert file_payload["mapping"] == {"external_id": "lead_id", "display_name": "full_name"}
    assert file_payload["connection_scopes"] == ["file_import:execute", "file_import:preview"]

    async def integration_connection_state() -> tuple[list[IntegrationConnection], list[str]]:
        async with session_factory() as session:
            connections = await list_tenant_owned(
                session,
                IntegrationConnection,
                tenant_id,
                order_by=IntegrationConnection.created_at.desc(),
            )
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(
                    AuditEvent.tenant_id == tenant_id,
                    AuditEvent.event_type.in_(
                        [
                            "integration_connection.created",
                            "integration.file_import.requested",
                        ]
                    ),
                )
                .order_by(AuditEvent.created_at)
            )
            return connections, list(audit_result.scalars().all())

    connections, audit_events = asyncio.run(integration_connection_state())
    assert {item.adapter_key for item in connections} == {"file.import.fake", "internal.noop"}
    assert Counter(audit_events) == Counter(
        {
            "integration_connection.created": 4,
            "integration.file_import.requested": 1,
        }
    )

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_integration_connections{adapter_key="file.import.fake",status="active"} 3' in (
        metrics_response.text
    )
    assert 'drivedesk_integration_connections{adapter_key="file.import.fake",status="disabled"} 1' in (
        metrics_response.text
    )
    assert 'drivedesk_integration_connections{adapter_key="internal.noop",status="active"} 1' in metrics_response.text
    assert 'drivedesk_integration_jobs{adapter_key="file.import.fake",status="processed"} 1' in metrics_response.text
    assert (
        'drivedesk_integration_job_attempts{adapter_key="file.import.fake",status="processed"} 1'
        in metrics_response.text
    )
    assert (
        'drivedesk_integration_job_errors{adapter_key="file.import.fake",status="processed"} 0'
        in metrics_response.text
    )
    assert 'drivedesk_integration_adapter_duration_milliseconds{adapter_key="file.import.fake",status="processed"}' in (
        metrics_response.text
    )
    assert "Demo file import profile" not in metrics_response.text
    assert connection["id"] not in metrics_response.text


def test_accounting_export_adapter_flow_and_operator_review(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_response = client.post(
        "/tenants",
        json={"slug": "accounting-export", "name": "Accounting Export"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Demo accounting export profile",
            "adapter_key": "accounting.export.mock",
            "config": {"provider": "mock-accounting", "mode": "synthetic"},
        },
        headers=owner_headers,
    )
    assert connection_response.status_code == 201
    connection = connection_response.json()
    assert connection["tenant_id"] == tenant_id
    assert connection["adapter_key"] == "accounting.export.mock"
    assert connection["status"] == "active"
    assert json.loads(connection["scopes_json"]) == ["accounting:export"]

    disabled_connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Disabled accounting export profile",
            "adapter_key": "accounting.export.mock",
            "status": "disabled",
        },
        headers=owner_headers,
    )
    assert disabled_connection_response.status_code == 201
    disabled_connection = disabled_connection_response.json()

    inactive_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "integration_connection_id": disabled_connection["id"],
            "export_batch_id": "disabled-batch",
            "documents": [
                {
                    "document_id": "doc_disabled",
                    "document_type": "invoice",
                    "amount_cents": 1000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_disabled",
                }
            ],
        },
        headers=owner_headers,
    )
    assert inactive_response.status_code == 409
    assert inactive_response.json()["detail"] == "integration connection is not active"

    async def insert_mismatched_connection() -> str:
        async with session_factory() as session:
            mismatch = IntegrationConnection(
                id="manual-file-connection",
                tenant_id=tenant_id,
                name="Manual file profile",
                adapter_key="file.import.fake",
                status="active",
                config_json="{}",
                mapping_json='{"external_id":"lead_id","display_name":"full_name"}',
                scopes_json='["file_import:execute"]',
            )
            session.add(mismatch)
            await session.commit()
            return mismatch.id

    mismatched_connection_id = asyncio.run(insert_mismatched_connection())
    mismatch_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "integration_connection_id": mismatched_connection_id,
            "export_batch_id": "wrong-adapter-batch",
            "documents": [
                {
                    "document_id": "doc_wrong",
                    "document_type": "invoice",
                    "amount_cents": 1000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_wrong",
                }
            ],
        },
        headers=owner_headers,
    )
    assert mismatch_response.status_code == 409
    assert mismatch_response.json()["detail"] == "integration connection adapter mismatch"

    export_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "integration_connection_id": connection["id"],
            "export_batch_id": "batch_2026_06",
            "documents": [
                {
                    "document_id": "doc_001",
                    "document_type": "invoice",
                    "amount_cents": 120000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_demo_1",
                },
                {
                    "document_id": "doc_002",
                    "document_type": "receipt",
                    "amount_cents": 50000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_demo_2",
                },
                {"document_id": "doc_rejected", "document_type": "invoice"},
            ],
        },
        headers=owner_headers,
    )
    assert export_response.status_code == 202
    export_event = export_response.json()
    assert export_event["event_type"] == "accounting.export.requested"
    assert export_event["adapter_key"] == "accounting.export.mock"
    assert export_event["status"] == "pending"

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed == 2

    outbox_response = client.get(
        f"/tenants/{tenant_id}/outbox-events",
        headers=owner_headers,
    )
    assert outbox_response.status_code == 200
    accounting_event = next(
        event for event in outbox_response.json() if event["event_type"] == "accounting.export.requested"
    )
    result = json.loads(accounting_event["result_json"])
    payload = json.loads(accounting_event["payload_json"])
    assert accounting_event["status"] == "processed"
    assert accounting_event["attempts"] == 1
    assert accounting_event["last_duration_ms"] is not None
    assert result["adapter_key"] == "accounting.export.mock"
    assert result["status"] == "partial_success"
    assert result["records_received"] == 3
    assert result["records_accepted"] == 2
    assert result["records_rejected"] == 1
    assert result["external_ref"] == "mock-accounting-export:batch_2026_06"
    assert result["details"]["accepted_document_ids"] == ["doc_001", "doc_002"]
    assert result["details"]["document_types"] == ["invoice", "receipt"]
    assert payload["integration_connection_id"] == connection["id"]
    assert payload["connection_scopes"] == ["accounting:export"]
    assert payload["document_count"] == 3
    assert payload["document_types"] == ["invoice", "receipt"]

    retry_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "export_batch_id": "retryable-accounting-batch",
            "simulate_failure": "retryable",
            "documents": [
                {
                    "document_id": "doc_retry",
                    "document_type": "invoice",
                    "amount_cents": 1000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_retry",
                }
            ],
        },
        headers=owner_headers,
    )
    assert retry_response.status_code == 202

    permanent_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "export_batch_id": "permanent-accounting-batch",
            "simulate_failure": "permanent",
            "documents": [
                {
                    "document_id": "doc_dead",
                    "document_type": "invoice",
                    "amount_cents": 1000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_dead",
                }
            ],
        },
        headers=owner_headers,
    )
    assert permanent_response.status_code == 202

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed == 2

    review_response = client.get(
        f"/tenants/{tenant_id}/integration-operator-review?adapter_key=accounting.export.mock",
        headers=owner_headers,
    )
    assert review_response.status_code == 200
    review_items = review_response.json()
    assert {item["status"] for item in review_items} == {"retry", "dead_letter"}
    assert {item["operation_key"] for item in review_items} == {"accounting_export_execute"}
    assert {item["required_connection_scope"] for item in review_items} == {"accounting:export"}
    assert {item["adapter_key"] for item in review_items} == {"accounting.export.mock"}
    assert {item["payload_summary"]["raw_documents_redacted"] for item in review_items} == {1}
    assert {item["payload_summary"]["document_count"] for item in review_items} == {1}
    assert {tuple(item["payload_summary"]["document_types"]) for item in review_items} == {("invoice",)}
    assert all("documents" not in item["payload_summary"] for item in review_items)
    assert all("records" not in item["payload_summary"] for item in review_items)

    async def accounting_state() -> tuple[list[IntegrationConnection], list[str]]:
        async with session_factory() as session:
            connections = await list_tenant_owned(
                session,
                IntegrationConnection,
                tenant_id,
                order_by=IntegrationConnection.created_at.desc(),
            )
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(
                    AuditEvent.tenant_id == tenant_id,
                    AuditEvent.event_type.in_(
                        [
                            "integration_connection.created",
                            "integration.accounting_export.requested",
                        ]
                    ),
                )
                .order_by(AuditEvent.created_at)
            )
            return connections, list(audit_result.scalars().all())

    connections, audit_events = asyncio.run(accounting_state())
    assert {item.adapter_key for item in connections} == {"accounting.export.mock", "file.import.fake"}
    assert Counter(audit_events) == Counter(
        {
            "integration_connection.created": 2,
            "integration.accounting_export.requested": 3,
        }
    )

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_integration_connections{adapter_key="accounting.export.mock",status="active"} 1' in (
        metrics_response.text
    )
    assert 'drivedesk_integration_connections{adapter_key="accounting.export.mock",status="disabled"} 1' in (
        metrics_response.text
    )
    assert 'drivedesk_integration_jobs{adapter_key="accounting.export.mock",status="processed"} 1' in (
        metrics_response.text
    )
    assert 'drivedesk_integration_jobs{adapter_key="accounting.export.mock",status="retry"} 1' in metrics_response.text
    assert 'drivedesk_integration_jobs{adapter_key="accounting.export.mock",status="dead_letter"} 1' in (
        metrics_response.text
    )
    assert "Demo accounting export profile" not in metrics_response.text
    assert connection["id"] not in metrics_response.text


def test_integration_connection_health_checks(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_response = client.post(
        "/tenants",
        json={"slug": "connection-health", "name": "Connection Health"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Health file import profile",
            "adapter_key": "file.import.fake",
            "config": {"mode": "synthetic", "api_token": "not-returned"},
            "mapping": {"external_id": "lead_id", "display_name": "full_name"},
            "scopes": ["file_import:preview"],
        },
        headers=owner_headers,
    )
    assert connection_response.status_code == 201
    connection = connection_response.json()

    never_checked_response = client.get(
        f"/tenants/{tenant_id}/integration-connections/{connection['id']}/health",
        headers=owner_headers,
    )
    assert never_checked_response.status_code == 200
    never_checked = never_checked_response.json()
    assert never_checked["latest_status"] == "never_checked"
    assert never_checked["last_success_at"] is None
    assert never_checked["last_failure_at"] is None
    assert never_checked["check_count"] == 0

    manager_run_response = client.post(
        f"/tenants/{tenant_id}/integration-connections/{connection['id']}/health-checks",
        json={},
        headers={"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"},
    )
    assert manager_run_response.status_code == 403
    assert manager_run_response.json()["detail"] == "permission required: tenant:write"

    check_response = client.post(
        f"/tenants/{tenant_id}/integration-connections/{connection['id']}/health-checks",
        json={},
        headers=owner_headers,
    )
    assert check_response.status_code == 201
    check = check_response.json()
    assert check["tenant_id"] == tenant_id
    assert check["integration_connection_id"] == connection["id"]
    assert check["adapter_key"] == "file.import.fake"
    assert check["status"] == "passed"
    assert check["summary"] == "Integration connection diagnostics passed."
    assert check["duration_ms"] is not None
    check_details = json.loads(check["details_json"])
    assert check_details["mapping_keys"] == ["display_name", "external_id"]
    assert check_details["config_keys"] == ["api_token", "mode"]
    assert check_details["scopes"] == ["file_import:preview"]
    assert check_details["operation_keys"] == ["file_import_preview", "file_import_execute"]
    assert check_details["executable_operation_keys"] == ["file_import_preview"]
    assert check_details["missing_operation_scopes"] == ["file_import:execute"]
    serialized_details = json.dumps(check_details)
    assert "lead_id" not in serialized_details
    assert "full_name" not in serialized_details
    assert "not-returned" not in serialized_details

    failed_response = client.post(
        f"/tenants/{tenant_id}/integration-connections/{connection['id']}/health-checks",
        json={"simulate_failure": "provider_unavailable"},
        headers=owner_headers,
    )
    assert failed_response.status_code == 201
    failed_check = failed_response.json()
    assert failed_check["status"] == "failed"
    assert failed_check["summary"] == "synthetic provider is unavailable"
    failed_details = json.loads(failed_check["details_json"])
    assert failed_details["simulated"] is True
    assert failed_details["error_type"] == "AdapterValidationError"

    disabled_connection_response = client.post(
        f"/tenants/{tenant_id}/integration-connections",
        json={
            "name": "Disabled health profile",
            "adapter_key": "accounting.export.mock",
            "status": "disabled",
        },
        headers=owner_headers,
    )
    assert disabled_connection_response.status_code == 201
    disabled_connection = disabled_connection_response.json()

    disabled_check_response = client.post(
        f"/tenants/{tenant_id}/integration-connections/{disabled_connection['id']}/health-checks",
        json={},
        headers=owner_headers,
    )
    assert disabled_check_response.status_code == 201
    disabled_check = disabled_check_response.json()
    assert disabled_check["adapter_key"] == "accounting.export.mock"
    assert disabled_check["status"] == "failed"
    assert disabled_check["summary"] == "integration connection is not active"

    checks_response = client.get(
        f"/tenants/{tenant_id}/integration-connections/{connection['id']}/health-checks",
        headers={"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"},
    )
    assert checks_response.status_code == 200
    checks = checks_response.json()
    assert [item["status"] for item in checks] == ["failed", "passed"]
    assert all(item["integration_connection_id"] == connection["id"] for item in checks)

    health_response = client.get(
        f"/tenants/{tenant_id}/integration-connections/{connection['id']}/health",
        headers=owner_headers,
    )
    assert health_response.status_code == 200
    health = health_response.json()
    assert health["latest_status"] == "failed"
    assert health["last_success_at"] is not None
    assert health["last_failure_at"] is not None
    assert health["check_count"] == 2
    assert health["latest_summary"] == "synthetic provider is unavailable"
    assert health["latest_details"]["simulated"] is True

    not_found_response = client.post(
        f"/tenants/{tenant_id}/integration-connections/missing-connection/health-checks",
        json={},
        headers=owner_headers,
    )
    assert not_found_response.status_code == 404
    assert not_found_response.json()["detail"] == "integration connection not found"

    async def health_check_state() -> tuple[list[IntegrationConnectionCheck], list[str]]:
        async with session_factory() as session:
            checks_result = await session.execute(
                select(IntegrationConnectionCheck).order_by(IntegrationConnectionCheck.created_at)
            )
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(AuditEvent.tenant_id == tenant_id)
                .order_by(AuditEvent.created_at)
            )
            return list(checks_result.scalars().all()), list(audit_result.scalars().all())

    stored_checks, audit_events = asyncio.run(health_check_state())
    assert [item.status for item in stored_checks] == ["passed", "failed", "failed"]
    assert Counter(audit_events)["integration_connection.health_checked"] == 3

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_integration_connection_checks{adapter_key="file.import.fake",status="passed"} 1' in (
        metrics_response.text
    )
    assert 'drivedesk_integration_connection_checks{adapter_key="file.import.fake",status="failed"} 1' in (
        metrics_response.text
    )
    assert (
        'drivedesk_integration_connection_checks{adapter_key="accounting.export.mock",status="failed"} 1'
        in metrics_response.text
    )
    assert "Health file import profile" not in metrics_response.text
    assert connection["id"] not in metrics_response.text
    assert "not-returned" not in metrics_response.text


def test_integration_reconciliation_evidence_flow(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}
    manager_headers = {"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"}

    tenant_response = client.post(
        "/tenants",
        json={"slug": "integration-reconcile", "name": "Integration Reconcile"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    export_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "export_batch_id": "batch_reconcile_001",
            "documents": [
                {
                    "document_id": "doc_match_001",
                    "document_type": "invoice",
                    "amount_cents": 120000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_match_1",
                },
                {
                    "document_id": "doc_match_002",
                    "document_type": "receipt",
                    "amount_cents": 50000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_match_2",
                },
                {"document_id": "doc_rejected", "document_type": "invoice"},
            ],
        },
        headers=owner_headers,
    )
    assert export_response.status_code == 202
    export_event_id = export_response.json()["id"]

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed >= 1

    outbox_response = client.get(
        f"/tenants/{tenant_id}/outbox-events",
        headers=owner_headers,
    )
    assert outbox_response.status_code == 200
    accounting_event = next(event for event in outbox_response.json() if event["id"] == export_event_id)
    result = json.loads(accounting_event["result_json"])
    assert accounting_event["status"] == "processed"
    assert result["status"] == "partial_success"
    assert result["records_received"] == 3
    assert result["records_accepted"] == 2
    assert result["records_rejected"] == 1

    manager_create_response = client.post(
        f"/tenants/{tenant_id}/integration-reconciliations",
        json={
            "outbox_event_id": export_event_id,
            "provider_status": "partial_success",
            "provider_reference": result["external_ref"],
            "records_received": 3,
            "records_accepted": 2,
            "records_rejected": 1,
        },
        headers=manager_headers,
    )
    assert manager_create_response.status_code == 403
    assert manager_create_response.json()["detail"] == "permission required: tenant:write"

    matched_response = client.post(
        f"/tenants/{tenant_id}/integration-reconciliations",
        json={
            "outbox_event_id": export_event_id,
            "provider_status": "partial_success",
            "provider_reference": result["external_ref"],
            "records_received": 3,
            "records_accepted": 2,
            "records_rejected": 1,
            "note": "operator checked provider dashboard",
        },
        headers=owner_headers,
    )
    assert matched_response.status_code == 201
    matched = matched_response.json()
    assert matched["status"] == "matched"
    assert matched["adapter_key"] == "accounting.export.mock"
    assert matched["operation_key"] == "accounting_export_execute"
    assert matched["summary"] == "Provider evidence matches outbox result evidence."
    assert json.loads(matched["diff_json"]) == {}
    matched_expected = json.loads(matched["expected_json"])
    matched_actual = json.loads(matched["actual_json"])
    assert matched_expected["records_accepted"] == 2
    assert matched_actual["provider_reference"] == result["external_ref"]
    serialized_match = json.dumps(matched, ensure_ascii=False)
    assert "doc_match_001" not in serialized_match
    assert "doc_match_002" not in serialized_match
    assert "counterparty_match" not in serialized_match
    assert "documents" not in serialized_match

    mismatched_response = client.post(
        f"/tenants/{tenant_id}/integration-reconciliations",
        json={
            "outbox_event_id": export_event_id,
            "provider_status": "partial_success",
            "provider_reference": result["external_ref"],
            "records_received": 3,
            "records_accepted": 1,
            "records_rejected": 2,
        },
        headers=owner_headers,
    )
    assert mismatched_response.status_code == 201
    mismatched = mismatched_response.json()
    assert mismatched["status"] == "mismatched"
    diff = json.loads(mismatched["diff_json"])
    assert diff["records_accepted"] == {"expected": 2, "actual": 1}
    assert diff["records_rejected"] == {"expected": 1, "actual": 2}

    pending_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "export_batch_id": "batch_reconcile_pending",
            "documents": [
                {
                    "document_id": "doc_pending",
                    "document_type": "invoice",
                    "amount_cents": 1000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_pending",
                }
            ],
        },
        headers=owner_headers,
    )
    assert pending_response.status_code == 202
    pending_event_id = pending_response.json()["id"]
    pending_reconciliation_response = client.post(
        f"/tenants/{tenant_id}/integration-reconciliations",
        json={
            "outbox_event_id": pending_event_id,
            "provider_status": "pending",
            "records_received": 0,
            "records_accepted": 0,
            "records_rejected": 0,
        },
        headers=owner_headers,
    )
    assert pending_reconciliation_response.status_code == 201
    assert pending_reconciliation_response.json()["status"] == "pending"

    permanent_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "export_batch_id": "batch_reconcile_dead",
            "simulate_failure": "permanent",
            "documents": [
                {
                    "document_id": "doc_dead",
                    "document_type": "invoice",
                    "amount_cents": 1000,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_dead",
                }
            ],
        },
        headers=owner_headers,
    )
    assert permanent_response.status_code == 202
    permanent_event_id = permanent_response.json()["id"]
    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed >= 1

    blocked_reconciliation_response = client.post(
        f"/tenants/{tenant_id}/integration-reconciliations",
        json={
            "outbox_event_id": permanent_event_id,
            "provider_status": "failed",
            "records_received": 0,
            "records_accepted": 0,
            "records_rejected": 1,
        },
        headers=owner_headers,
    )
    assert blocked_reconciliation_response.status_code == 201
    assert blocked_reconciliation_response.json()["status"] == "blocked"

    mismatched_list_response = client.get(
        f"/tenants/{tenant_id}/integration-reconciliations?status=mismatched",
        headers=manager_headers,
    )
    assert mismatched_list_response.status_code == 200
    mismatched_items = mismatched_list_response.json()
    assert len(mismatched_items) == 1
    assert mismatched_items[0]["id"] == mismatched["id"]

    outbox_filtered_response = client.get(
        f"/tenants/{tenant_id}/integration-reconciliations?outbox_event_id={export_event_id}",
        headers=manager_headers,
    )
    assert outbox_filtered_response.status_code == 200
    assert {item["status"] for item in outbox_filtered_response.json()} == {"matched", "mismatched"}

    invalid_filter_response = client.get(
        f"/tenants/{tenant_id}/integration-reconciliations?status=processed",
        headers=owner_headers,
    )
    assert invalid_filter_response.status_code == 400
    assert invalid_filter_response.json()["detail"] == "status must be matched, mismatched, pending, or blocked"

    missing_outbox_response = client.post(
        f"/tenants/{tenant_id}/integration-reconciliations",
        json={
            "outbox_event_id": "missing-outbox-event",
            "provider_status": "success",
        },
        headers=owner_headers,
    )
    assert missing_outbox_response.status_code == 404
    assert missing_outbox_response.json()["detail"] == "outbox event not found"

    async def reconciliation_state() -> tuple[list[IntegrationReconciliation], list[str]]:
        async with session_factory() as session:
            reconciliation_result = await session.execute(
                select(IntegrationReconciliation).order_by(IntegrationReconciliation.created_at)
            )
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(AuditEvent.tenant_id == tenant_id)
                .order_by(AuditEvent.created_at)
            )
            return list(reconciliation_result.scalars().all()), list(audit_result.scalars().all())

    reconciliations, audit_events = asyncio.run(reconciliation_state())
    assert [item.status for item in reconciliations] == ["matched", "mismatched", "pending", "blocked"]
    assert Counter(audit_events)["integration.reconciliation.recorded"] == 4

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert (
        'drivedesk_integration_reconciliations{adapter_key="accounting.export.mock",status="matched"} 1'
        in metrics_response.text
    )
    assert (
        'drivedesk_integration_reconciliations{adapter_key="accounting.export.mock",status="mismatched"} 1'
        in metrics_response.text
    )
    assert (
        'drivedesk_integration_reconciliations{adapter_key="accounting.export.mock",status="pending"} 1'
        in metrics_response.text
    )
    assert (
        'drivedesk_integration_reconciliations{adapter_key="accounting.export.mock",status="blocked"} 1'
        in metrics_response.text
    )
    assert "batch_reconcile_001" not in metrics_response.text
    assert export_event_id not in metrics_response.text


def test_integration_incident_runbook_flow(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}
    manager_headers = {"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"}

    runbooks_response = client.get("/integration-runbooks")
    assert runbooks_response.status_code == 200
    runbooks = {item["key"]: item for item in runbooks_response.json()}
    assert runbooks["integration.retry_backlog"]["alert_name"] == "DriveDeskIntegrationRetries"
    assert runbooks["integration.dead_letter"]["severity"] == "critical"
    assert runbooks["integration.reconciliation_mismatch"]["source_statuses"] == ["mismatched"]

    tenant_response = client.post(
        "/tenants",
        json={"slug": "integration-incidents", "name": "Integration Incidents"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    retry_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "export_batch_id": "incident_retry_batch",
            "simulate_failure": "retryable",
            "documents": [
                {
                    "document_id": "incident_retry_doc",
                    "document_type": "invoice",
                    "amount_cents": 1000,
                    "currency": "RUB",
                    "counterparty_ref": "incident_retry_counterparty",
                }
            ],
        },
        headers=owner_headers,
    )
    assert retry_response.status_code == 202
    retry_event_id = retry_response.json()["id"]

    permanent_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "export_batch_id": "incident_dead_batch",
            "simulate_failure": "permanent",
            "documents": [
                {
                    "document_id": "incident_dead_doc",
                    "document_type": "invoice",
                    "amount_cents": 1000,
                    "currency": "RUB",
                    "counterparty_ref": "incident_dead_counterparty",
                }
            ],
        },
        headers=owner_headers,
    )
    assert permanent_response.status_code == 202
    dead_event_id = permanent_response.json()["id"]

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed >= 2

    manager_create_response = client.post(
        f"/tenants/{tenant_id}/integration-incidents",
        json={"source_type": "outbox_event", "source_id": retry_event_id},
        headers=manager_headers,
    )
    assert manager_create_response.status_code == 403
    assert manager_create_response.json()["detail"] == "permission required: tenant:write"

    retry_incident_response = client.post(
        f"/tenants/{tenant_id}/integration-incidents",
        json={"source_type": "outbox_event", "source_id": retry_event_id, "note": "provider status checked"},
        headers=owner_headers,
    )
    assert retry_incident_response.status_code == 201
    retry_incident = retry_incident_response.json()
    assert retry_incident["source_type"] == "outbox_event"
    assert retry_incident["runbook_key"] == "integration.retry_backlog"
    assert retry_incident["severity"] == "warning"
    assert retry_incident["status"] == "open"
    retry_evidence = json.loads(retry_incident["evidence_json"])
    assert retry_evidence["payload_summary"]["document_count"] == 1
    assert retry_evidence["payload_summary"]["raw_documents_redacted"] == 1
    assert retry_evidence["retry_endpoint"].endswith(f"/outbox-events/{retry_event_id}/retry")
    assert retry_evidence["operator_note_present"] is True

    dead_incident_response = client.post(
        f"/tenants/{tenant_id}/integration-incidents",
        json={"source_type": "outbox_event", "source_id": dead_event_id},
        headers=owner_headers,
    )
    assert dead_incident_response.status_code == 201
    dead_incident = dead_incident_response.json()
    assert dead_incident["runbook_key"] == "integration.dead_letter"
    assert dead_incident["severity"] == "critical"

    success_response = client.post(
        f"/tenants/{tenant_id}/integration-exports/accounting",
        json={
            "export_batch_id": "incident_success_batch",
            "documents": [
                {
                    "document_id": "incident_success_doc",
                    "document_type": "receipt",
                    "amount_cents": 5000,
                    "currency": "RUB",
                    "counterparty_ref": "incident_success_counterparty",
                }
            ],
        },
        headers=owner_headers,
    )
    assert success_response.status_code == 202
    success_event_id = success_response.json()["id"]
    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed >= 1

    processed_incident_response = client.post(
        f"/tenants/{tenant_id}/integration-incidents",
        json={"source_type": "outbox_event", "source_id": success_event_id},
        headers=owner_headers,
    )
    assert processed_incident_response.status_code == 409
    assert processed_incident_response.json()["detail"] == (
        "outbox event does not require an integration incident runbook"
    )

    outbox_response = client.get(f"/tenants/{tenant_id}/outbox-events", headers=owner_headers)
    assert outbox_response.status_code == 200
    success_event = next(event for event in outbox_response.json() if event["id"] == success_event_id)
    result = json.loads(success_event["result_json"])
    reconciliation_response = client.post(
        f"/tenants/{tenant_id}/integration-reconciliations",
        json={
            "outbox_event_id": success_event_id,
            "provider_status": "success",
            "provider_reference": "provider-reference-not-returned",
            "records_received": 1,
            "records_accepted": 0,
            "records_rejected": 1,
        },
        headers=owner_headers,
    )
    assert reconciliation_response.status_code == 201
    reconciliation = reconciliation_response.json()
    assert reconciliation["status"] == "mismatched"
    assert result["records_accepted"] == 1

    reconciliation_incident_response = client.post(
        f"/tenants/{tenant_id}/integration-incidents",
        json={"source_type": "reconciliation", "source_id": reconciliation["id"]},
        headers=owner_headers,
    )
    assert reconciliation_incident_response.status_code == 201
    reconciliation_incident = reconciliation_incident_response.json()
    assert reconciliation_incident["runbook_key"] == "integration.reconciliation_mismatch"
    assert reconciliation_incident["severity"] == "critical"
    reconciliation_evidence = json.loads(reconciliation_incident["evidence_json"])
    assert reconciliation_evidence["provider_reference_present"] is True
    assert set(reconciliation_evidence["diff_keys"]) == {"external_ref", "records_accepted", "records_rejected"}

    serialized_incidents = json.dumps(
        [retry_incident, dead_incident, reconciliation_incident],
        ensure_ascii=False,
    )
    assert "incident_retry_doc" not in serialized_incidents
    assert "incident_dead_doc" not in serialized_incidents
    assert "incident_success_doc" not in serialized_incidents
    assert "incident_retry_counterparty" not in serialized_incidents
    assert "provider-reference-not-returned" not in serialized_incidents
    assert "incident_retry_batch" not in serialized_incidents

    critical_response = client.get(
        f"/tenants/{tenant_id}/integration-incidents?severity=critical",
        headers=manager_headers,
    )
    assert critical_response.status_code == 200
    assert {item["runbook_key"] for item in critical_response.json()} == {
        "integration.dead_letter",
        "integration.reconciliation_mismatch",
    }

    invalid_filter_response = client.get(
        f"/tenants/{tenant_id}/integration-incidents?status=dead_letter",
        headers=owner_headers,
    )
    assert invalid_filter_response.status_code == 400
    assert invalid_filter_response.json()["detail"] == "status must be open, acknowledged, or resolved"

    manager_status_response = client.post(
        f"/tenants/{tenant_id}/integration-incidents/{retry_incident['id']}/status",
        json={"status": "acknowledged"},
        headers=manager_headers,
    )
    assert manager_status_response.status_code == 403
    assert manager_status_response.json()["detail"] == "permission required: tenant:write"

    acknowledged_response = client.post(
        f"/tenants/{tenant_id}/integration-incidents/{retry_incident['id']}/status",
        json={"status": "acknowledged", "note": "operator is investigating"},
        headers=owner_headers,
    )
    assert acknowledged_response.status_code == 200
    assert acknowledged_response.json()["status"] == "acknowledged"
    assert acknowledged_response.json()["resolved_at"] is None

    resolved_response = client.post(
        f"/tenants/{tenant_id}/integration-incidents/{retry_incident['id']}/status",
        json={"status": "resolved", "note": "provider recovered"},
        headers=owner_headers,
    )
    assert resolved_response.status_code == 200
    assert resolved_response.json()["status"] == "resolved"
    assert resolved_response.json()["resolved_at"] is not None

    async def incident_state() -> tuple[list[IntegrationIncident], list[str]]:
        async with session_factory() as session:
            incident_result = await session.execute(select(IntegrationIncident).order_by(IntegrationIncident.created_at))
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(AuditEvent.tenant_id == tenant_id)
                .order_by(AuditEvent.created_at)
            )
            return list(incident_result.scalars().all()), list(audit_result.scalars().all())

    incidents, audit_events = asyncio.run(incident_state())
    assert [item.runbook_key for item in incidents] == [
        "integration.retry_backlog",
        "integration.dead_letter",
        "integration.reconciliation_mismatch",
    ]
    assert Counter(audit_events)["integration.incident.created"] == 3
    assert Counter(audit_events)["integration.incident.status_changed"] == 2

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert (
        'drivedesk_integration_incidents{adapter_key="accounting.export.mock",severity="warning",status="resolved"} 1'
        in metrics_response.text
    )
    assert (
        'drivedesk_integration_incidents{adapter_key="accounting.export.mock",severity="critical",status="open"} 2'
        in metrics_response.text
    )
    assert "incident_retry_batch" not in metrics_response.text
    assert retry_event_id not in metrics_response.text


def test_file_import_adapter_retry_and_dead_letter(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client
    owner_headers = {"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"}

    tenant_response = client.post(
        "/tenants",
        json={"slug": "adapter-failure", "name": "Adapter Failure"},
        headers=owner_headers,
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    retry_response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "source_name": "retryable-file",
            "source_format": "json",
            "simulate_failure": "retryable",
            "records": [{"external_id": "lead_retry", "display_name": "Retry Demo"}],
        },
        headers=owner_headers,
    )
    assert retry_response.status_code == 202

    permanent_response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "source_name": "permanent-file",
            "source_format": "json",
            "simulate_failure": "permanent",
            "records": [{"external_id": "lead_dead", "display_name": "Dead Letter Demo"}],
        },
        headers=owner_headers,
    )
    assert permanent_response.status_code == 202

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed == 3

    async def outbox_events() -> list[OutboxEvent]:
        async with session_factory() as session:
            result = await session.execute(select(OutboxEvent).order_by(OutboxEvent.created_at))
            return list(result.scalars().all())

    events = asyncio.run(outbox_events())
    statuses_by_source = {}
    for event in events:
        payload = json.loads(event.payload_json)
        if "source_name" in payload:
            statuses_by_source[payload["source_name"]] = event

    retry_event = statuses_by_source["retryable-file"]
    assert retry_event.status == "retry"
    assert retry_event.attempts == 1
    assert retry_event.last_duration_ms is not None
    assert retry_event.next_retry_at is not None
    assert retry_event.last_error == "Synthetic provider is temporarily unavailable."

    dead_event = statuses_by_source["permanent-file"]
    assert dead_event.status == "dead_letter"
    assert dead_event.attempts == 1
    assert dead_event.last_duration_ms is not None
    assert dead_event.dead_lettered_at is not None
    assert dead_event.next_retry_at is None
    assert dead_event.last_error == "Synthetic provider rejected the import contract."

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_integration_jobs{adapter_key="file.import.fake",status="retry"} 1' in metrics_response.text
    assert 'drivedesk_integration_jobs{adapter_key="file.import.fake",status="dead_letter"} 1' in metrics_response.text
    assert 'drivedesk_integration_job_errors{adapter_key="file.import.fake",status="retry"} 1' in metrics_response.text
    assert (
        'drivedesk_integration_job_errors{adapter_key="file.import.fake",status="dead_letter"} 1'
        in metrics_response.text
    )

    review_response = client.get(
        f"/tenants/{tenant_id}/integration-operator-review",
        headers=owner_headers,
    )
    assert review_response.status_code == 200
    review_items = review_response.json()
    assert {item["status"] for item in review_items} == {"retry", "dead_letter"}
    assert {item["operation_key"] for item in review_items} == {"file_import_execute"}
    assert {item["required_connection_scope"] for item in review_items} == {"file_import:execute"}
    assert {item["adapter_key"] for item in review_items} == {"file.import.fake"}
    assert {item["payload_summary"]["raw_records_redacted"] for item in review_items} == {1}
    assert all("records" not in item["payload_summary"] for item in review_items)
    assert all("source_name" not in item["payload_summary"] for item in review_items)
    assert all(item["retry_endpoint"].startswith(f"/tenants/{tenant_id}/outbox-events/") for item in review_items)

    dead_letter_review_response = client.get(
        f"/tenants/{tenant_id}/integration-operator-review?status=dead_letter",
        headers=owner_headers,
    )
    assert dead_letter_review_response.status_code == 200
    dead_letter_review = dead_letter_review_response.json()
    assert len(dead_letter_review) == 1
    assert dead_letter_review[0]["status"] == "dead_letter"
    assert dead_letter_review[0]["severity"] == "operator_review"
    assert "review mapping/provider contract" in dead_letter_review[0]["recommended_action"]

    invalid_review_filter_response = client.get(
        f"/tenants/{tenant_id}/integration-operator-review?status=processed",
        headers=owner_headers,
    )
    assert invalid_review_filter_response.status_code == 400
    assert invalid_review_filter_response.json()["detail"] == "status must be retry or dead_letter"

    manager_review_response = client.get(
        f"/tenants/{tenant_id}/integration-operator-review",
        headers={"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"},
    )
    assert manager_review_response.status_code == 403
    assert manager_review_response.json()["detail"] == "permission required: outbox:read"

    processed_event = next(event for event in events if event.status == "processed")
    processed_retry_response = client.post(
        f"/tenants/{tenant_id}/outbox-events/{processed_event.id}/retry",
        json={"reason": "already processed"},
        headers=owner_headers,
    )
    assert processed_retry_response.status_code == 409
    assert processed_retry_response.json()["detail"] == "outbox event is not in retry or dead_letter status"

    manager_retry_response = client.post(
        f"/tenants/{tenant_id}/outbox-events/{retry_event.id}/retry",
        json={"reason": "provider recovered"},
        headers={"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"},
    )
    assert manager_retry_response.status_code == 403
    assert manager_retry_response.json()["detail"] == "permission required: outbox:read"

    retry_requeue_response = client.post(
        f"/tenants/{tenant_id}/outbox-events/{retry_event.id}/retry",
        json={"reason": "provider recovered"},
        headers=owner_headers,
    )
    assert retry_requeue_response.status_code == 200
    retry_requeue = retry_requeue_response.json()
    assert retry_requeue["status"] == "pending"
    assert retry_requeue["attempts"] == 1
    assert retry_requeue["last_error"] is None
    assert retry_requeue["last_duration_ms"] is None
    assert retry_requeue["next_retry_at"] is None
    assert retry_requeue["dead_lettered_at"] is None

    dead_requeue_response = client.post(
        f"/tenants/{tenant_id}/outbox-events/{dead_event.id}/retry",
        json={"reason": "operator fixed provider mapping", "reset_attempts": True},
        headers=owner_headers,
    )
    assert dead_requeue_response.status_code == 200
    dead_requeue = dead_requeue_response.json()
    assert dead_requeue["status"] == "pending"
    assert dead_requeue["attempts"] == 0
    assert dead_requeue["last_error"] is None
    assert dead_requeue["dead_lettered_at"] is None

    async def recovery_state() -> tuple[list[OutboxEvent], list[str]]:
        async with session_factory() as session:
            outbox_result = await session.execute(select(OutboxEvent).order_by(OutboxEvent.created_at))
            audit_result = await session.execute(
                select(AuditEvent.event_type)
                .where(
                    AuditEvent.tenant_id == tenant_id,
                    AuditEvent.event_type == "outbox_event.retry_requested",
                )
                .order_by(AuditEvent.created_at)
            )
            return list(outbox_result.scalars().all()), list(audit_result.scalars().all())

    recovered_events, recovery_audit_events = asyncio.run(recovery_state())
    recovered_by_id = {event.id: event for event in recovered_events}
    assert recovered_by_id[retry_event.id].status == "pending"
    assert recovered_by_id[retry_event.id].attempts == 1
    assert recovered_by_id[retry_event.id].last_error is None
    assert recovered_by_id[dead_event.id].status == "pending"
    assert recovered_by_id[dead_event.id].attempts == 0
    assert recovered_by_id[dead_event.id].dead_lettered_at is None
    assert Counter(recovery_audit_events) == Counter({"outbox_event.retry_requested": 2})

    recovery_metrics_response = client.get("/metrics")
    assert recovery_metrics_response.status_code == 200
    assert 'drivedesk_integration_jobs{adapter_key="file.import.fake",status="pending"} 2' in (
        recovery_metrics_response.text
    )
    assert 'drivedesk_integration_job_errors{adapter_key="file.import.fake",status="pending"} 0' in (
        recovery_metrics_response.text
    )

    empty_review_response = client.get(
        f"/tenants/{tenant_id}/integration-operator-review",
        headers=owner_headers,
    )
    assert empty_review_response.status_code == 200
    assert empty_review_response.json() == []


def test_worker_adapter_logs_are_structured_json(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    client, session_factory = api_client
    caplog.set_level(logging.INFO, logger="drivedesk.worker.adapters")

    tenant_response = client.post(
        "/tenants",
        json={"slug": "adapter-logs", "name": "Adapter Logs"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "source_name": "log-file",
            "source_format": "json",
            "records": [{"external_id": "lead_log", "display_name": "Log Demo"}],
        },
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert response.status_code == 202

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed == 2

    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "drivedesk.worker.adapters" and record.message.startswith("{")
    ]
    event_types = {event["event_type"] for event in events}
    assert "adapter.started" in event_types
    assert "adapter.completed" in event_types
    completed = next(
        event
        for event in events
        if event["event_type"] == "adapter.completed" and event["adapter_key"] == "file.import.fake"
    )
    assert completed["service"] == "drivedesk-worker"
    assert completed["tenant_id"] == tenant_id
    assert completed["duration_ms"] >= 0
    assert completed["records_accepted"] == 1
    assert "headers" not in completed
    assert "body" not in completed
