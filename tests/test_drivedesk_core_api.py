from __future__ import annotations

import asyncio
import json
import logging
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

from drivedesk_api.db import AccessToken, AuditEvent, AuthAttempt, Base, OutboxEvent, PlatformAdmin, User
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
    client, _ = api_client
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

    logout_viewer_response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {viewer_a_token}"},
    )
    assert logout_viewer_response.status_code == 200

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
    assert file_event["last_duration_ms"] is not None
    assert result["adapter_key"] == "file.import.fake"
    assert result["status"] == "partial_success"
    assert result["records_received"] == 3
    assert result["records_accepted"] == 2
    assert result["records_rejected"] == 1

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
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
