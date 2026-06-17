from __future__ import annotations

from datetime import datetime
from typing import Literal

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
    payload_json: str
    status: str
    attempts: int
    last_error: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
