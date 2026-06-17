from __future__ import annotations

import asyncio
import json
import sys
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

from drivedesk_api.db import Base, OutboxEvent
from drivedesk_api.main import build_app
from drivedesk_api.session import get_session
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
        json={"email": "manager@example.com", "display_name": "Manager User"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    membership_response = client.post(
        f"/tenants/{tenant_id}/memberships",
        json={"user_id": user_id, "role": "manager"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert membership_response.status_code == 201
    assert membership_response.json()["role"] == "manager"

    tenants_response = client.get("/tenants", headers={"X-Actor-Id": "viewer_1", "X-Actor-Role": "viewer"})
    assert tenants_response.status_code == 200
    assert tenants_response.json()[0]["slug"] == "drive-test"

    memberships_response = client.get(
        f"/tenants/{tenant_id}/memberships",
        headers={"X-Actor-Id": "viewer_1", "X-Actor-Role": "viewer"},
    )
    assert memberships_response.status_code == 200
    assert memberships_response.json()[0]["user_id"] == user_id

    audit_response = client.get(
        f"/tenants/{tenant_id}/audit-events",
        headers={"X-Actor-Id": "viewer_1", "X-Actor-Role": "viewer"},
    )
    assert audit_response.status_code == 200
    event_types = {event["event_type"] for event in audit_response.json()}
    assert {"tenant.created", "membership.created"}.issubset(event_types)

    outbox_response = client.get(
        f"/tenants/{tenant_id}/outbox-events",
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert outbox_response.status_code == 200
    assert {event["status"] for event in outbox_response.json()} == {"pending"}

    processed = asyncio.run(process_outbox_once(session_factory=session_factory))
    assert processed == 3

    async def outbox_statuses() -> list[str]:
        async with session_factory() as session:
            result = await session.execute(select(OutboxEvent.status).order_by(OutboxEvent.created_at))
            return list(result.scalars().all())

    assert asyncio.run(outbox_statuses()) == ["processed", "processed", "processed"]


def test_file_import_adapter_success_flow(api_client: tuple[TestClient, async_sessionmaker[AsyncSession]]) -> None:
    client, session_factory = api_client

    tenant_response = client.post(
        "/tenants",
        json={"slug": "adapter-success", "name": "Adapter Success"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["id"]

    import_response = client.post(
        f"/tenants/{tenant_id}/integration-imports/file",
        json={
            "source_name": "demo-leads-json",
            "source_format": "json",
            "records": [
                {"external_id": "lead_001", "display_name": "Demo Learner One"},
                {"external_id": "lead_002", "display_name": "Demo Learner Two"},
                {"external_id": "", "display_name": "Rejected Demo Row"},
            ],
        },
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
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
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    assert outbox_response.status_code == 200
    file_event = next(
        event for event in outbox_response.json() if event["event_type"] == "integration.file_import.requested"
    )
    result = json.loads(file_event["result_json"])
    assert file_event["status"] == "processed"
    assert file_event["attempts"] == 1
    assert result["adapter_key"] == "file.import.fake"
    assert result["status"] == "partial_success"
    assert result["records_received"] == 3
    assert result["records_accepted"] == 2
    assert result["records_rejected"] == 1


def test_file_import_adapter_retry_and_dead_letter(
    api_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_client

    tenant_response = client.post(
        "/tenants",
        json={"slug": "adapter-failure", "name": "Adapter Failure"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
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
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
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
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
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
    assert retry_event.next_retry_at is not None
    assert retry_event.last_error == "Fake provider is temporarily unavailable."

    dead_event = statuses_by_source["permanent-file"]
    assert dead_event.status == "dead_letter"
    assert dead_event.attempts == 1
    assert dead_event.dead_lettered_at is not None
    assert dead_event.next_retry_at is None
    assert dead_event.last_error == "Fake provider rejected the import contract."
