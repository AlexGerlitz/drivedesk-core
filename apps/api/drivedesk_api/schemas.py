from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["owner", "admin", "manager", "viewer"]
PlatformRole = Literal["platform_admin"]
BusinessRecordType = Literal["contract", "payment", "lesson", "task", "document"]
WorkflowRuleTrigger = Literal["business_record.status_changed"]
WorkflowRuleActionType = Literal["emit_outbox_event", "create_task_record", "request_adapter_sync"]


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


class BusinessRecordCreate(BaseModel):
    record_type: BusinessRecordType
    title: str = Field(min_length=2, max_length=255)
    status: str = Field(default="draft", min_length=2, max_length=32, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    external_ref: str | None = Field(default=None, min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


class BusinessRecordTransition(BaseModel):
    status: str = Field(min_length=2, max_length=32, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    reason: str | None = Field(default=None, min_length=2, max_length=255)


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


class FileImportCreate(BaseModel):
    source_name: str = Field(min_length=2, max_length=120)
    source_format: Literal["json", "csv"] = "json"
    records: list[dict[str, Any]] = Field(min_length=1, max_length=50)
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
    adapters: list[dict[str, str]]
    integrationJobs: list[dict[str, Any]]
    integrationHealth: list[dict[str, str]]
    integrationReadiness: list[dict[str, Any]]
    workflow: dict[str, Any]
    timeline: list[dict[str, str]]
    domainEvents: list[dict[str, str]]
