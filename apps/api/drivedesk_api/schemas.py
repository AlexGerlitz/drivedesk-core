from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["owner", "admin", "manager", "viewer"]
PlatformRole = Literal["platform_admin"]
BusinessRecordType = Literal["contract", "payment", "lesson", "task", "document"]
WorkflowRuleTrigger = Literal["business_record.status_changed"]
WorkflowRuleActionType = Literal["emit_outbox_event", "create_task_record", "request_adapter_sync"]
IntegrationConnectionStatus = Literal["active", "disabled"]


class AdapterContractRead(BaseModel):
    key: str
    name: str
    status: str
    category: str
    direction: str
    purpose: str
    connection_profile_supported: bool
    connection_profile_required: bool
    payload_schema: dict[str, Any] = Field(default_factory=dict)
    config_example: dict[str, Any] = Field(default_factory=dict)
    mapping_example: dict[str, Any] = Field(default_factory=dict)
    required_mapping_keys: list[str] = Field(default_factory=list)
    supported_connection_scopes: list[str] = Field(default_factory=list)
    default_connection_scopes: list[str] = Field(default_factory=list)
    operation_contracts: list[dict[str, Any]] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    public_notes: list[str] = Field(default_factory=list)


class TenantCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
    name: str = Field(min_length=2, max_length=255)


class TenantRead(BaseModel):
    id: str
    slug: str
    name: str
    status: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    display_name: str = Field(min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(BaseModel):
    id: str
    email: str
    display_name: str
    status: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MembershipCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)
    role: Role


class MembershipRead(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    role: Role
    status: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PlatformAdminCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)
    role: PlatformRole = "platform_admin"


class PlatformAdminRead(BaseModel):
    id: str
    user_id: str
    role: PlatformRole
    status: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class AccessTokenRead(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: UserRead


class TokenRevocationRead(BaseModel):
    revoked: bool
    token_id: str
    status: Literal["revoked"]


class AuthMeRead(BaseModel):
    user: UserRead
    memberships: list[MembershipRead]
    platform_roles: list[PlatformRole] = Field(default_factory=list)


class AuthSessionRead(BaseModel):
    token_id: str
    user_id: str
    user_email: str
    user_display_name: str
    status: str
    created_at: datetime | None = None
    expires_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    tenant_ids: list[str]


class AuditEventRead(BaseModel):
    id: str
    tenant_id: str
    actor_id: str | None = None
    event_type: str
    entity_type: str | None = None
    entity_id: str | None = None
    summary: str | None = None
    metadata_json: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OutboxEventRead(BaseModel):
    id: str
    tenant_id: str
    event_type: str
    adapter_key: str | None = None
    payload_json: str
    result_json: str | None = None
    status: str
    attempts: int
    last_error: str | None = None
    last_duration_ms: float | None = None
    next_retry_at: datetime | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None
    dead_lettered_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OutboxEventRetryRequest(BaseModel):
    reason: str | None = Field(default=None, min_length=2, max_length=255)
    reset_attempts: bool = False


class IntegrationOperatorReviewItemRead(BaseModel):
    id: str
    tenant_id: str
    adapter_key: str
    operation_key: str | None = None
    event_type: str
    status: Literal["retry", "dead_letter"]
    severity: Literal["retryable", "operator_review"]
    attempts: int
    last_error: str | None = None
    last_duration_ms: float | None = None
    next_retry_at: datetime | None = None
    dead_lettered_at: datetime | None = None
    created_at: datetime | None = None
    integration_connection_id: str | None = None
    required_connection_scope: str | None = None
    payload_summary: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str
    retry_endpoint: str


class IntegrationConnectionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    adapter_key: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    status: IntegrationConnectionStatus = "active"
    config: dict[str, Any] = Field(default_factory=dict)
    mapping: dict[str, Any] = Field(default_factory=dict)
    scopes: list[str] = Field(default_factory=list, max_length=8)


class IntegrationConnectionRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    adapter_key: str
    status: IntegrationConnectionStatus
    config_json: str
    mapping_json: str
    scopes_json: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class IntegrationConnectionCheckCreate(BaseModel):
    check_type: Literal["synthetic_preflight"] = "synthetic_preflight"
    simulate_failure: Literal["provider_unavailable", "credential_rejected"] | None = None


class IntegrationConnectionCheckRead(BaseModel):
    id: str
    tenant_id: str
    integration_connection_id: str
    adapter_key: str
    check_type: str
    status: Literal["passed", "failed"]
    summary: str
    details_json: str
    duration_ms: float | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class IntegrationConnectionHealthRead(BaseModel):
    tenant_id: str
    integration_connection_id: str
    adapter_key: str
    connection_status: IntegrationConnectionStatus
    latest_status: Literal["never_checked", "passed", "failed"]
    latest_checked_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    check_count: int
    latest_summary: str | None = None
    latest_details: dict[str, Any] = Field(default_factory=dict)


class IntegrationReconciliationCreate(BaseModel):
    outbox_event_id: str = Field(min_length=1, max_length=36)
    provider_status: Literal["success", "partial_success", "failed", "pending"]
    provider_reference: str | None = Field(default=None, min_length=1, max_length=128)
    records_received: int | None = Field(default=None, ge=0)
    records_accepted: int | None = Field(default=None, ge=0)
    records_rejected: int | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, min_length=2, max_length=255)


class IntegrationReconciliationRead(BaseModel):
    id: str
    tenant_id: str
    outbox_event_id: str
    adapter_key: str
    operation_key: str | None = None
    status: Literal["matched", "mismatched", "pending", "blocked"]
    summary: str
    expected_json: str
    actual_json: str
    diff_json: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class IntegrationRunbookRead(BaseModel):
    key: str
    title: str
    severity: Literal["info", "warning", "critical"]
    source_type: Literal["outbox_event", "reconciliation"]
    source_statuses: list[str]
    alert_name: str | None = None
    summary: str
    recommended_actions: list[str]
    evidence_fields: list[str]


class IntegrationIncidentCreate(BaseModel):
    source_type: Literal["outbox_event", "reconciliation"]
    source_id: str = Field(min_length=1, max_length=36)
    note: str | None = Field(default=None, min_length=2, max_length=255)


class IntegrationIncidentStatusChange(BaseModel):
    status: Literal["acknowledged", "resolved"]
    note: str | None = Field(default=None, min_length=2, max_length=255)


class IntegrationIncidentRead(BaseModel):
    id: str
    tenant_id: str
    source_type: str
    source_id: str
    adapter_key: str
    operation_key: str | None = None
    runbook_key: str
    severity: Literal["info", "warning", "critical"]
    status: Literal["open", "acknowledged", "resolved"]
    summary: str
    recommended_action: str
    evidence_json: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class IntegrationMappingPreviewCreate(BaseModel):
    adapter_key: str = Field(default="file.import.fake", min_length=2, max_length=128, pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    integration_connection_id: str | None = Field(default=None, min_length=1, max_length=36)
    mapping: dict[str, Any] = Field(default_factory=dict)
    records: list[dict[str, Any]] = Field(min_length=1, max_length=20)


class IntegrationMappingPreviewRecordRead(BaseModel):
    index: int
    status: Literal["accepted", "rejected"]
    normalized: dict[str, Any]
    errors: list[str] = Field(default_factory=list)


class IntegrationMappingPreviewRead(BaseModel):
    adapter_key: str
    required_mapping_keys: list[str]
    records_received: int
    records_accepted: int
    records_rejected: int
    records: list[IntegrationMappingPreviewRecordRead]


class BusinessRecordCreate(BaseModel):
    record_type: BusinessRecordType
    title: str = Field(min_length=2, max_length=255)
    status: str = Field(default="draft", min_length=2, max_length=32, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    external_ref: str | None = Field(default=None, min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


class BusinessRecordTransition(BaseModel):
    status: str = Field(min_length=2, max_length=32, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    reason: str | None = Field(default=None, min_length=2, max_length=255)


class BusinessRecordLifecyclePolicyRead(BaseModel):
    record_type: BusinessRecordType
    initial_status: str
    statuses: list[str]
    terminal_statuses: list[str]
    transitions: list[dict[str, Any]]


class BusinessRecordLifecyclePreviewCreate(BaseModel):
    record_type: BusinessRecordType
    from_status: str = Field(min_length=2, max_length=32, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    to_status: str = Field(min_length=2, max_length=32, pattern=r"^[a-z0-9][a-z0-9_-]*$")


class BusinessRecordLifecyclePreviewRead(BaseModel):
    record_type: BusinessRecordType
    from_status: str
    to_status: str
    valid: bool
    reason: str
    allowed_next_statuses: list[str]
    terminal: bool


class BusinessRecordRead(BaseModel):
    id: str
    tenant_id: str
    record_type: BusinessRecordType
    status: str
    title: str
    external_ref: str | None = None
    payload_json: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowRuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    trigger_event_type: WorkflowRuleTrigger = "business_record.status_changed"
    record_type: BusinessRecordType | None = None
    from_status: str | None = Field(default=None, min_length=2, max_length=32, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    to_status: str | None = Field(default=None, min_length=2, max_length=32, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    action_type: WorkflowRuleActionType = "emit_outbox_event"
    action_config: dict[str, Any] = Field(default_factory=dict)


class WorkflowRuleRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    status: str
    trigger_event_type: WorkflowRuleTrigger
    record_type: BusinessRecordType | None = None
    from_status: str | None = None
    to_status: str | None = None
    action_type: WorkflowRuleActionType
    action_config_json: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowActionRunRead(BaseModel):
    id: str
    tenant_id: str
    workflow_rule_id: str
    trigger_event_type: str
    action_type: str
    status: str
    source_record_id: str
    source_record_type: str
    previous_status: str | None = None
    new_status: str | None = None
    outbox_event_id: str | None = None
    task_record_id: str | None = None
    result_json: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class FileImportCreate(BaseModel):
    integration_connection_id: str | None = Field(default=None, min_length=1, max_length=36)
    source_name: str = Field(min_length=2, max_length=120)
    source_format: Literal["json", "csv"] = "json"
    records: list[dict[str, Any]] = Field(min_length=1, max_length=50)
    simulate_failure: Literal["retryable", "permanent"] | None = None


class AccountingExportCreate(BaseModel):
    integration_connection_id: str | None = Field(default=None, min_length=1, max_length=36)
    export_batch_id: str = Field(min_length=2, max_length=120)
    documents: list[dict[str, Any]] = Field(min_length=1, max_length=50)
    simulate_failure: Literal["retryable", "permanent"] | None = None


class PublicDemoRead(BaseModel):
    schemaVersion: int
    generatedAt: str
    dataSource: Literal["api.synthetic"]
    apiContract: dict[str, str]
    tenant: dict[str, str]
    health: dict[str, str]
    metrics: list[dict[str, Any]]
    workQueue: list[dict[str, Any]]
    members: list[dict[str, str]]
    auditEvents: list[dict[str, str]]
    outbox: list[dict[str, Any]]
    adapters: list[dict[str, Any]]
    integrationJobs: list[dict[str, Any]]
    integrationHealth: list[dict[str, str]]
    integrationReadiness: list[dict[str, Any]]
    recoveryEvidence: list[dict[str, str]]
    engineeringProof: dict[str, Any]
    workflow: dict[str, Any]
    timeline: list[dict[str, str]]
    domainEvents: list[dict[str, str]]
