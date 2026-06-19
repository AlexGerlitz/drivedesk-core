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
from drivedesk_core import (
    ActorRef,
    MockAccountingExportAdapter,
    MockCrmDealAdapter,
    TenantRef,
    build_adapter_connection_diagnostics,
    build_event,
    list_integration_runbooks,
    list_lifecycle_policies,
    preview_lifecycle_transition,
)
from drivedesk_core.adapters import AdapterExecutionError, FakeFileImportAdapter, list_adapter_descriptors
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

    mapped_result = adapter.execute(
        {
            "source_name": "mapped-json",
            "source_format": "json",
            "mapping": {"external_id": "lead_id", "display_name": "full_name"},
            "records": [
                {"lead_id": "lead_1", "full_name": "Mapped One"},
                {"lead_id": "lead_2", "full_name": ""},
            ],
        }
    )
    assert mapped_result.status == "partial_success"
    assert mapped_result.records_received == 2
    assert mapped_result.records_accepted == 1
    assert mapped_result.records_rejected == 1
    assert mapped_result.to_payload()["details"]["accepted_external_ids"] == ["lead_1"]

    try:
        adapter.execute({"simulate_failure": "retryable", "records": []})
    except AdapterExecutionError as exc:
        assert exc.retryable is True
        assert exc.adapter_key == "file.import.fake"
    else:
        raise AssertionError("expected retryable adapter failure")


def test_mock_accounting_export_adapter_contract() -> None:
    adapter = MockAccountingExportAdapter()

    result = adapter.execute(
        {
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
        }
    )

    assert result.adapter_key == "accounting.export.mock"
    assert result.status == "partial_success"
    assert result.records_received == 3
    assert result.records_accepted == 2
    assert result.records_rejected == 1
    payload = result.to_payload()
    assert payload["external_ref"] == "mock-accounting-export:batch_2026_06"
    assert payload["details"]["accepted_document_ids"] == ["doc_001", "doc_002"]
    assert payload["details"]["document_types"] == ["invoice", "receipt"]

    success_result = adapter.execute(
        {
            "export_batch_id": "batch_success",
            "documents": [
                {
                    "document_id": "doc_success",
                    "document_type": "invoice",
                    "amount_cents": 0,
                    "currency": "RUB",
                    "counterparty_ref": "counterparty_demo",
                }
            ],
        }
    )
    assert success_result.status == "success"
    assert success_result.records_rejected == 0

    try:
        adapter.execute({"simulate_failure": "retryable", "documents": []})
    except AdapterExecutionError as exc:
        assert exc.retryable is True
        assert exc.adapter_key == "accounting.export.mock"
    else:
        raise AssertionError("expected retryable accounting adapter failure")


def test_mock_crm_deal_adapter_contract() -> None:
    adapter = MockCrmDealAdapter()

    result = adapter.execute(
        {
            "batch_id": "bitrix_demo_batch",
            "mapping": {
                "deal_id": "ID",
                "source_state": "STAGE_ID",
                "owner_role": "ASSIGNED_BY_ROLE",
                "amount": "OPPORTUNITY",
            },
            "deals": [
                {
                    "ID": "DEAL-2026-001",
                    "STAGE_ID": "invoice_sent",
                    "ASSIGNED_BY_ROLE": "sales",
                    "OPPORTUNITY": "1500",
                    "PHONE": "+70000000000",
                    "access_token": "secret-token",
                },
                {
                    "ID": "",
                    "STAGE_ID": "lost",
                    "CLIENT_NAME": "Hidden Person",
                },
            ],
        }
    )

    assert result.adapter_key == "crm.bitrix24.mock"
    assert result.status == "partial_success"
    assert result.records_received == 2
    assert result.records_accepted == 1
    assert result.records_rejected == 1
    payload = result.to_payload()
    assert payload["external_ref"] == "mock-crm-deal-intake:bitrix_demo_batch"
    assert payload["details"]["accepted_subject_refs"] == ["deal:DEAL-2026-001"]
    assert payload["details"]["source_states"] == ["invoice_sent"]
    assert payload["details"]["amount_buckets"] == ["1000-2000"]
    assert set(payload["details"]["dropped_sensitive_keys"]) >= {
        "CLIENT_NAME",
        "PHONE",
        "access_token",
    }
    assert payload["details"]["public_safe"] is True
    assert payload["details"]["raw_payload_included"] is False
    assert payload["details"]["external_mutation"] is False
    assert payload["details"]["requires_secret"] is False
    assert "+70000000000" not in json.dumps(payload)
    assert "secret-token" not in json.dumps(payload)
    assert "Hidden Person" not in json.dumps(payload)

    success_result = adapter.execute(
        {
            "batch_id": "bitrix_success",
            "deals": [
                {
                    "deal_id": "DEAL-2026-002",
                    "source_state": "paid",
                    "amount_bucket": "2001-5000",
                }
            ],
        }
    )
    assert success_result.status == "success"
    assert success_result.records_rejected == 0

    try:
        adapter.execute({"simulate_failure": "retryable", "deals": []})
    except AdapterExecutionError as exc:
        assert exc.retryable is True
        assert exc.adapter_key == "crm.bitrix24.mock"
    else:
        raise AssertionError("expected retryable CRM adapter failure")


def test_adapter_catalog_describes_runtime_adapters() -> None:
    descriptors = {item["key"]: item for item in list_adapter_descriptors()}

    assert set(descriptors) == {
        "accounting.export.mock",
        "crm.bitrix24.mock",
        "file.import.fake",
        "internal.noop",
    }
    assert descriptors["file.import.fake"]["connection_profile_supported"] is True
    assert descriptors["file.import.fake"]["connection_profile_required"] is False
    assert descriptors["file.import.fake"]["mapping_example"] == {
        "external_id": "lead_id",
        "display_name": "full_name",
    }
    assert descriptors["file.import.fake"]["required_mapping_keys"] == ["external_id", "display_name"]
    assert descriptors["file.import.fake"]["supported_connection_scopes"] == [
        "file_import:execute",
        "file_import:preview",
    ]
    assert descriptors["file.import.fake"]["default_connection_scopes"] == [
        "file_import:execute",
        "file_import:preview",
    ]
    operation_contracts = {item["key"]: item for item in descriptors["file.import.fake"]["operation_contracts"]}
    assert set(operation_contracts) == {"file_import_execute", "file_import_preview"}
    assert operation_contracts["file_import_preview"]["required_connection_scope"] == "file_import:preview"
    assert operation_contracts["file_import_execute"]["required_connection_scope"] == "file_import:execute"
    assert operation_contracts["file_import_execute"]["event_type"] == "integration.file_import.requested"
    assert operation_contracts["file_import_execute"]["retryable"] is True
    assert operation_contracts["file_import_execute"]["dead_letter"] is True
    assert "records" in descriptors["file.import.fake"]["payload_schema"]["required"]
    assert "field mapping transform" in descriptors["file.import.fake"]["capabilities"]
    assert "mapping preview" in descriptors["file.import.fake"]["capabilities"]
    assert "connection scope enforcement" in descriptors["file.import.fake"]["capabilities"]
    assert descriptors["accounting.export.mock"]["direction"] == "outbound"
    assert descriptors["accounting.export.mock"]["connection_profile_supported"] is True
    assert descriptors["accounting.export.mock"]["required_mapping_keys"] == []
    assert descriptors["accounting.export.mock"]["supported_connection_scopes"] == ["accounting:export"]
    assert descriptors["accounting.export.mock"]["default_connection_scopes"] == ["accounting:export"]
    accounting_operation_contracts = {
        item["key"]: item for item in descriptors["accounting.export.mock"]["operation_contracts"]
    }
    assert set(accounting_operation_contracts) == {"accounting_export_execute"}
    assert accounting_operation_contracts["accounting_export_execute"]["event_type"] == (
        "accounting.export.requested"
    )
    assert accounting_operation_contracts["accounting_export_execute"]["endpoint"] == (
        "POST /tenants/{tenant_id}/integration-exports/accounting"
    )
    assert accounting_operation_contracts["accounting_export_execute"]["required_connection_scope"] == (
        "accounting:export"
    )
    assert accounting_operation_contracts["accounting_export_execute"]["retryable"] is True
    assert accounting_operation_contracts["accounting_export_execute"]["dead_letter"] is True
    assert descriptors["crm.bitrix24.mock"]["direction"] == "inbound"
    assert descriptors["crm.bitrix24.mock"]["category"] == "crm"
    assert descriptors["crm.bitrix24.mock"]["connection_profile_supported"] is True
    assert descriptors["crm.bitrix24.mock"]["required_mapping_keys"] == ["deal_id", "source_state"]
    assert descriptors["crm.bitrix24.mock"]["mapping_example"] == {
        "deal_id": "ID",
        "source_state": "STAGE_ID",
        "owner_role": "ASSIGNED_BY_ROLE",
        "amount": "OPPORTUNITY",
    }
    assert descriptors["crm.bitrix24.mock"]["supported_connection_scopes"] == [
        "crm:deal.ingest",
        "crm:deal.preview",
    ]
    assert descriptors["crm.bitrix24.mock"]["default_connection_scopes"] == [
        "crm:deal.ingest",
        "crm:deal.preview",
    ]
    crm_operation_contracts = {
        item["key"]: item for item in descriptors["crm.bitrix24.mock"]["operation_contracts"]
    }
    assert set(crm_operation_contracts) == {
        "crm_deal_ingest_execute",
        "crm_deal_intake_preview",
    }
    assert crm_operation_contracts["crm_deal_intake_preview"]["endpoint"] == (
        "POST /tenants/{tenant_id}/business-provider-intake/preview"
    )
    assert crm_operation_contracts["crm_deal_intake_preview"]["required_connection_scope"] == (
        "crm:deal.preview"
    )
    assert crm_operation_contracts["crm_deal_ingest_execute"]["event_type"] == (
        "integration.crm_deal.ingest.requested"
    )
    assert crm_operation_contracts["crm_deal_ingest_execute"]["required_connection_scope"] == (
        "crm:deal.ingest"
    )
    assert "crm deal normalization" in descriptors["crm.bitrix24.mock"]["capabilities"]
    assert "sensitive key redaction evidence" in descriptors["crm.bitrix24.mock"]["capabilities"]
    assert descriptors["crm.bitrix24.mock"]["auth_profile"] == {
        "mode": "oauth2_or_webhook_boundary",
        "public_demo_requires_secret": False,
        "real_provider_requires_secret": True,
        "secret_refs": ["BITRIX24_WEBHOOK_URL", "BITRIX24_CLIENT_SECRET"],
        "credential_placement": "server_secret_store",
        "token_exchange": "private_connector_only",
        "external_token_exchange": False,
        "data_boundaries": [
            "no_public_secrets",
            "no_browser_token_storage",
            "server_side_provider_calls_only",
        ],
    }
    assert descriptors["file.import.fake"]["auth_profile"]["public_demo_requires_secret"] is False
    assert descriptors["internal.noop"]["connection_profile_supported"] is False


def test_adapter_connection_diagnostics_are_safe_and_operation_aware() -> None:
    diagnostics = build_adapter_connection_diagnostics(
        "file.import.fake",
        mapping={"external_id": "lead_id", "display_name": "full_name"},
        scopes=["file_import:preview"],
    )

    assert diagnostics["adapter_key"] == "file.import.fake"
    assert diagnostics["direction"] == "inbound"
    assert diagnostics["mapping_keys"] == ["display_name", "external_id"]
    assert diagnostics["scopes"] == ["file_import:preview"]
    assert diagnostics["operation_keys"] == ["file_import_preview", "file_import_execute"]
    assert diagnostics["executable_operation_keys"] == ["file_import_preview"]
    assert diagnostics["missing_operation_scopes"] == ["file_import:execute"]
    assert "lead_id" not in json.dumps(diagnostics)
    assert "full_name" not in json.dumps(diagnostics)

    accounting = build_adapter_connection_diagnostics(
        "accounting.export.mock",
        mapping={},
        scopes=["accounting:export"],
    )
    assert accounting["adapter_key"] == "accounting.export.mock"
    assert accounting["direction"] == "outbound"
    assert accounting["executable_operation_keys"] == ["accounting_export_execute"]
    assert accounting["missing_operation_scopes"] == []
    assert accounting["auth_mode"] == "mock_outbound_boundary"
    assert accounting["public_demo_requires_secret"] is False
    assert accounting["real_provider_requires_secret"] is True

    crm = build_adapter_connection_diagnostics(
        "crm.bitrix24.mock",
        mapping={"deal_id": "ID", "source_state": "STAGE_ID"},
        scopes=["crm:deal.preview"],
    )
    assert crm["adapter_key"] == "crm.bitrix24.mock"
    assert crm["direction"] == "inbound"
    assert crm["mapping_keys"] == ["deal_id", "source_state"]
    assert crm["scopes"] == ["crm:deal.preview"]
    assert crm["operation_keys"] == ["crm_deal_intake_preview", "crm_deal_ingest_execute"]
    assert crm["executable_operation_keys"] == ["crm_deal_intake_preview"]
    assert crm["missing_operation_scopes"] == ["crm:deal.ingest"]
    assert crm["auth_mode"] == "oauth2_or_webhook_boundary"
    assert crm["public_demo_requires_secret"] is False
    assert crm["real_provider_requires_secret"] is True
    assert crm["secret_refs"] == ["BITRIX24_CLIENT_SECRET", "BITRIX24_WEBHOOK_URL"]
    assert "STAGE_ID" not in json.dumps(crm)


def test_integration_runbook_catalog_covers_operational_states() -> None:
    runbooks = {runbook["key"]: runbook for runbook in list_integration_runbooks()}

    assert set(runbooks) >= {
        "integration.retry_backlog",
        "integration.dead_letter",
        "integration.reconciliation_mismatch",
        "integration.reconciliation_blocked",
        "integration.reconciliation_pending",
    }
    assert runbooks["integration.retry_backlog"]["source_type"] == "outbox_event"
    assert runbooks["integration.retry_backlog"]["source_statuses"] == ["retry"]
    assert runbooks["integration.retry_backlog"]["alert_name"] == "DriveDeskIntegrationRetries"
    assert runbooks["integration.dead_letter"]["severity"] == "critical"
    assert runbooks["integration.dead_letter"]["source_statuses"] == ["dead_letter"]
    assert runbooks["integration.reconciliation_mismatch"]["source_type"] == "reconciliation"
    assert runbooks["integration.reconciliation_mismatch"]["source_statuses"] == ["mismatched"]
    assert runbooks["integration.reconciliation_mismatch"]["alert_name"] == (
        "DriveDeskIntegrationReconciliationMismatch"
    )
    assert "provider" in runbooks["integration.reconciliation_mismatch"]["summary"].lower()


def test_business_record_lifecycle_policy_contract() -> None:
    policies = {policy["record_type"]: policy for policy in list_lifecycle_policies()}

    assert set(policies) == {"contract", "document", "lesson", "payment", "task"}
    assert policies["contract"]["initial_status"] == "draft"
    assert "completed" in policies["contract"]["terminal_statuses"]
    assert "confirmed" in policies["payment"]["statuses"]

    accepted = preview_lifecycle_transition("contract", from_status="draft", to_status="approved")
    rejected = preview_lifecycle_transition("contract", from_status="completed", to_status="active")

    assert accepted["valid"] is True
    assert accepted["allowed_next_statuses"] == ["approved", "pending_signature", "cancelled"]
    assert rejected["valid"] is False
    assert rejected["terminal"] is True
    assert rejected["reason"] == "completed is terminal for contract."


def test_api_health_and_ready_endpoints() -> None:
    client = TestClient(build_app())

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_api_integration_adapter_catalog_endpoint() -> None:
    client = TestClient(build_app())

    response = client.get("/integration-adapters")

    assert response.status_code == 200
    payload = {item["key"]: item for item in response.json()}
    assert set(payload) == {
        "accounting.export.mock",
        "crm.bitrix24.mock",
        "file.import.fake",
        "internal.noop",
    }
    assert payload["file.import.fake"]["status"] == "active"
    assert payload["file.import.fake"]["direction"] == "inbound"
    assert payload["file.import.fake"]["connection_profile_supported"] is True
    assert payload["file.import.fake"]["mapping_example"]["external_id"] == "lead_id"
    assert payload["file.import.fake"]["required_mapping_keys"] == ["external_id", "display_name"]
    assert payload["file.import.fake"]["supported_connection_scopes"] == [
        "file_import:execute",
        "file_import:preview",
    ]
    assert payload["file.import.fake"]["default_connection_scopes"] == [
        "file_import:execute",
        "file_import:preview",
    ]
    api_operation_contracts = {item["key"]: item for item in payload["file.import.fake"]["operation_contracts"]}
    assert api_operation_contracts["file_import_preview"]["endpoint"] == (
        "POST /tenants/{tenant_id}/integration-mapping-preview"
    )
    assert api_operation_contracts["file_import_execute"]["idempotency_keys"] == [
        "tenant_id",
        "source_name",
        "source_format",
        "records_hash",
    ]
    assert "field mapping transform" in payload["file.import.fake"]["capabilities"]
    assert "mapping preview" in payload["file.import.fake"]["capabilities"]
    assert "connection scope enforcement" in payload["file.import.fake"]["capabilities"]
    assert "payload validation" in payload["file.import.fake"]["capabilities"]
    assert payload["accounting.export.mock"]["status"] == "active"
    assert payload["accounting.export.mock"]["direction"] == "outbound"
    assert payload["accounting.export.mock"]["supported_connection_scopes"] == ["accounting:export"]
    accounting_api_contracts = {
        item["key"]: item for item in payload["accounting.export.mock"]["operation_contracts"]
    }
    assert accounting_api_contracts["accounting_export_execute"]["idempotency_keys"] == [
        "tenant_id",
        "export_batch_id",
        "documents_hash",
    ]
    assert payload["crm.bitrix24.mock"]["status"] == "active"
    assert payload["crm.bitrix24.mock"]["direction"] == "inbound"
    assert payload["crm.bitrix24.mock"]["supported_connection_scopes"] == [
        "crm:deal.ingest",
        "crm:deal.preview",
    ]
    crm_api_contracts = {
        item["key"]: item for item in payload["crm.bitrix24.mock"]["operation_contracts"]
    }
    assert crm_api_contracts["crm_deal_intake_preview"]["endpoint"] == (
        "POST /tenants/{tenant_id}/business-provider-intake/preview"
    )
    assert crm_api_contracts["crm_deal_ingest_execute"]["idempotency_keys"] == [
        "tenant_id",
        "batch_id",
        "deals_hash",
    ]
    assert payload["crm.bitrix24.mock"]["auth_profile"]["mode"] == "oauth2_or_webhook_boundary"
    assert payload["crm.bitrix24.mock"]["auth_profile"]["public_demo_requires_secret"] is False
    assert payload["crm.bitrix24.mock"]["auth_profile"]["real_provider_requires_secret"] is True
    assert payload["crm.bitrix24.mock"]["auth_profile"]["credential_placement"] == "server_secret_store"
    assert payload["internal.noop"]["direction"] == "internal"


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
    assert "# HELP drivedesk_integration_connection_checks Integration connection health checks by adapter and status." in (
        response.text
    )
    assert "# TYPE drivedesk_integration_connection_checks gauge" in response.text
    assert "# HELP drivedesk_integration_reconciliations Integration reconciliation results by adapter and status." in (
        response.text
    )
    assert "# TYPE drivedesk_integration_reconciliations gauge" in response.text
    assert "# HELP drivedesk_integration_incidents Integration incidents by adapter, severity, and status." in (
        response.text
    )
    assert "# TYPE drivedesk_integration_incidents gauge" in response.text


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
    assert "# HELP drivedesk_integration_connection_checks Integration connection health checks by adapter and status." in (
        response.text
    )
    assert "# HELP drivedesk_integration_reconciliations Integration reconciliation results by adapter and status." in (
        response.text
    )
    assert "# HELP drivedesk_integration_incidents Integration incidents by adapter, severity, and status." in (
        response.text
    )


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
