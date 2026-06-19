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
BusinessExceptionSeverity = Literal["info", "warning", "critical"]
BusinessExceptionStatus = Literal["open", "acknowledged", "resolved"]
RepairActionStatus = Literal["proposed", "approved", "executed"]
RepairActionSafetyLevel = Literal["low", "medium", "high"]
RepairActionExecutionMode = Literal["dry_run", "commit_request"]
BusinessBriefingRole = Literal["operator", "accountant", "manager", "owner", "support"]
BusinessBriefingRiskLevel = Literal["normal", "attention", "critical"]
BusinessDetectionRuleSet = Literal["payment_reconciliation"]
BusinessEscalationPolicy = Literal["exception_triage"]
BusinessActionPlanKind = Literal["exception_resolution"]
BusinessNotificationKind = Literal["action_plan_updates"]
BusinessNotificationChannel = Literal["in_app", "telegram", "email", "sms", "webhook"]
BusinessNotificationChannelMatrixKind = Literal["operator_channel_readiness"]
BusinessProviderIntakeSource = Literal["crm_deal", "bank_payment", "accounting_export", "support_ticket"]
BusinessWorkbenchContextKind = Literal["role_assist"]
BusinessTaskHandoffKind = Literal["action_plan_task_handoff"]
BusinessActionExecutionKind = Literal["action_plan_execution_preview"]


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
    auth_profile: dict[str, Any] = Field(default_factory=dict)
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


class BusinessStateObservationCreate(BaseModel):
    system_key: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    subject_type: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str = Field(min_length=1, max_length=128)
    external_ref: str | None = Field(default=None, min_length=1, max_length=128)
    state: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    observed_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class BusinessStateObservationRead(BaseModel):
    id: str
    tenant_id: str
    system_key: str
    subject_type: str
    subject_id: str
    external_ref: str | None = None
    state: str
    observed_at: datetime
    payload_json: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BusinessExceptionCreate(BaseModel):
    exception_type: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    severity: BusinessExceptionSeverity = "warning"
    subject_type: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=2, max_length=255)
    summary: str = Field(min_length=2, max_length=2000)
    impact: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    observation_ids: list[str] = Field(default_factory=list, max_length=20)


class BusinessExceptionStatusChange(BaseModel):
    status: Literal["acknowledged", "resolved"]
    note: str | None = Field(default=None, min_length=2, max_length=255)


class BusinessExceptionRead(BaseModel):
    id: str
    tenant_id: str
    exception_type: str
    severity: BusinessExceptionSeverity
    status: BusinessExceptionStatus
    subject_type: str
    subject_id: str
    title: str
    summary: str
    impact_json: str
    evidence_json: str
    detected_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RepairActionPropose(BaseModel):
    action_type: str = Field(default="sync_status", min_length=2, max_length=128, pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    safety_level: RepairActionSafetyLevel = "medium"
    requires_approval: bool = True
    summary: str | None = Field(default=None, min_length=2, max_length=2000)
    payload: dict[str, Any] = Field(default_factory=dict)


class RepairActionExecutionRequest(BaseModel):
    mode: RepairActionExecutionMode = "dry_run"
    note: str | None = Field(default=None, min_length=2, max_length=255)


class RepairActionRead(BaseModel):
    id: str
    tenant_id: str
    business_exception_id: str
    action_type: str
    safety_level: RepairActionSafetyLevel
    requires_approval: bool
    status: RepairActionStatus
    summary: str
    payload_json: str
    result_json: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    approved_at: datetime | None = None
    executed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BusinessBriefingPreviewCreate(BaseModel):
    role: BusinessBriefingRole = "operator"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    include_resolved: bool = False
    limit: int = Field(default=20, ge=1, le=50)


class BusinessBriefingRead(BaseModel):
    tenant_id: str
    role: BusinessBriefingRole
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    risk_level: BusinessBriefingRiskLevel
    summary: str
    source_systems: list[str] = Field(default_factory=list)
    highlights: list[dict[str, Any]] = Field(default_factory=list)
    recommended_actions: list[dict[str, Any]] = Field(default_factory=list)
    review_points: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessEscalationPreviewCreate(BaseModel):
    policy: BusinessEscalationPolicy = "exception_triage"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    include_resolved: bool = False
    limit: int = Field(default=20, ge=1, le=50)


class BusinessEscalationPreviewRead(BaseModel):
    tenant_id: str
    policy: BusinessEscalationPolicy
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    risk_level: BusinessBriefingRiskLevel
    summary: str
    queues: list[dict[str, Any]] = Field(default_factory=list)
    escalation_items: list[dict[str, Any]] = Field(default_factory=list)
    suggested_actions: list[dict[str, Any]] = Field(default_factory=list)
    review_points: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessActionPlanPreviewCreate(BaseModel):
    plan_kind: BusinessActionPlanKind = "exception_resolution"
    role: BusinessBriefingRole = "operator"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    include_resolved: bool = False
    limit: int = Field(default=20, ge=1, le=50)


class BusinessActionPlanPreviewRead(BaseModel):
    tenant_id: str
    plan_kind: BusinessActionPlanKind
    role: BusinessBriefingRole
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    risk_level: BusinessBriefingRiskLevel
    summary: str
    lanes: list[dict[str, Any]] = Field(default_factory=list)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    automation_candidates: list[dict[str, Any]] = Field(default_factory=list)
    approval_gates: list[dict[str, Any]] = Field(default_factory=list)
    review_points: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessNotificationPreviewCreate(BaseModel):
    notification_kind: BusinessNotificationKind = "action_plan_updates"
    role: BusinessBriefingRole = "operator"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    channels: list[Literal["in_app", "telegram", "email"]] = Field(
        default_factory=lambda: ["in_app"],
        min_length=1,
        max_length=3,
    )
    include_resolved: bool = False
    limit: int = Field(default=20, ge=1, le=50)


class BusinessNotificationPreviewRead(BaseModel):
    tenant_id: str
    notification_kind: BusinessNotificationKind
    role: BusinessBriefingRole
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    risk_level: BusinessBriefingRiskLevel
    summary: str
    channels: list[dict[str, Any]] = Field(default_factory=list)
    drafts: list[dict[str, Any]] = Field(default_factory=list)
    delivery_plan: list[dict[str, Any]] = Field(default_factory=list)
    approval_gates: list[dict[str, Any]] = Field(default_factory=list)
    review_points: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessNotificationChannelMatrixPreviewCreate(BaseModel):
    matrix_kind: BusinessNotificationChannelMatrixKind = "operator_channel_readiness"
    role: BusinessBriefingRole = "operator"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    channels: list[BusinessNotificationChannel] = Field(
        default_factory=lambda: ["in_app", "telegram", "email", "sms", "webhook"],
        min_length=1,
        max_length=5,
    )
    include_delivery_drafts: bool = True


class BusinessNotificationChannelMatrixPreviewRead(BaseModel):
    tenant_id: str
    matrix_kind: BusinessNotificationChannelMatrixKind
    role: BusinessBriefingRole
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    status: Literal["previewed"]
    summary: str
    channels: list[dict[str, Any]] = Field(default_factory=list)
    routing_rules: list[dict[str, Any]] = Field(default_factory=list)
    delivery_drafts: list[dict[str, Any]] = Field(default_factory=list)
    approval_gates: list[dict[str, Any]] = Field(default_factory=list)
    data_boundaries: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessProviderIntakePreviewCreate(BaseModel):
    provider_key: str = Field(min_length=3, max_length=120, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    source_type: BusinessProviderIntakeSource = "crm_deal"
    subject_type: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str = Field(min_length=1, max_length=128)
    external_ref: str | None = Field(default=None, min_length=1, max_length=128)
    provider_payload: dict[str, Any] = Field(default_factory=dict)


class BusinessProviderIntakePreviewRead(BaseModel):
    tenant_id: str
    provider_key: str
    source_type: BusinessProviderIntakeSource
    subject_type: str
    subject_id: str
    generated_at: datetime
    summary: str
    normalized_observation: dict[str, Any] = Field(default_factory=dict)
    safe_payload: dict[str, Any] = Field(default_factory=dict)
    payload_keys: list[str] = Field(default_factory=list)
    dropped_keys: list[str] = Field(default_factory=list)
    data_boundaries: list[dict[str, Any]] = Field(default_factory=list)
    next_steps: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessIntakePipelinePreviewCreate(BaseModel):
    role: BusinessBriefingRole = "operator"
    events: list[BusinessProviderIntakePreviewCreate] = Field(min_length=1, max_length=8)
    include_notification_drafts: bool = True


class BusinessIntakePipelinePreviewRead(BaseModel):
    tenant_id: str
    role: BusinessBriefingRole
    generated_at: datetime
    status: Literal["previewed"]
    summary: str
    source_systems: list[str] = Field(default_factory=list)
    intake_previews: list[dict[str, Any]] = Field(default_factory=list)
    workbench_context: dict[str, Any] = Field(default_factory=dict)
    detections: dict[str, Any] = Field(default_factory=dict)
    action_plan: dict[str, Any] = Field(default_factory=dict)
    notification_preview: dict[str, Any] = Field(default_factory=dict)
    data_boundaries: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessTaskHandoffPreviewCreate(BaseModel):
    handoff_kind: BusinessTaskHandoffKind = "action_plan_task_handoff"
    role: BusinessBriefingRole = "operator"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    action_plan_steps: list[dict[str, Any]] = Field(default_factory=list, max_length=10)
    include_internal_outbox: bool = True
    include_notification_drafts: bool = True


class BusinessTaskHandoffPreviewRead(BaseModel):
    tenant_id: str
    handoff_kind: BusinessTaskHandoffKind
    role: BusinessBriefingRole
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    status: Literal["previewed"]
    summary: str
    task_cards: list[dict[str, Any]] = Field(default_factory=list)
    outbox_candidates: list[dict[str, Any]] = Field(default_factory=list)
    notification_drafts: list[dict[str, Any]] = Field(default_factory=list)
    approval_gates: list[dict[str, Any]] = Field(default_factory=list)
    data_boundaries: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessActionExecutionPreviewCreate(BaseModel):
    execution_kind: BusinessActionExecutionKind = "action_plan_execution_preview"
    role: BusinessBriefingRole = "operator"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    action_steps: list[dict[str, Any]] = Field(default_factory=list, max_length=10)
    execution_mode: Literal["dry_run", "approval_request"] = "dry_run"
    include_preflight: bool = True
    include_rollback_plan: bool = True


class BusinessActionExecutionPreviewRead(BaseModel):
    tenant_id: str
    execution_kind: BusinessActionExecutionKind
    role: BusinessBriefingRole
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    status: Literal["previewed"]
    summary: str
    execution_plan: list[dict[str, Any]] = Field(default_factory=list)
    preflight_checks: list[dict[str, Any]] = Field(default_factory=list)
    dry_run_results: list[dict[str, Any]] = Field(default_factory=list)
    approval_gates: list[dict[str, Any]] = Field(default_factory=list)
    rollback_plan: list[dict[str, Any]] = Field(default_factory=list)
    data_boundaries: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessWorkbenchContextPreviewCreate(BaseModel):
    context_kind: BusinessWorkbenchContextKind = "role_assist"
    role: BusinessBriefingRole = "operator"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    source_systems: list[str] = Field(default_factory=list, max_length=8)
    include_resolved: bool = False
    limit: int = Field(default=20, ge=1, le=50)


class BusinessWorkbenchContextPreviewRead(BaseModel):
    tenant_id: str
    context_kind: BusinessWorkbenchContextKind
    role: BusinessBriefingRole
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    risk_level: BusinessBriefingRiskLevel
    summary: str
    source_systems: list[str] = Field(default_factory=list)
    context_cards: list[dict[str, Any]] = Field(default_factory=list)
    suggested_actions: list[dict[str, Any]] = Field(default_factory=list)
    data_boundaries: list[dict[str, Any]] = Field(default_factory=list)
    review_points: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


class BusinessDetectionPreviewCreate(BaseModel):
    rule_set: BusinessDetectionRuleSet = "payment_reconciliation"
    subject_type: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    limit: int = Field(default=50, ge=1, le=100)


class BusinessDetectionPreviewRead(BaseModel):
    tenant_id: str
    rule_set: BusinessDetectionRuleSet
    subject_type: str | None = None
    subject_id: str | None = None
    generated_at: datetime
    summary: str
    source_systems: list[str] = Field(default_factory=list)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    detected_exceptions: list[dict[str, Any]] = Field(default_factory=list)
    suggested_repair_actions: list[dict[str, Any]] = Field(default_factory=list)
    rules: list[dict[str, Any]] = Field(default_factory=list)
    api: dict[str, str] = Field(default_factory=dict)


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


class ConnectorFixtureReplayRead(BaseModel):
    status: Literal["validated"]
    command: str
    fixtureFile: str
    evidenceFile: str
    summary: list[dict[str, Any]]
    outcomes: list[dict[str, Any]]
    boundaries: list[dict[str, Any]]
    docs: list[dict[str, str]]


class BusinessScenarioReplayRead(BaseModel):
    status: Literal["validated"]
    command: str
    summary: list[dict[str, Any]]
    scenarios: list[dict[str, Any]]
    flow: list[dict[str, Any]]
    docs: list[dict[str, str]]


class BusinessIntakePipelineDemoRead(BaseModel):
    status: Literal["previewed"]
    command: str
    summary: list[dict[str, Any]]
    sourceSystems: list[str]
    intakePreviews: list[dict[str, Any]]
    workbench: dict[str, Any]
    detections: dict[str, Any]
    actionPlan: dict[str, Any]
    notifications: dict[str, Any]
    dataBoundaries: list[dict[str, Any]]
    api: dict[str, str]
    docs: list[dict[str, str]]


class BusinessTaskHandoffDemoRead(BaseModel):
    status: Literal["previewed"]
    command: str
    summary: list[dict[str, Any]]
    role: str
    subject: str
    taskCards: list[dict[str, Any]]
    outboxCandidates: list[dict[str, Any]]
    notificationDrafts: list[dict[str, Any]]
    approvalGates: list[dict[str, Any]]
    dataBoundaries: list[dict[str, Any]]
    api: dict[str, str]
    docs: list[dict[str, str]]


class BusinessNotificationChannelMatrixDemoRead(BaseModel):
    status: Literal["previewed"]
    command: str
    summary: list[dict[str, Any]]
    role: str
    subject: str
    channels: list[dict[str, Any]]
    routingRules: list[dict[str, Any]]
    deliveryDrafts: list[dict[str, Any]]
    approvalGates: list[dict[str, Any]]
    dataBoundaries: list[dict[str, Any]]
    api: dict[str, str]
    docs: list[dict[str, str]]


class BusinessContextAssistantDemoRead(BaseModel):
    status: Literal["previewed"]
    command: str
    summary: list[dict[str, Any]]
    role: str
    subject: str
    sourceSystems: list[str]
    contextCards: list[dict[str, Any]]
    insightRules: list[dict[str, Any]]
    suggestedActions: list[dict[str, Any]]
    dataBoundaries: list[dict[str, Any]]
    api: dict[str, str]
    docs: list[dict[str, str]]


class BusinessActionExecutionDemoRead(BaseModel):
    status: Literal["previewed"]
    command: str
    summary: list[dict[str, Any]]
    role: str
    subject: str
    executionPlan: list[dict[str, Any]]
    preflightChecks: list[dict[str, Any]]
    dryRunResults: list[dict[str, Any]]
    approvalGates: list[dict[str, Any]]
    rollbackPlan: list[dict[str, Any]]
    dataBoundaries: list[dict[str, Any]]
    api: dict[str, str]
    docs: list[dict[str, str]]


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
    adapterScenarios: list[dict[str, Any]]
    adapterStudio: dict[str, Any]
    connectorFixtureReplay: dict[str, Any]
    businessIntakePipeline: dict[str, Any]
    businessTaskHandoff: dict[str, Any]
    businessNotificationChannels: dict[str, Any]
    businessContextAssistant: dict[str, Any]
    businessActionExecution: dict[str, Any]
    integrationJobs: list[dict[str, Any]]
    integrationHealth: list[dict[str, str]]
    integrationReadiness: list[dict[str, Any]]
    recoveryEvidence: list[dict[str, str]]
    alertRouting: dict[str, Any]
    incidentResponse: dict[str, Any]
    businessControlTower: dict[str, Any]
    businessScenarioReplay: dict[str, Any]
    engineeringProof: dict[str, Any]
    workflow: dict[str, Any]
    workflowScenarios: list[dict[str, Any]]
    endToEndScenario: dict[str, Any]
    timeline: list[dict[str, str]]
    domainEvents: list[dict[str, str]]
