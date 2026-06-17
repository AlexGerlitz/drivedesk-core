from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["owner", "admin", "manager", "viewer"]


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


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class AccessTokenRead(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: UserRead


class AuthMeRead(BaseModel):
    user: UserRead
    memberships: list[MembershipRead]


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
