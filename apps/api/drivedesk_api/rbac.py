from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fastapi import Header, HTTPException, status


class Permission(StrEnum):
    TENANT_READ = "tenant:read"
    TENANT_WRITE = "tenant:write"
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    MEMBERSHIP_READ = "membership:read"
    MEMBERSHIP_WRITE = "membership:write"
    AUDIT_READ = "audit:read"
    OUTBOX_READ = "outbox:read"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "owner": set(Permission),
    "admin": {
        Permission.TENANT_READ,
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.MEMBERSHIP_READ,
        Permission.MEMBERSHIP_WRITE,
        Permission.AUDIT_READ,
        Permission.OUTBOX_READ,
    },
    "manager": {
        Permission.TENANT_READ,
        Permission.USER_READ,
        Permission.MEMBERSHIP_READ,
        Permission.AUDIT_READ,
    },
    "viewer": {
        Permission.TENANT_READ,
        Permission.USER_READ,
        Permission.MEMBERSHIP_READ,
        Permission.AUDIT_READ,
    },
}


@dataclass(frozen=True)
class ActorContext:
    actor_id: str
    role: str

    def can(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())


async def actor_context(
    x_actor_id: str = Header(default="system", alias="X-Actor-Id"),
    x_actor_role: str = Header(default="viewer", alias="X-Actor-Role"),
) -> ActorContext:
    role = x_actor_role.strip().lower()
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"unknown actor role: {role}",
        )
    return ActorContext(actor_id=x_actor_id.strip() or "system", role=role)


def require_permission(actor: ActorContext, permission: Permission) -> None:
    if not actor.can(permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"permission required: {permission.value}",
        )
