from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[1]
for relative in ("apps/api", "apps/worker", "packages/core"):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi.testclient import TestClient

from drivedesk_api.db import Base
from drivedesk_api.main import build_app
from drivedesk_api.session import get_session
from drivedesk_core import ActorRef, TenantRef, build_event
from drivedesk_core.adapters import AdapterExecutionError, FakeFileImportAdapter
from drivedesk_worker.main import build_heartbeat, heartbeat_to_json


@pytest.fixture()
def api_client() -> Iterator[TestClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(create_schema())
    app = build_app()
    app.dependency_overrides[get_session] = override_session

    with TestClient(app) as client:
        yield client

    asyncio.run(engine.dispose())


def test_core_event_envelope() -> None:
    tenant = TenantRef(tenant_id="tenant_test", slug="test")
    actor = ActorRef(actor_id="tester", actor_type="system")

    event = build_event(
        event_type="tenant.created",
        tenant=tenant,
        actor=actor,
        payload={"source": "test"},
        correlation_id="test-correlation",
    )

    assert event.event_id
    assert event.event_type == "tenant.created"
    assert event.tenant == tenant
    assert event.actor == actor
    assert event.payload["source"] == "test"
    assert event.correlation_id == "test-correlation"


def test_fake_file_import_adapter_contract() -> None:
    adapter = FakeFileImportAdapter()

    result = adapter.execute(
        {
            "source_name": "demo-json",
            "source_format": "json",
            "records": [
                {"external_id": "row_1", "display_name": "Demo One"},
                {"external_id": "", "display_name": "Rejected"},
            ],
        }
    )

    assert result.adapter_key == "file.import.fake"
    assert result.status == "partial_success"
    assert result.records_received == 2
    assert result.records_accepted == 1
    assert result.records_rejected == 1
    assert result.to_payload()["details"]["accepted_external_ids"] == ["row_1"]

    try:
        adapter.execute({"simulate_failure": "retryable", "records": []})
    except AdapterExecutionError as exc:
        assert exc.retryable is True
        assert exc.adapter_key == "file.import.fake"
    else:
        raise AssertionError("expected retryable adapter failure")


def test_api_health_and_ready_endpoints() -> None:
    client = TestClient(build_app())

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_api_metrics_endpoint(api_client: TestClient) -> None:
    client = api_client

    client.post(
        "/tenants",
        json={"slug": "metrics-test", "name": "Metrics Test"},
        headers={"X-Actor-Id": "owner_1", "X-Actor-Role": "owner"},
    )
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "drivedesk_api_info{" in response.text
    assert 'service="drivedesk-api"' in response.text
    assert 'drivedesk_api_readiness{dependency="all"} 1' in response.text
    assert 'drivedesk_api_readiness{dependency="database_url_configured"} 1' in response.text
    assert 'drivedesk_api_readiness{dependency="redis_url_configured"} 1' in response.text
    assert "drivedesk_metrics_storage_available 1" in response.text
    assert "drivedesk_api_uptime_seconds " in response.text
    assert "drivedesk_api_started_at_seconds " in response.text
    assert 'drivedesk_api_http_requests_total{method="GET",path="/health",status_code="200"}' in response.text
    assert 'drivedesk_api_http_request_duration_seconds_bucket{le="0.005",method="GET",path="/health",' in response.text
    assert 'drivedesk_outbox_events{status="pending"} 1' in response.text
    assert 'drivedesk_integration_jobs{adapter_key="internal.noop",status="pending"} 1' in response.text
    assert 'drivedesk_integration_job_attempts{adapter_key="internal.noop",status="pending"} 0' in response.text
    assert 'drivedesk_integration_job_errors{adapter_key="internal.noop",status="pending"} 0' in response.text
    assert "# HELP drivedesk_auth_sessions Current auth sessions by lifecycle status." in response.text
    assert "# TYPE drivedesk_auth_sessions gauge" in response.text
    assert "# HELP drivedesk_auth_attempts_total Auth attempts grouped by outcome." in response.text
    assert "# TYPE drivedesk_auth_attempts_total counter" in response.text
    assert "# HELP drivedesk_business_records Current business records by type and status." in response.text
    assert "# TYPE drivedesk_business_records gauge" in response.text
    assert "# HELP drivedesk_workflow_rules Current workflow rules by status, trigger, and action." in response.text
    assert "# TYPE drivedesk_workflow_rules gauge" in response.text
    assert "# HELP drivedesk_workflow_action_runs Workflow action runs by action type and status." in response.text
    assert "# TYPE drivedesk_workflow_action_runs gauge" in response.text
    assert "# HELP drivedesk_integration_connections Integration connections by adapter and status." in response.text
    assert "# TYPE drivedesk_integration_connections gauge" in response.text


def test_api_metrics_endpoint_degrades_without_database_schema() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app = build_app()
    app.dependency_overrides[get_session] = override_session

    with TestClient(app) as client:
        response = client.get("/metrics")

    asyncio.run(engine.dispose())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "drivedesk_metrics_storage_available 0" in response.text
    assert "# HELP drivedesk_auth_sessions Current auth sessions by lifecycle status." in response.text
    assert "# HELP drivedesk_auth_attempts_total Auth attempts grouped by outcome." in response.text
    assert "# HELP drivedesk_business_records Current business records by type and status." in response.text
    assert "# HELP drivedesk_workflow_rules Current workflow rules by status, trigger, and action." in response.text
    assert "# HELP drivedesk_workflow_action_runs Workflow action runs by action type and status." in response.text
    assert "# HELP drivedesk_integration_connections Integration connections by adapter and status." in response.text


def test_api_request_log_is_structured_json(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="drivedesk.api.requests")
    client = TestClient(build_app())

    response = client.get("/health?ignored_query=value")

    assert response.status_code == 200
    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "drivedesk.api.requests" and record.message.startswith("{")
    ]
    request_event = next(event for event in events if event["event_type"] == "http.request")
    assert request_event["method"] == "GET"
    assert request_event["path"] == "/health"
    assert request_event["status_code"] == 200
    assert request_event["service"] == "drivedesk-api"
    assert "duration_ms" in request_event
    assert "headers" not in request_event
    assert "query" not in request_event
    assert "body" not in request_event


def test_worker_heartbeat() -> None:
    heartbeat = build_heartbeat()

    assert heartbeat.event_type == "worker.heartbeat"
    assert heartbeat.service == "drivedesk-worker"
    assert heartbeat.environment
    assert heartbeat.status == "ok"
    assert heartbeat.core_version

    heartbeat_json = json.loads(heartbeat_to_json(heartbeat))
    assert heartbeat_json["event_type"] == "worker.heartbeat"
    assert heartbeat_json["service"] == "drivedesk-worker"
