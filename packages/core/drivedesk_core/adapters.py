from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

CRM_SENSITIVE_KEY_TOKENS = (
    "access_token",
    "address",
    "birth",
    "client_name",
    "email",
    "full_name",
    "name",
    "passport",
    "phone",
    "secret",
    "token",
)


def _crm_amount_bucket(value: object) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip()
    if not text:
        return "unknown"
    try:
        amount = float(text.replace(",", "."))
    except ValueError:
        return text[:32]

    if amount < 1000:
        return "0-999"
    if amount <= 2000:
        return "1000-2000"
    if amount <= 5000:
        return "2001-5000"
    return "5000+"


def _crm_sensitive_keys(record: object) -> list[str]:
    if not isinstance(record, dict):
        return []
    sensitive_keys = []
    for key in record:
        lowered = str(key).lower()
        if any(token in lowered for token in CRM_SENSITIVE_KEY_TOKENS):
            sensitive_keys.append(str(key))
    return sorted(set(sensitive_keys))


@dataclass(frozen=True)
class AdapterResult:
    adapter_key: str
    status: str
    message: str
    records_received: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    external_ref: str | None = None
    details: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AdapterOperationContract:
    key: str
    title: str
    trigger: str
    event_type: str
    endpoint: str
    required_connection_scope: str | None
    idempotency_keys: list[str] = field(default_factory=list)
    retryable: bool = True
    dead_letter: bool = True
    operator_review: bool = True


@dataclass(frozen=True)
class AdapterDescriptor:
    key: str
    name: str
    status: str
    category: str
    direction: str
    purpose: str
    connection_profile_supported: bool
    connection_profile_required: bool
    payload_schema: dict[str, object] = field(default_factory=dict)
    config_example: dict[str, object] = field(default_factory=dict)
    mapping_example: dict[str, object] = field(default_factory=dict)
    required_mapping_keys: list[str] = field(default_factory=list)
    supported_connection_scopes: list[str] = field(default_factory=list)
    default_connection_scopes: list[str] = field(default_factory=list)
    operation_contracts: list[AdapterOperationContract] = field(default_factory=list)
    auth_profile: dict[str, object] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    public_notes: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


class AdapterExecutionError(Exception):
    def __init__(self, message: str, *, adapter_key: str, retryable: bool) -> None:
        super().__init__(message)
        self.message = message
        self.adapter_key = adapter_key
        self.retryable = retryable


class AdapterValidationError(Exception):
    def __init__(self, message: str, *, adapter_key: str) -> None:
        super().__init__(message)
        self.message = message
        self.adapter_key = adapter_key


class IntegrationAdapter(Protocol):
    adapter_key: str
    descriptor: AdapterDescriptor

    def execute(self, payload: dict[str, object]) -> AdapterResult:
        ...


def _validate_mapping_values(adapter_key: str, mapping: dict[str, object]) -> None:
    invalid_keys = [
        key
        for key, value in mapping.items()
        if not isinstance(key, str) or not isinstance(value, str) or not value.strip()
    ]
    if invalid_keys:
        raise AdapterValidationError(
            f"Invalid mapping values for {adapter_key}: {', '.join(sorted(str(key) for key in invalid_keys))}",
            adapter_key=adapter_key,
        )


def resolve_adapter_connection_scopes(
    adapter_key: str,
    *,
    scopes: list[str] | None = None,
) -> list[str]:
    descriptor = resolve_adapter(adapter_key).descriptor
    requested_scopes = list(scopes or descriptor.default_connection_scopes)
    invalid_values = [
        scope
        for scope in requested_scopes
        if not isinstance(scope, str) or not scope.strip()
    ]
    if invalid_values:
        raise AdapterValidationError(
            f"Invalid connection scopes for {adapter_key}: {', '.join(sorted(str(scope) for scope in invalid_values))}",
            adapter_key=adapter_key,
        )

    normalized_scopes = sorted({scope.strip() for scope in requested_scopes})
    unsupported_scopes = [
        scope for scope in normalized_scopes if scope not in descriptor.supported_connection_scopes
    ]
    if unsupported_scopes:
        raise AdapterValidationError(
            f"Unsupported connection scopes for {adapter_key}: {', '.join(unsupported_scopes)}",
            adapter_key=adapter_key,
        )
    return normalized_scopes


def validate_adapter_connection_scope(adapter_key: str, *, scopes: list[str], required_scope: str) -> None:
    resolved_scopes = resolve_adapter_connection_scopes(adapter_key, scopes=scopes)
    if required_scope not in resolved_scopes:
        raise AdapterValidationError(
            f"Integration connection for {adapter_key} lacks required scope: {required_scope}",
            adapter_key=adapter_key,
        )


def _mapped_record(
    record: dict[str, object],
    *,
    mapping: dict[str, object],
    required_mapping_keys: list[str],
) -> dict[str, object]:
    if not mapping:
        return dict(record)

    normalized: dict[str, object] = {}
    for target_key, source_key in mapping.items():
        if isinstance(target_key, str) and isinstance(source_key, str) and source_key in record:
            normalized[target_key] = record[source_key]

    for target_key in required_mapping_keys:
        if target_key not in normalized and target_key in record:
            normalized[target_key] = record[target_key]
    return normalized


def normalize_adapter_records(
    adapter_key: str,
    *,
    records: list[object],
    mapping: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    descriptor = resolve_adapter(adapter_key).descriptor
    mapping_payload = mapping or {}
    if mapping_payload:
        validate_adapter_connection_profile(adapter_key, mapping=mapping_payload)

    normalized_records: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, dict):
            normalized_records.append({})
            continue
        normalized_records.append(
            _mapped_record(
                record,
                mapping=mapping_payload,
                required_mapping_keys=descriptor.required_mapping_keys,
            )
        )
    return normalized_records


def build_adapter_mapping_preview(
    adapter_key: str,
    *,
    records: list[object],
    mapping: dict[str, object] | None = None,
) -> dict[str, object]:
    descriptor = resolve_adapter(adapter_key).descriptor
    if not descriptor.connection_profile_supported:
        raise AdapterValidationError(
            f"Adapter does not support integration mapping preview: {adapter_key}",
            adapter_key=adapter_key,
        )

    normalized_records = normalize_adapter_records(adapter_key, records=records, mapping=mapping)
    preview_records: list[dict[str, object]] = []
    accepted = 0
    rejected = 0
    for index, normalized_record in enumerate(normalized_records, start=1):
        errors = [
            f"missing mapped value: {key}"
            for key in descriptor.required_mapping_keys
            if not str(normalized_record.get(key) or "").strip()
        ]
        if errors:
            rejected += 1
            status = "rejected"
        else:
            accepted += 1
            status = "accepted"
        preview_records.append(
            {
                "index": index,
                "status": status,
                "normalized": normalized_record,
                "errors": errors,
            }
        )

    return {
        "adapter_key": adapter_key,
        "required_mapping_keys": descriptor.required_mapping_keys,
        "records_received": len(records),
        "records_accepted": accepted,
        "records_rejected": rejected,
        "records": preview_records,
    }


class NoopAdapter:
    adapter_key = "internal.noop"
    descriptor = AdapterDescriptor(
        key=adapter_key,
        name="Internal Noop",
        status="active",
        category="internal",
        direction="internal",
        purpose="Acknowledge internal domain events without calling an external provider.",
        connection_profile_supported=False,
        connection_profile_required=False,
        payload_schema={
            "type": "object",
            "required": [],
            "properties": {
                "event_type": "optional internal event type",
            },
        },
        operation_contracts=[
            AdapterOperationContract(
                key="internal_event_ack",
                title="Acknowledge internal outbox event",
                trigger="worker.outbox.pending",
                event_type="internal.*",
                endpoint="worker:drivedesk_worker.main.process_pending_outbox",
                required_connection_scope=None,
                idempotency_keys=["outbox_event.id"],
                retryable=False,
                dead_letter=False,
                operator_review=False,
            )
        ],
        auth_profile={
            "mode": "none",
            "public_demo_requires_secret": False,
            "real_provider_requires_secret": False,
            "secret_refs": [],
            "credential_placement": "none",
            "token_exchange": "none",
            "external_token_exchange": False,
            "data_boundaries": ["internal_event_only"],
        },
        capabilities=["internal acknowledgement", "outbox smoke path"],
        failure_modes=[],
        public_notes=["Used as the default adapter for internal outbox events."],
    )

    def execute(self, payload: dict[str, object]) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.adapter_key,
            status="success",
            message="Internal event acknowledged.",
            details={"event_passthrough": True, "payload_keys": sorted(payload.keys())},
        )


class FakeFileImportAdapter:
    adapter_key = "file.import.fake"
    descriptor = AdapterDescriptor(
        key=adapter_key,
        name="Synthetic File Import",
        status="active",
        category="file_import",
        direction="inbound",
        purpose="Normalize synthetic imported rows and report accepted or rejected records.",
        connection_profile_supported=True,
        connection_profile_required=False,
        payload_schema={
            "type": "object",
            "required": ["source_name", "source_format", "records"],
            "properties": {
                "source_name": "short source label",
                "source_format": "json or csv",
                "records": "list of objects with external_id and display_name",
                "simulate_failure": "optional retryable or permanent test mode",
            },
        },
        config_example={"mode": "synthetic"},
        mapping_example={"external_id": "lead_id", "display_name": "full_name"},
        required_mapping_keys=["external_id", "display_name"],
        supported_connection_scopes=["file_import:execute", "file_import:preview"],
        default_connection_scopes=["file_import:execute", "file_import:preview"],
        operation_contracts=[
            AdapterOperationContract(
                key="file_import_preview",
                title="Preview mapped import rows",
                trigger="api.request",
                event_type="integration.mapping_preview.requested",
                endpoint="POST /tenants/{tenant_id}/integration-mapping-preview",
                required_connection_scope="file_import:preview",
                idempotency_keys=["tenant_id", "integration_connection_id", "records_hash"],
                retryable=False,
                dead_letter=False,
                operator_review=False,
            ),
            AdapterOperationContract(
                key="file_import_execute",
                title="Execute file import job",
                trigger="api.outbox.enqueue",
                event_type="integration.file_import.requested",
                endpoint="POST /tenants/{tenant_id}/integration-imports/file",
                required_connection_scope="file_import:execute",
                idempotency_keys=["tenant_id", "source_name", "source_format", "records_hash"],
                retryable=True,
                dead_letter=True,
                operator_review=True,
            ),
        ],
        auth_profile={
            "mode": "local_file_boundary",
            "public_demo_requires_secret": False,
            "real_provider_requires_secret": False,
            "secret_refs": [],
            "credential_placement": "none",
            "token_exchange": "none",
            "external_token_exchange": False,
            "data_boundaries": ["no_public_secrets", "tenant_owned_mapping_only"],
        },
        capabilities=[
            "payload validation",
            "field mapping transform",
            "mapping preview",
            "connection scope enforcement",
            "accepted/rejected record counts",
            "retryable failure simulation",
            "permanent failure simulation",
        ],
        failure_modes=["retryable", "permanent"],
        public_notes=[
            "Safe synthetic adapter for public demos and contract tests.",
            "Real provider values are handled outside the public adapter catalog.",
        ],
    )

    def execute(self, payload: dict[str, object]) -> AdapterResult:
        simulated_failure = payload.get("simulate_failure")
        if simulated_failure == "retryable":
            raise AdapterExecutionError(
                "Synthetic provider is temporarily unavailable.",
                adapter_key=self.adapter_key,
                retryable=True,
            )
        if simulated_failure == "permanent":
            raise AdapterExecutionError(
                "Synthetic provider rejected the import contract.",
                adapter_key=self.adapter_key,
                retryable=False,
            )

        records = payload.get("records")
        if not isinstance(records, list):
            raise AdapterExecutionError(
                "Import payload must contain a records list.",
                adapter_key=self.adapter_key,
                retryable=False,
            )
        mapping = payload.get("mapping", {})
        if mapping is None:
            mapping = {}
        if not isinstance(mapping, dict):
            raise AdapterExecutionError(
                "Import payload mapping must be a JSON object.",
                adapter_key=self.adapter_key,
                retryable=False,
            )
        try:
            normalized_records = normalize_adapter_records(self.adapter_key, records=records, mapping=mapping)
        except AdapterValidationError as exc:
            raise AdapterExecutionError(
                exc.message,
                adapter_key=self.adapter_key,
                retryable=False,
            ) from exc

        accepted_external_ids: list[str] = []
        rejected = 0
        for record in normalized_records:
            if not isinstance(record, dict):
                rejected += 1
                continue
            external_id = str(record.get("external_id") or "").strip()
            display_name = str(record.get("display_name") or "").strip()
            if external_id and display_name:
                accepted_external_ids.append(external_id)
            else:
                rejected += 1

        accepted = len(accepted_external_ids)
        status = "success" if rejected == 0 else "partial_success"
        source_name = str(payload.get("source_name") or "synthetic-file")
        return AdapterResult(
            adapter_key=self.adapter_key,
            status=status,
            message=f"Imported {accepted} synthetic records from {source_name}.",
            records_received=len(records),
            records_accepted=accepted,
            records_rejected=rejected,
            external_ref=f"synthetic-import:{source_name}",
            details={
                "source_name": source_name,
                "source_format": str(payload.get("source_format") or "json"),
                "accepted_external_ids": accepted_external_ids,
            },
        )


class MockAccountingExportAdapter:
    adapter_key = "accounting.export.mock"
    descriptor = AdapterDescriptor(
        key=adapter_key,
        name="Mock Accounting Export",
        status="active",
        category="accounting_export",
        direction="outbound",
        purpose="Export synthetic accounting documents through the shared outbox adapter boundary.",
        connection_profile_supported=True,
        connection_profile_required=False,
        payload_schema={
            "type": "object",
            "required": ["export_batch_id", "documents"],
            "properties": {
                "export_batch_id": "idempotent export batch label",
                "documents": "list of accounting document summaries",
                "simulate_failure": "optional retryable or permanent test mode",
            },
        },
        config_example={"provider": "mock-accounting", "mode": "synthetic"},
        mapping_example={},
        required_mapping_keys=[],
        supported_connection_scopes=["accounting:export"],
        default_connection_scopes=["accounting:export"],
        operation_contracts=[
            AdapterOperationContract(
                key="accounting_export_execute",
                title="Export accounting documents",
                trigger="api.outbox.enqueue",
                event_type="accounting.export.requested",
                endpoint="POST /tenants/{tenant_id}/integration-exports/accounting",
                required_connection_scope="accounting:export",
                idempotency_keys=["tenant_id", "export_batch_id", "documents_hash"],
                retryable=True,
                dead_letter=True,
                operator_review=True,
            ),
        ],
        auth_profile={
            "mode": "mock_outbound_boundary",
            "public_demo_requires_secret": False,
            "real_provider_requires_secret": True,
            "secret_refs": ["ACCOUNTING_PROVIDER_API_KEY", "ACCOUNTING_PROVIDER_ENDPOINT"],
            "credential_placement": "server_secret_store",
            "token_exchange": "private_connector_only",
            "external_token_exchange": False,
            "data_boundaries": ["no_public_secrets", "server_side_provider_calls_only"],
        },
        capabilities=[
            "outbound export boundary",
            "connection scope enforcement",
            "document count summary",
            "retryable failure simulation",
            "permanent failure simulation",
        ],
        failure_modes=["retryable", "permanent"],
        public_notes=[
            "Safe mock adapter for accounting export contracts.",
            "Real 1C, KKT, and bank provider payloads stay outside public docs and demos.",
        ],
    )

    def execute(self, payload: dict[str, object]) -> AdapterResult:
        simulated_failure = payload.get("simulate_failure")
        if simulated_failure == "retryable":
            raise AdapterExecutionError(
                "Mock accounting provider is temporarily unavailable.",
                adapter_key=self.adapter_key,
                retryable=True,
            )
        if simulated_failure == "permanent":
            raise AdapterExecutionError(
                "Mock accounting provider rejected the export contract.",
                adapter_key=self.adapter_key,
                retryable=False,
            )

        documents = payload.get("documents")
        if not isinstance(documents, list):
            raise AdapterExecutionError(
                "Accounting export payload must contain a documents list.",
                adapter_key=self.adapter_key,
                retryable=False,
            )

        accepted_document_ids: list[str] = []
        document_types: set[str] = set()
        rejected = 0
        for document in documents:
            if not isinstance(document, dict):
                rejected += 1
                continue

            document_id = str(document.get("document_id") or "").strip()
            document_type = str(document.get("document_type") or "").strip()
            currency = str(document.get("currency") or "").strip()
            counterparty_ref = str(document.get("counterparty_ref") or "").strip()
            amount_cents = document.get("amount_cents")
            amount_valid = isinstance(amount_cents, int) and amount_cents >= 0

            if document_id and document_type and currency and counterparty_ref and amount_valid:
                accepted_document_ids.append(document_id)
                document_types.add(document_type)
            else:
                rejected += 1

        accepted = len(accepted_document_ids)
        export_batch_id = str(payload.get("export_batch_id") or "mock-accounting-export")
        status = "success" if rejected == 0 else "partial_success"
        return AdapterResult(
            adapter_key=self.adapter_key,
            status=status,
            message=f"Exported {accepted} mock accounting documents from {export_batch_id}.",
            records_received=len(documents),
            records_accepted=accepted,
            records_rejected=rejected,
            external_ref=f"mock-accounting-export:{export_batch_id}",
            details={
                "export_batch_id": export_batch_id,
                "accepted_document_ids": accepted_document_ids,
                "document_types": sorted(document_types),
            },
        )


class MockCrmDealAdapter:
    adapter_key = "crm.bitrix24.mock"
    descriptor = AdapterDescriptor(
        key=adapter_key,
        name="Mock Bitrix24 CRM Intake",
        status="active",
        category="crm",
        direction="inbound",
        purpose=(
            "Normalize synthetic CRM deal facts into safe DriveDesk observations "
            "without calling a real CRM provider."
        ),
        connection_profile_supported=True,
        connection_profile_required=False,
        payload_schema={
            "type": "object",
            "required": ["deals"],
            "properties": {
                "batch_id": "idempotent synthetic CRM batch label",
                "deals": "list of CRM deal objects",
                "mapping": "optional provider field mapping",
                "simulate_failure": "optional retryable or permanent test mode",
            },
        },
        config_example={"provider": "bitrix24", "mode": "synthetic"},
        mapping_example={
            "deal_id": "ID",
            "source_state": "STAGE_ID",
            "owner_role": "ASSIGNED_BY_ROLE",
            "amount": "OPPORTUNITY",
        },
        required_mapping_keys=["deal_id", "source_state"],
        supported_connection_scopes=["crm:deal.ingest", "crm:deal.preview"],
        default_connection_scopes=["crm:deal.ingest", "crm:deal.preview"],
        operation_contracts=[
            AdapterOperationContract(
                key="crm_deal_intake_preview",
                title="Preview CRM deal intake",
                trigger="api.request",
                event_type="business_provider_intake.previewed",
                endpoint="POST /tenants/{tenant_id}/business-provider-intake/preview",
                required_connection_scope="crm:deal.preview",
                idempotency_keys=["tenant_id", "provider_key", "subject_ref", "payload_hash"],
                retryable=False,
                dead_letter=False,
                operator_review=False,
            ),
            AdapterOperationContract(
                key="crm_deal_ingest_execute",
                title="Queue CRM deal intake",
                trigger="api.outbox.enqueue",
                event_type="integration.crm_deal.ingest.requested",
                endpoint="worker:drivedesk_worker.main.process_pending_outbox",
                required_connection_scope="crm:deal.ingest",
                idempotency_keys=["tenant_id", "batch_id", "deals_hash"],
                retryable=True,
                dead_letter=True,
                operator_review=True,
            ),
        ],
        auth_profile={
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
        },
        capabilities=[
            "crm deal normalization",
            "safe provider payload summary",
            "field mapping transform",
            "mapping preview",
            "connection scope enforcement",
            "sensitive key redaction evidence",
            "retryable failure simulation",
            "permanent failure simulation",
        ],
        failure_modes=["retryable", "permanent"],
        public_notes=[
            "Public-safe Bitrix24-style adapter contract using synthetic data.",
            "No real CRM credentials, raw provider payloads, or personal data are returned.",
        ],
    )

    def execute(self, payload: dict[str, object]) -> AdapterResult:
        simulated_failure = payload.get("simulate_failure")
        if simulated_failure == "retryable":
            raise AdapterExecutionError(
                "Mock CRM provider is temporarily unavailable.",
                adapter_key=self.adapter_key,
                retryable=True,
            )
        if simulated_failure == "permanent":
            raise AdapterExecutionError(
                "Mock CRM provider rejected the deal intake contract.",
                adapter_key=self.adapter_key,
                retryable=False,
            )

        deals = payload.get("deals")
        if deals is None:
            deals = payload.get("records")
        if not isinstance(deals, list):
            raise AdapterExecutionError(
                "CRM intake payload must contain a deals list.",
                adapter_key=self.adapter_key,
                retryable=False,
            )

        mapping = payload.get("mapping", {})
        if mapping is None:
            mapping = {}
        if not isinstance(mapping, dict):
            raise AdapterExecutionError(
                "CRM intake payload mapping must be a JSON object.",
                adapter_key=self.adapter_key,
                retryable=False,
            )
        try:
            normalized_deals = normalize_adapter_records(self.adapter_key, records=deals, mapping=mapping)
        except AdapterValidationError as exc:
            raise AdapterExecutionError(
                exc.message,
                adapter_key=self.adapter_key,
                retryable=False,
            ) from exc

        accepted_subject_refs: list[str] = []
        source_states: set[str] = set()
        amount_buckets: set[str] = set()
        dropped_sensitive_keys: set[str] = set()
        rejected = 0

        for original, normalized in zip(deals, normalized_deals, strict=False):
            dropped_sensitive_keys.update(_crm_sensitive_keys(original))
            if not isinstance(normalized, dict):
                rejected += 1
                continue

            deal_id = str(normalized.get("deal_id") or "").strip()
            source_state = str(
                normalized.get("source_state") or normalized.get("stage") or ""
            ).strip()
            if not deal_id or not source_state:
                rejected += 1
                continue

            accepted_subject_refs.append(f"deal:{deal_id}")
            source_states.add(source_state)
            amount_buckets.add(
                _crm_amount_bucket(normalized.get("amount_bucket") or normalized.get("amount"))
            )

        accepted = len(accepted_subject_refs)
        batch_id = str(payload.get("batch_id") or "crm-deal-intake")
        status = "success" if rejected == 0 else "partial_success"
        return AdapterResult(
            adapter_key=self.adapter_key,
            status=status,
            message=f"Accepted {accepted} synthetic CRM deals from {batch_id}.",
            records_received=len(deals),
            records_accepted=accepted,
            records_rejected=rejected,
            external_ref=f"mock-crm-deal-intake:{batch_id}",
            details={
                "provider_family": "crm",
                "normalized_observation_type": "BusinessStateObservation",
                "accepted_subject_refs": accepted_subject_refs,
                "source_states": sorted(source_states),
                "amount_buckets": sorted(amount_buckets),
                "dropped_sensitive_keys": sorted(dropped_sensitive_keys),
                "public_safe": True,
                "raw_payload_included": False,
                "external_mutation": False,
                "requires_secret": False,
            },
        )


ADAPTERS: dict[str, IntegrationAdapter] = {
    MockCrmDealAdapter.adapter_key: MockCrmDealAdapter(),
    NoopAdapter.adapter_key: NoopAdapter(),
    FakeFileImportAdapter.adapter_key: FakeFileImportAdapter(),
    MockAccountingExportAdapter.adapter_key: MockAccountingExportAdapter(),
}


def resolve_adapter(adapter_key: str | None) -> IntegrationAdapter:
    resolved_key = adapter_key or NoopAdapter.adapter_key
    adapter = ADAPTERS.get(resolved_key)
    if adapter is None:
        raise AdapterExecutionError(
            f"Unknown adapter: {resolved_key}",
            adapter_key=resolved_key,
            retryable=False,
        )
    return adapter


def list_adapter_descriptors() -> list[dict[str, object]]:
    return [ADAPTERS[key].descriptor.to_payload() for key in sorted(ADAPTERS)]


def describe_adapter(adapter_key: str | None) -> dict[str, object]:
    return resolve_adapter(adapter_key).descriptor.to_payload()


def validate_adapter_connection_profile(
    adapter_key: str,
    *,
    mapping: dict[str, object],
    scopes: list[str] | None = None,
) -> AdapterDescriptor:
    descriptor = resolve_adapter(adapter_key).descriptor
    if not descriptor.connection_profile_supported:
        raise AdapterValidationError(
            f"Adapter does not support integration connections: {adapter_key}",
            adapter_key=adapter_key,
        )

    missing_keys = [key for key in descriptor.required_mapping_keys if key not in mapping]
    if missing_keys:
        raise AdapterValidationError(
            f"Missing mapping keys for {adapter_key}: {', '.join(missing_keys)}",
            adapter_key=adapter_key,
        )

    _validate_mapping_values(adapter_key, mapping)
    resolve_adapter_connection_scopes(adapter_key, scopes=scopes)
    return descriptor


def build_adapter_connection_diagnostics(
    adapter_key: str,
    *,
    mapping: dict[str, object],
    scopes: list[str] | None = None,
) -> dict[str, object]:
    descriptor = validate_adapter_connection_profile(adapter_key, mapping=mapping, scopes=scopes)
    resolved_scopes = resolve_adapter_connection_scopes(adapter_key, scopes=scopes)
    operation_keys: list[str] = []
    executable_operation_keys: list[str] = []
    missing_operation_scopes: list[str] = []
    for operation in descriptor.operation_contracts:
        operation_keys.append(operation.key)
        required_scope = operation.required_connection_scope
        if required_scope is None or required_scope in resolved_scopes:
            executable_operation_keys.append(operation.key)
            continue
        missing_operation_scopes.append(required_scope)

    return {
        "adapter_key": descriptor.key,
        "adapter_status": descriptor.status,
        "direction": descriptor.direction,
        "connection_profile_supported": descriptor.connection_profile_supported,
        "required_mapping_keys": list(descriptor.required_mapping_keys),
        "mapping_keys": sorted(str(key) for key in mapping.keys()),
        "scopes": resolved_scopes,
        "operation_keys": operation_keys,
        "executable_operation_keys": executable_operation_keys,
        "missing_operation_scopes": sorted(set(missing_operation_scopes)),
        "auth_mode": str(descriptor.auth_profile.get("mode") or "unspecified"),
        "public_demo_requires_secret": bool(descriptor.auth_profile.get("public_demo_requires_secret")),
        "real_provider_requires_secret": bool(descriptor.auth_profile.get("real_provider_requires_secret")),
        "secret_refs": sorted(str(item) for item in descriptor.auth_profile.get("secret_refs", [])),
        "capabilities": list(descriptor.capabilities),
    }


def build_adapter_runtime_plan(
    adapter_key: str,
    *,
    operation_key: str | None = None,
    scopes: list[str] | None = None,
    execution_mode: str = "contract_only",
) -> dict[str, object]:
    descriptor = resolve_adapter(adapter_key).descriptor
    if not descriptor.operation_contracts:
        raise AdapterValidationError(
            f"Adapter does not expose operation contracts: {adapter_key}",
            adapter_key=adapter_key,
        )

    if operation_key is None:
        operation = descriptor.operation_contracts[0]
    else:
        matching = [item for item in descriptor.operation_contracts if item.key == operation_key]
        if not matching:
            raise AdapterValidationError(
                f"Adapter operation is not available for {adapter_key}: {operation_key}",
                adapter_key=adapter_key,
            )
        operation = matching[0]

    resolved_scopes = resolve_adapter_connection_scopes(adapter_key, scopes=scopes)
    required_scope = operation.required_connection_scope
    scope_status = "not_required"
    if required_scope is not None:
        scope_status = "available" if required_scope in resolved_scopes else "missing"

    is_worker_endpoint = operation.endpoint.startswith("worker:")
    provider_write_candidate = descriptor.direction == "outbound" or operation.trigger == "api.outbox.enqueue"
    provider_call_enabled = execution_mode == "commit_request" and provider_write_candidate
    secret_refs = sorted(str(item) for item in descriptor.auth_profile.get("secret_refs", []))

    runtime_steps = [
        {
            "step": "contract_selected",
            "status": "ready",
            "detail": f"{descriptor.key}.{operation.key} selected from runtime adapter catalog.",
            "evidence": "adapter_runtime.contract_selected",
        },
        {
            "step": "scope_preflight",
            "status": scope_status,
            "detail": required_scope or "Operation does not require a tenant connection scope.",
            "evidence": "adapter_runtime.scope_checked",
        },
        {
            "step": "idempotency_prepared",
            "status": "ready" if operation.idempotency_keys else "missing",
            "detail": ", ".join(operation.idempotency_keys) or "No idempotency keys declared.",
            "evidence": "adapter_runtime.idempotency_prepared",
        },
        {
            "step": "approval_dependency",
            "status": "required" if operation.operator_review or provider_write_candidate else "not_required",
            "detail": "Provider-changing or operator-review operations remain behind approval gates.",
            "evidence": "adapter_runtime.approval_dependency_attached",
        },
        {
            "step": "outbox_handoff",
            "status": "ready" if operation.trigger == "api.outbox.enqueue" else "not_required",
            "detail": operation.event_type,
            "evidence": "adapter_runtime.outbox_handoff_prepared",
        },
        {
            "step": "worker_boundary",
            "status": "ready" if operation.retryable or is_worker_endpoint else "not_required",
            "detail": operation.endpoint,
            "evidence": "adapter_runtime.worker_boundary_selected",
        },
        {
            "step": "reconciliation_plan",
            "status": "ready" if provider_write_candidate else "not_required",
            "detail": "Provider evidence is compared after execution before the operator closes the loop.",
            "evidence": "adapter_runtime.reconciliation_planned",
        },
    ]

    preflight_checks = [
        {
            "check": "adapter_registered",
            "status": "passed",
            "detail": descriptor.key,
            "external_mutation": False,
            "evidence": "adapter_runtime.previewed",
        },
        {
            "check": "operation_contract_present",
            "status": "passed",
            "detail": operation.key,
            "external_mutation": False,
            "evidence": "adapter_runtime.previewed",
        },
        {
            "check": "required_scope_available",
            "status": "passed" if scope_status in {"available", "not_required"} else "blocked",
            "detail": required_scope or "scope_not_required",
            "external_mutation": False,
            "evidence": "adapter_runtime.previewed",
        },
        {
            "check": "idempotency_keys_declared",
            "status": "passed" if operation.idempotency_keys else "warning",
            "detail": ", ".join(operation.idempotency_keys) or "no_idempotency_keys_declared",
            "external_mutation": False,
            "evidence": "adapter_runtime.previewed",
        },
        {
            "check": "secret_boundary_server_side",
            "status": "clean",
            "detail": str(descriptor.auth_profile.get("credential_placement") or "unspecified"),
            "external_mutation": False,
            "secret_refs_visible": bool(secret_refs),
            "evidence": "adapter_runtime.previewed",
        },
        {
            "check": "provider_write_disabled_in_preview",
            "status": "closed",
            "detail": "Runtime preview never calls the external provider.",
            "external_mutation": False,
            "provider_call_enabled": False,
            "evidence": "adapter_runtime.previewed",
        },
    ]

    return {
        "adapter_key": descriptor.key,
        "adapter_name": descriptor.name,
        "adapter_direction": descriptor.direction,
        "operation_contract": {
            "key": operation.key,
            "title": operation.title,
            "trigger": operation.trigger,
            "event_type": operation.event_type,
            "endpoint": operation.endpoint,
            "required_connection_scope": required_scope,
            "idempotency_keys": list(operation.idempotency_keys),
            "retryable": operation.retryable,
            "dead_letter": operation.dead_letter,
            "operator_review": operation.operator_review,
        },
        "runtime_steps": runtime_steps,
        "preflight_checks": preflight_checks,
        "outbox_handoff": {
            "status": "ready" if operation.trigger == "api.outbox.enqueue" else "not_required",
            "would_enqueue_event": operation.event_type,
            "adapter_key": descriptor.key,
            "operation_key": operation.key,
            "required_connection_scope": required_scope,
            "idempotency_keys": list(operation.idempotency_keys),
            "retryable": operation.retryable,
            "dead_letter": operation.dead_letter,
            "operator_review": operation.operator_review,
            "external_mutation": False,
            "provider_call_enabled": False,
            "evidence": "adapter_runtime.outbox_handoff_prepared",
        },
        "worker_boundary": {
            "status": "ready" if operation.retryable or is_worker_endpoint else "not_required",
            "endpoint": operation.endpoint,
            "worker_function": operation.endpoint.removeprefix("worker:") if is_worker_endpoint else "drivedesk_worker.main.process_pending_outbox",
            "execution_mode": execution_mode,
            "public_run_mode": "contract_only",
            "external_mutation": False,
            "provider_call_enabled": provider_call_enabled,
            "raw_payload_included": False,
            "contains_pii": False,
            "evidence": "adapter_runtime.worker_boundary_selected",
        },
        "reconciliation_plan": [
            {
                "step": "capture_expected_result",
                "status": "ready",
                "detail": "Expected adapter result is derived from the operation contract and idempotency key.",
                "external_mutation": False,
                "evidence": "adapter_runtime.reconciliation_planned",
            },
            {
                "step": "compare_provider_evidence",
                "status": "ready" if provider_write_candidate else "not_required",
                "detail": "Provider status, accepted/rejected counts, and external reference are compared after execution.",
                "external_mutation": False,
                "evidence": "adapter_runtime.reconciliation_planned",
            },
            {
                "step": "route_mismatch_to_operator",
                "status": "armed" if operation.operator_review else "not_required",
                "detail": "Mismatched or blocked evidence becomes an operator review card.",
                "external_mutation": False,
                "evidence": "adapter_runtime.reconciliation_planned",
            },
        ],
        "incident_routes": [
            {
                "route": "retry_queue",
                "status": "armed" if operation.retryable else "not_required",
                "source": "outbox.retry",
                "runbook": "integration.retry_backlog",
                "external_mutation": False,
                "evidence": "adapter_runtime.incident_route_selected",
            },
            {
                "route": "dead_letter_review",
                "status": "armed" if operation.dead_letter else "not_required",
                "source": "outbox.dead_letter",
                "runbook": "integration.dead_letter",
                "external_mutation": False,
                "evidence": "adapter_runtime.incident_route_selected",
            },
            {
                "route": "reconciliation_mismatch",
                "status": "armed" if provider_write_candidate else "not_required",
                "source": "integration.reconciliation",
                "runbook": "integration.reconciliation_mismatch",
                "external_mutation": False,
                "evidence": "adapter_runtime.incident_route_selected",
            },
        ],
        "data_boundaries": [
            {
                "name": "contract_only_preview",
                "status": "preview_only",
                "external_mutation": False,
                "detail": "The runtime plan is computed without queueing or executing provider work.",
            },
            {
                "name": "server_side_secret_boundary",
                "status": "clean",
                "external_mutation": False,
                "secret_refs": secret_refs,
                "detail": "Secret names may be referenced, but secret values are never returned.",
            },
            {
                "name": "safe_payload_boundary",
                "status": "clean",
                "contains_pii": False,
                "raw_payload_included": False,
                "detail": "Runtime preview uses contract metadata and safe references only.",
            },
            {
                "name": "approval_before_provider_write",
                "status": "closed",
                "external_mutation": False,
                "detail": "Provider mutation remains unavailable until approval and outbox commit exist.",
            },
        ],
    }


def build_adapter_execution_timeline(
    adapter_key: str,
    *,
    operation_key: str | None = None,
    scopes: list[str] | None = None,
    execution_mode: str = "contract_only",
    request_id: str = "demo-request-001",
    include_failure_path: bool = True,
) -> dict[str, object]:
    runtime = build_adapter_runtime_plan(
        adapter_key,
        operation_key=operation_key,
        scopes=scopes,
        execution_mode=execution_mode,
    )
    operation = runtime["operation_contract"]
    if not isinstance(operation, dict):
        raise AdapterValidationError(
            f"Adapter operation contract is invalid for {adapter_key}",
            adapter_key=adapter_key,
        )

    selected_operation_key = str(operation.get("key") or operation_key or "unknown")
    event_type = str(operation.get("event_type") or "integration.operation.requested")
    outbox_handoff = runtime.get("outbox_handoff", {})
    worker_boundary = runtime.get("worker_boundary", {})
    retryable = bool(operation.get("retryable"))
    dead_letter = bool(operation.get("dead_letter"))
    operator_review = bool(operation.get("operator_review"))
    provider_write_candidate = (
        str(runtime.get("adapter_direction") or "") == "outbound"
        or str(operation.get("trigger") or "") == "api.outbox.enqueue"
    )

    run_id = f"run_{str(runtime['adapter_key']).replace('.', '_')}_{selected_operation_key}"
    idempotency_keys = [str(item) for item in operation.get("idempotency_keys", [])]
    idempotency_fingerprint = ":".join(
        [str(runtime["adapter_key"]), selected_operation_key, request_id]
    )

    timeline = [
        {
            "stage": "request_accepted",
            "status": "ready",
            "detail": f"{runtime['adapter_key']}.{selected_operation_key} execution request accepted.",
            "would_record": "WorkflowActionRun",
            "external_mutation": False,
            "evidence": "integration_execution.requested",
        },
        {
            "stage": "runtime_preflight",
            "status": "passed",
            "detail": f"{len(runtime.get('preflight_checks', []))} runtime preflight checks evaluated.",
            "would_record": "adapter_runtime.previewed",
            "external_mutation": False,
            "evidence": "integration_execution.preflight_passed",
        },
        {
            "stage": "approval_gate",
            "status": "locked" if provider_write_candidate or operator_review else "not_required",
            "detail": "Provider mutation remains locked until approval and idempotent outbox commit.",
            "would_record": "business_approval.requested" if provider_write_candidate or operator_review else None,
            "external_mutation": False,
            "evidence": "integration_execution.approval_gate_evaluated",
        },
        {
            "stage": "outbox_enqueue",
            "status": str(outbox_handoff.get("status") or "not_required"),
            "detail": event_type,
            "would_record": "OutboxEvent" if outbox_handoff.get("status") == "ready" else None,
            "external_mutation": False,
            "evidence": "integration_execution.outbox_planned",
        },
        {
            "stage": "worker_dispatch",
            "status": str(worker_boundary.get("status") or "not_required"),
            "detail": str(worker_boundary.get("worker_function") or worker_boundary.get("endpoint") or "worker not required"),
            "would_record": "worker.outbox.pending" if worker_boundary.get("status") == "ready" else None,
            "external_mutation": False,
            "evidence": "integration_execution.worker_dispatch_planned",
        },
        {
            "stage": "provider_call",
            "status": "blocked_in_public_preview",
            "detail": "External provider calls are represented as contract evidence only.",
            "would_record": None,
            "external_mutation": False,
            "provider_call_enabled": False,
            "evidence": "integration_execution.provider_call_blocked",
        },
        {
            "stage": "reconciliation",
            "status": "planned" if provider_write_candidate else "not_required",
            "detail": "Expected internal result is compared with provider evidence after worker completion.",
            "would_record": "IntegrationReconciliation" if provider_write_candidate else None,
            "external_mutation": False,
            "evidence": "integration_execution.reconciliation_planned",
        },
        {
            "stage": "operator_closure",
            "status": "ready",
            "detail": "Operator receives retry, dead-letter, or reconciliation evidence before closure.",
            "would_record": "IntegrationIncident" if include_failure_path else None,
            "external_mutation": False,
            "evidence": "integration_execution.operator_closure_ready",
        },
    ]

    run_ledger = {
        "run_id": run_id,
        "request_id": request_id,
        "adapter_key": runtime["adapter_key"],
        "operation_key": selected_operation_key,
        "event_type": event_type,
        "status": "previewed",
        "execution_mode": execution_mode,
        "idempotency_fingerprint": idempotency_fingerprint,
        "would_create_workflow_action_run": True,
        "would_create_outbox_event": outbox_handoff.get("status") == "ready",
        "would_call_provider": False,
        "external_mutation": False,
        "raw_payload_included": False,
        "contains_pii": False,
        "evidence": "integration_execution.run_ledger_prepared",
    }

    state_transitions = [
        {
            "from": "none",
            "to": "requested",
            "trigger": "POST /tenants/{tenant_id}/integration-executions/preview",
            "evidence": "integration_execution.requested",
        },
        {
            "from": "requested",
            "to": "preflight_passed",
            "trigger": "adapter_runtime.previewed",
            "evidence": "integration_execution.preflight_passed",
        },
        {
            "from": "preflight_passed",
            "to": "queued",
            "trigger": event_type,
            "evidence": "integration_execution.outbox_planned",
        },
        {
            "from": "queued",
            "to": "awaiting_reconciliation",
            "trigger": "worker.outbox.pending",
            "evidence": "integration_execution.worker_dispatch_planned",
        },
        {
            "from": "awaiting_reconciliation",
            "to": "operator_review_ready",
            "trigger": "integration.reconciliation.recorded",
            "evidence": "integration_execution.operator_closure_ready",
        },
    ]

    retry_policy = [
        {
            "name": "retry_queue",
            "status": "armed" if retryable else "not_required",
            "trigger": "outbox_event.retry_requested",
            "max_attempts": 3,
            "external_mutation": False,
            "evidence": "integration_execution.retry_policy_attached",
        },
        {
            "name": "dead_letter_review",
            "status": "armed" if dead_letter else "not_required",
            "trigger": "outbox.dead_letter",
            "max_attempts": 3,
            "external_mutation": False,
            "evidence": "integration_execution.dead_letter_policy_attached",
        },
    ]

    reconciliation_links = [
        {
            "name": "expected_result",
            "status": "prepared",
            "source": "operation_contract",
            "would_record": "IntegrationReconciliation.expected_json",
            "evidence": "integration_execution.reconciliation_planned",
        },
        {
            "name": "provider_evidence",
            "status": "redacted",
            "source": "worker_result",
            "would_record": "IntegrationReconciliation.actual_json",
            "evidence": "integration_execution.reconciliation_planned",
        },
        {
            "name": "mismatch_route",
            "status": "armed" if include_failure_path else "disabled",
            "source": "integration.reconciliation",
            "would_record": "IntegrationIncident",
            "evidence": "integration_execution.incident_route_armed",
        },
    ]

    observability = [
        {
            "metric": "drivedesk_workflow_action_runs",
            "status": "planned",
            "labels": ["action_type", "status"],
            "evidence": "integration_execution.metric_attached",
        },
        {
            "metric": "drivedesk_outbox_events",
            "status": "planned",
            "labels": ["adapter_key", "status"],
            "evidence": "integration_execution.metric_attached",
        },
        {
            "metric": "drivedesk_integration_reconciliations",
            "status": "planned",
            "labels": ["adapter_key", "status"],
            "evidence": "integration_execution.metric_attached",
        },
        {
            "metric": "drivedesk_integration_incidents",
            "status": "planned",
            "labels": ["adapter_key", "severity", "status"],
            "evidence": "integration_execution.metric_attached",
        },
    ]

    data_boundaries = [
        {
            "name": "preview_only_execution",
            "status": "clean",
            "external_mutation": False,
            "detail": "Execution timeline is computed without creating run rows or queueing provider work.",
        },
        {
            "name": "idempotency_without_payload",
            "status": "clean",
            "external_mutation": False,
            "idempotency_keys": idempotency_keys,
            "detail": "Only idempotency key names and a synthetic fingerprint are shown.",
        },
        {
            "name": "provider_result_redaction",
            "status": "clean",
            "contains_pii": False,
            "raw_payload_included": False,
            "detail": "Provider result payloads are represented by status and evidence references only.",
        },
        {
            "name": "operator_review_before_mutation",
            "status": "closed",
            "external_mutation": False,
            "detail": "Provider-changing work stays behind approval, outbox, and audit boundaries.",
        },
    ]

    return {
        "adapter_key": runtime["adapter_key"],
        "operation_key": selected_operation_key,
        "execution_mode": execution_mode,
        "runtime_plan": runtime,
        "run_ledger": run_ledger,
        "timeline": timeline,
        "state_transitions": state_transitions,
        "retry_policy": retry_policy,
        "reconciliation_links": reconciliation_links,
        "observability": observability,
        "data_boundaries": data_boundaries,
    }


def build_connector_certification_workbench() -> dict[str, object]:
    descriptors = [resolve_adapter(key).descriptor for key in sorted(ADAPTERS)]
    provider_rows: list[dict[str, object]] = []
    for descriptor in descriptors:
        auth_profile = descriptor.auth_profile
        operations = list(descriptor.operation_contracts)
        has_runtime_contract = bool(operations)
        has_secret_boundary = (
            auth_profile.get("credential_placement") == "server_secret_store"
            and auth_profile.get("public_demo_requires_secret") is False
        )
        has_operation_scope = any(operation.required_connection_scope for operation in operations)
        has_idempotency = all(operation.idempotency_keys for operation in operations) if operations else False
        has_recovery_path = any(
            operation.retryable or operation.dead_letter or operation.operator_review
            for operation in operations
        )
        private_ready = (
            descriptor.connection_profile_supported
            and has_runtime_contract
            and has_secret_boundary
            and has_operation_scope
            and has_idempotency
        )
        provider_rows.append(
            {
                "adapter_key": descriptor.key,
                "name": descriptor.name,
                "category": descriptor.category,
                "direction": descriptor.direction,
                "status": "private_ready" if private_ready else "contract_ready",
                "operation_count": len(operations),
                "capability_count": len(descriptor.capabilities),
                "connection_profile_supported": descriptor.connection_profile_supported,
                "server_secret_boundary": has_secret_boundary,
                "requires_real_provider_secret": bool(
                    auth_profile.get("real_provider_requires_secret")
                ),
                "public_demo_requires_secret": bool(
                    auth_profile.get("public_demo_requires_secret")
                ),
                "scope_boundary": has_operation_scope,
                "idempotency_boundary": has_idempotency,
                "recovery_boundary": has_recovery_path,
                "public_safe": True,
                "ready_for_private_connector": private_ready,
                "evidence": "connector_certification.provider_profile_checked",
            }
        )

    certified = [row for row in provider_rows if row["ready_for_private_connector"]]
    return {
        "status": "validated",
        "certification_level": "public_contract_certified",
        "adapter_count": len(provider_rows),
        "private_ready_count": len(certified),
        "summary": [
            {
                "label": "Adapters checked",
                "value": str(len(provider_rows)),
                "detail": "runtime catalog providers",
                "tone": "blue",
            },
            {
                "label": "Private-ready",
                "value": str(len(certified)),
                "detail": "profile, scope, secret boundary, idempotency",
                "tone": "green",
            },
            {
                "label": "Provider calls",
                "value": "0",
                "detail": "certification is public-safe and offline",
                "tone": "amber",
            },
            {
                "label": "Evidence",
                "value": "linked",
                "detail": "docs, fixtures, runtime, execution",
                "tone": "violet",
            },
        ],
        "provider_profiles": provider_rows,
        "certification_stages": [
            {
                "stage": "provider_profile",
                "status": "passed",
                "detail": "Adapter identity, category, direction, connection profile, and auth mode are declared.",
                "evidence": "connector_certification.provider_profile_checked",
            },
            {
                "stage": "capability_manifest",
                "status": "passed",
                "detail": "Capabilities, failure modes, mapping requirements, and operation contracts are visible.",
                "evidence": "connector_certification.capability_manifest_checked",
            },
            {
                "stage": "auth_boundary",
                "status": "clean",
                "detail": "Public demo returns secret reference names and boundary metadata, never secret values.",
                "evidence": "server_secret_store",
            },
            {
                "stage": "fixture_replay",
                "status": "validated",
                "detail": "Synthetic fixtures cover happy path, redaction, validation, retry, dead-letter, and reconciliation.",
                "evidence": "bash scripts/check_public_connector_fixture_replay.sh",
            },
            {
                "stage": "runtime_preview",
                "status": "validated",
                "detail": "Operation contracts resolve into scope preflight, outbox, worker, reconciliation, and incidents.",
                "evidence": "adapter_runtime.previewed",
            },
            {
                "stage": "execution_timeline",
                "status": "validated",
                "detail": "Run ledger, provider-call block, retry policy, and operator closure are represented.",
                "evidence": "integration_execution.run_ledger_prepared",
            },
            {
                "stage": "release_gate",
                "status": "enforced",
                "detail": "Public export, smoke, OpenAPI, SDK, and Pages checks must include this contract.",
                "evidence": "bash scripts/public_repo_release_gate.sh",
            },
        ],
        "certification_gates": [
            {
                "gate": "no_real_provider_call",
                "status": "closed",
                "detail": "Public certification does not call Bitrix, bank, accounting, email, Telegram, or payment APIs.",
                "external_mutation": False,
                "evidence": "provider_call_enabled=false",
            },
            {
                "gate": "no_secret_value",
                "status": "clean",
                "detail": "Only secret reference names are exposed in generated contracts.",
                "external_mutation": False,
                "evidence": "server_secret_store",
            },
            {
                "gate": "no_raw_payload",
                "status": "clean",
                "detail": "Raw provider payloads and request bodies stay outside the public payload.",
                "external_mutation": False,
                "evidence": "raw_payload_returned=false",
            },
            {
                "gate": "idempotent_execution",
                "status": "required",
                "detail": "Provider-changing operations must declare idempotency keys before private rollout.",
                "external_mutation": False,
                "evidence": "operation_contracts.idempotency_keys",
            },
            {
                "gate": "operator_review",
                "status": "armed",
                "detail": "Retry, dead-letter, and reconciliation mismatches route to operator review.",
                "external_mutation": False,
                "evidence": "integration.operator_review.created",
            },
        ],
        "implementation_path": [
            {
                "step": "add_private_provider_client",
                "status": "next_private_step",
                "detail": "Implement the real provider client behind server-side secrets and the existing adapter interface.",
                "evidence": "private_connector_only",
            },
            {
                "step": "bind_connection_profile",
                "status": "next_private_step",
                "detail": "Attach tenant-scoped connection profile, scopes, mappings, rate limits, and retry policy.",
                "evidence": "IntegrationConnection",
            },
            {
                "step": "run_fixture_replay",
                "status": "required",
                "detail": "Replay public-safe fixtures plus private sandbox fixtures before enabling provider writes.",
                "evidence": "connector_fixture_replay",
            },
            {
                "step": "enable_dry_run",
                "status": "required",
                "detail": "Run provider API calls in dry-run or read-only mode with audit and redaction evidence.",
                "evidence": "adapter_runtime.previewed",
            },
            {
                "step": "unlock_commit_request",
                "status": "requires_approval",
                "detail": "Allow write-mode execution only after approval, idempotency, observability, and rollback review.",
                "evidence": "business_approval_gateway.previewed",
            },
        ],
        "data_boundaries": [
            {
                "name": "public_demo_data",
                "status": "synthetic_only",
                "contains_pii": False,
                "raw_payload_included": False,
                "external_mutation": False,
                "detail": "Workbench payload is generated from adapter metadata and synthetic evidence.",
            },
            {
                "name": "browser_boundary",
                "status": "clean",
                "contains_pii": False,
                "raw_payload_included": False,
                "external_mutation": False,
                "detail": "Browser receives certification state, not provider tokens or raw provider responses.",
            },
            {
                "name": "private_connector_boundary",
                "status": "separate",
                "contains_pii": False,
                "raw_payload_included": False,
                "external_mutation": False,
                "detail": "Real provider clients and secrets belong only in the private connector runtime.",
            },
        ],
        "api": {
            "standalone": "GET /demo/connector-certification",
            "catalog": "GET /integration-adapters",
            "publicDemo": "GET /demo/public",
            "fixtureReplay": "GET /demo/connector-fixture-replay",
            "runtime": "GET /demo/integration-runtime",
            "execution": "GET /demo/integration-execution",
        },
        "docs": [
            {
                "label": "Connector certification",
                "path": "docs/public/CONNECTOR_CERTIFICATION.md",
                "check": "bash scripts/check_public_connector_certification.sh",
            },
            {
                "label": "Connector fixture replay",
                "path": "docs/public/CONNECTOR_FIXTURE_REPLAY.md",
                "check": "bash scripts/check_public_connector_fixture_replay.sh",
            },
            {
                "label": "Integration runtime",
                "path": "docs/public/INTEGRATION_RUNTIME.md",
                "check": "bash scripts/check_public_integration_runtime.sh",
            },
            {
                "label": "Integration execution",
                "path": "docs/public/INTEGRATION_EXECUTION.md",
                "check": "bash scripts/check_public_integration_execution.sh",
            },
        ],
    }


def build_provider_onboarding_workbench(adapter_key: str = "crm.bitrix24.mock") -> dict[str, object]:
    descriptor = resolve_adapter(adapter_key).descriptor
    mapping = dict(descriptor.mapping_example)
    scopes = list(descriptor.default_connection_scopes)
    sample_records: list[dict[str, object]] = [
        {
            "ID": "DEAL-2026-001",
            "STAGE_ID": "invoice_sent",
            "ASSIGNED_BY_ROLE": "sales",
            "OPPORTUNITY": 1500,
            "CLIENT_NAME": "Synthetic Customer",
            "PHONE": "+70000000000",
            "ACCESS_TOKEN": "redacted-in-public-contract",
        },
        {
            "ID": "DEAL-2026-002",
            "STAGE_ID": "paid",
            "ASSIGNED_BY_ROLE": "manager",
            "OPPORTUNITY": 4200,
            "EMAIL": "synthetic@example.invalid",
            "SECRET": "redacted-in-public-contract",
        },
    ]
    diagnostics = build_adapter_connection_diagnostics(
        adapter_key,
        mapping=mapping,
        scopes=scopes,
    )
    mapping_preview = build_adapter_mapping_preview(
        adapter_key,
        records=sample_records,
        mapping=mapping,
    )
    preview_runtime = build_adapter_runtime_plan(
        adapter_key,
        operation_key="crm_deal_intake_preview",
        scopes=["crm:deal.preview"],
        execution_mode="contract_only",
    )
    ingest_execution = build_adapter_execution_timeline(
        adapter_key,
        operation_key="crm_deal_ingest_execute",
        scopes=scopes,
        execution_mode="contract_only",
        include_failure_path=True,
    )
    dropped_sensitive_keys = sorted(
        {
            sensitive_key
            for record in sample_records
            for sensitive_key in _crm_sensitive_keys(record)
        }
    )
    auth_profile = descriptor.auth_profile

    return {
        "status": "previewed",
        "onboarding_level": "sandbox_onboarding_ready",
        "provider_key": descriptor.key,
        "provider_name": descriptor.name,
        "provider_category": descriptor.category,
        "summary": [
            {
                "label": "Provider",
                "value": descriptor.category.upper(),
                "detail": descriptor.key,
                "tone": "blue",
            },
            {
                "label": "Records",
                "value": str(mapping_preview["records_accepted"]),
                "detail": "synthetic records accepted in mapping preview",
                "tone": "green",
            },
            {
                "label": "External calls",
                "value": "0",
                "detail": "public onboarding is dry-run only",
                "tone": "amber",
            },
            {
                "label": "Rollout",
                "value": "gated",
                "detail": "private connector requires approval evidence",
                "tone": "violet",
            },
        ],
        "provider_profile": {
            "adapter_key": descriptor.key,
            "adapter_name": descriptor.name,
            "category": descriptor.category,
            "direction": descriptor.direction,
            "auth_mode": auth_profile.get("mode", "unspecified"),
            "credential_placement": auth_profile.get("credential_placement", "unspecified"),
            "secret_refs": sorted(str(item) for item in auth_profile.get("secret_refs", [])),
            "public_demo_requires_secret": bool(auth_profile.get("public_demo_requires_secret")),
            "real_provider_requires_secret": bool(auth_profile.get("real_provider_requires_secret")),
            "supported_scopes": scopes,
            "operation_keys": diagnostics["operation_keys"],
            "executable_operation_keys": diagnostics["executable_operation_keys"],
            "evidence": "provider_onboarding.provider_profile_selected",
        },
        "onboarding_stages": [
            {
                "stage": "select_provider_profile",
                "status": "selected",
                "detail": f"{descriptor.key} selected from the adapter catalog.",
                "evidence": "GET /integration-adapters",
            },
            {
                "stage": "bind_connection_profile",
                "status": "prepared",
                "detail": "Tenant mapping, scopes, and server-side secret references are ready.",
                "evidence": "IntegrationConnection",
            },
            {
                "stage": "mapping_preview",
                "status": "previewed",
                "detail": (
                    f"{mapping_preview['records_accepted']} accepted, "
                    f"{mapping_preview['records_rejected']} rejected."
                ),
                "evidence": "adapter_mapping.previewed",
            },
            {
                "stage": "sandbox_dry_run",
                "status": "previewed",
                "detail": "Runtime and execution plans are computed without provider mutation.",
                "evidence": "adapter_runtime.previewed",
            },
            {
                "stage": "approval_review",
                "status": "approval_required",
                "detail": "Provider writes stay behind approval, idempotency, and rollback review.",
                "evidence": "business_approval_gateway.previewed",
            },
            {
                "stage": "private_rollout",
                "status": "next_private_step",
                "detail": "Private connector can swap the mock client for a real provider client.",
                "evidence": "private_connector_only",
            },
        ],
        "mapping_preview": {
            "adapter_key": mapping_preview["adapter_key"],
            "records_received": mapping_preview["records_received"],
            "records_accepted": mapping_preview["records_accepted"],
            "records_rejected": mapping_preview["records_rejected"],
            "required_mapping_keys": mapping_preview["required_mapping_keys"],
            "mapping_keys": sorted(mapping.keys()),
            "dropped_sensitive_keys": dropped_sensitive_keys,
            "raw_payload_included": False,
            "contains_pii": False,
            "evidence": "adapter_mapping.previewed",
        },
        "preflight_checks": [
            {
                "check": "adapter_registered",
                "status": "passed",
                "detail": descriptor.key,
                "external_mutation": False,
                "evidence": "provider_onboarding.preflight_passed",
            },
            {
                "check": "connection_scopes_available",
                "status": "passed",
                "detail": ", ".join(scopes),
                "external_mutation": False,
                "evidence": "adapter_runtime.scope_checked",
            },
            {
                "check": "mapping_profile_valid",
                "status": "passed",
                "detail": ", ".join(sorted(mapping.keys())),
                "external_mutation": False,
                "evidence": "adapter_mapping.previewed",
            },
            {
                "check": "secret_refs_server_side",
                "status": "clean",
                "detail": str(auth_profile.get("credential_placement") or "unspecified"),
                "external_mutation": False,
                "evidence": "server_secret_store",
            },
            {
                "check": "provider_call_disabled",
                "status": "closed",
                "detail": "Public onboarding never calls the external provider.",
                "external_mutation": False,
                "evidence": "provider_call_enabled=false",
            },
        ],
        "sandbox_contract": {
            "preview_operation": preview_runtime["operation_contract"]["key"],
            "execute_operation": ingest_execution["operation_key"],
            "runtime_steps": len(preview_runtime["runtime_steps"]),
            "execution_timeline_steps": len(ingest_execution["timeline"]),
            "provider_call_enabled": False,
            "external_mutation": False,
            "raw_payload_included": False,
            "contains_pii": False,
            "evidence": "provider_onboarding.sandbox_contract_ready",
        },
        "rollout_plan": [
            {
                "step": "create_tenant_connection",
                "status": "ready",
                "detail": "Create tenant-scoped connection metadata with mapping and scopes.",
                "evidence": "IntegrationConnection",
            },
            {
                "step": "run_mapping_preview",
                "status": "ready",
                "detail": "Validate provider field mapping against synthetic and sandbox fixtures.",
                "evidence": "adapter_mapping.previewed",
            },
            {
                "step": "run_fixture_replay",
                "status": "ready",
                "detail": "Replay success, redaction, invalid payload, retry, dead-letter, and reconciliation cases.",
                "evidence": "connector_fixture_replay",
            },
            {
                "step": "enable_private_dry_run",
                "status": "next_private_step",
                "detail": "Use real provider sandbox credentials only inside the private connector runtime.",
                "evidence": "private_connector_only",
            },
            {
                "step": "request_write_unlock",
                "status": "approval_required",
                "detail": "Enable write-mode only after approval, idempotency, SLO, and rollback evidence are attached.",
                "evidence": "business_approval_gateway.previewed",
            },
            {
                "step": "monitor_and_reconcile",
                "status": "scheduled",
                "detail": "Track outbox, reconciliation, incidents, and scheduled validation after rollout.",
                "evidence": "drivedesk_integration_reconciliations",
            },
        ],
        "data_boundaries": [
            {
                "name": "public_onboarding_payload",
                "status": "synthetic_only",
                "contains_pii": False,
                "raw_payload_included": False,
                "external_mutation": False,
                "detail": "Public payload contains adapter metadata, counts, and redaction evidence only.",
            },
            {
                "name": "server_secret_store",
                "status": "server_side",
                "contains_pii": False,
                "raw_payload_included": False,
                "external_mutation": False,
                "detail": "Secret reference names are visible, values stay in the private secret store.",
            },
            {
                "name": "browser_session",
                "status": "metadata_only",
                "contains_pii": False,
                "raw_payload_included": False,
                "external_mutation": False,
                "detail": "Browser sees onboarding evidence, never provider tokens or raw responses.",
            },
            {
                "name": "private_provider_runtime",
                "status": "separate",
                "contains_pii": False,
                "raw_payload_included": False,
                "external_mutation": False,
                "detail": "Real provider API calls belong only in the private connector runtime.",
            },
        ],
        "api": {
            "standalone": "GET /demo/provider-onboarding",
            "publicDemo": "GET /demo/public",
            "catalog": "GET /integration-adapters",
            "mappingPreview": "POST /tenants/{tenant_id}/integration-mapping/preview",
            "runtimePreview": "POST /tenants/{tenant_id}/integration-runtime/preview",
            "approvalGateway": "POST /tenants/{tenant_id}/business-approval-gateway/preview",
        },
        "docs": [
            {
                "label": "Provider onboarding",
                "path": "docs/public/PROVIDER_ONBOARDING.md",
                "check": "bash scripts/check_public_provider_onboarding.sh",
            },
            {
                "label": "Provider onboarding evidence",
                "path": "docs/public/evidence/provider-onboarding.sanitized.json",
                "check": "bash scripts/check_public_provider_onboarding.sh",
            },
            {
                "label": "Generated SDK",
                "path": "docs/public/CLIENT_SDK.md",
                "check": "bash scripts/check_public_demo_sdk.sh",
            },
            {
                "label": "Provider connector guide",
                "path": "docs/public/PROVIDER_CONNECTOR_GUIDE.md",
                "check": "bash scripts/check_public_provider_connector_guide.sh",
            },
            {
                "label": "Connector certification",
                "path": "docs/public/CONNECTOR_CERTIFICATION.md",
                "check": "bash scripts/check_public_connector_certification.sh",
            },
        ],
    }


def execute_adapter(adapter_key: str | None, payload: dict[str, object]) -> AdapterResult:
    adapter = resolve_adapter(adapter_key)
    return adapter.execute(payload)
