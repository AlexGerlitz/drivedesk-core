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
    BusinessRecord,
    IntegrationConnection,
    OutboxEvent,
    PlatformAdmin,
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
    assert payload["apiContract"]["data_profile"] == "synthetic_fake_data"
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
    assert len(payload["integrationJobs"]) >= 3
    assert len(payload["integrationHealth"]) >= 4
    assert {job["status"] for job in payload["integrationJobs"]} >= {"processed", "retry", "dead_letter"}

    serialized = json.dumps(payload).lower()
    assert "land" "vps" not in serialized
    assert "auto" "school54" not in serialized
    assert "password" not in serialized


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

    connections_response = client.get(
        f"/tenants/{tenant_id}/integration-connections",
        headers={"X-Actor-Id": "manager_1", "X-Actor-Role": "manager"},
    )
    assert connections_response.status_code == 200
    assert [item["id"] for item in connections_response.json()] == [connection["id"]]

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
            "integration_connection.created": 2,
            "integration.file_import.requested": 1,
        }
    )

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_integration_connections{adapter_key="file.import.fake",status="active"} 1' in (
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
    assert retry_event.last_error == "Fake provider is temporarily unavailable."

    dead_event = statuses_by_source["permanent-file"]
    assert dead_event.status == "dead_letter"
    assert dead_event.attempts == 1
    assert dead_event.last_duration_ms is not None
    assert dead_event.dead_lettered_at is not None
    assert dead_event.next_retry_at is None
    assert dead_event.last_error == "Fake provider rejected the import contract."

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert 'drivedesk_integration_jobs{adapter_key="file.import.fake",status="retry"} 1' in metrics_response.text
    assert 'drivedesk_integration_jobs{adapter_key="file.import.fake",status="dead_letter"} 1' in metrics_response.text
    assert 'drivedesk_integration_job_errors{adapter_key="file.import.fake",status="retry"} 1' in metrics_response.text
    assert (
        'drivedesk_integration_job_errors{adapter_key="file.import.fake",status="dead_letter"} 1'
        in metrics_response.text
    )

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
