from __future__ import annotations

import asyncio
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
