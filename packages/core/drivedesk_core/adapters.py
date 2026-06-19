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
        "capabilities": list(descriptor.capabilities),
    }


def execute_adapter(adapter_key: str | None, payload: dict[str, object]) -> AdapterResult:
    adapter = resolve_adapter(adapter_key)
    return adapter.execute(payload)
