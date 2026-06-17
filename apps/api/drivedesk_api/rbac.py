from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from drivedesk_api.auth import parse_bearer_token, resolve_access_token
from drivedesk_api.session import get_session


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
    "authenticated": set(),
}

ROLE_PRIORITY = {
    "authenticated": 0,
    "viewer": 1,
    "manager": 2,
    "admin": 3,
    "owner": 4,
}


@dataclass(frozen=True)
class ActorContext:
    actor_id: str
    role: str
    source: str = "header"
    email: str | None = None
    token_id: str | None = None
    tenant_roles: dict[str, str] | None = None

    def can(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())

    def role_for_tenant(self, tenant_id: str) -> str | None:
        if not self.tenant_roles:
            return None
        return self.tenant_roles.get(tenant_id)


def _highest_role(roles: list[str]) -> str:
    if not roles:
        return "authenticated"
    return max(roles, key=lambda role: ROLE_PRIORITY.get(role, -1))


async def actor_context(
    session: AsyncSession = Depends(get_session),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_actor_id: str = Header(default="system", alias="X-Actor-Id"),
    x_actor_role: str = Header(default="viewer", alias="X-Actor-Role"),
) -> ActorContext:
    bearer_token = parse_bearer_token(authorization)
    if bearer_token:
        authenticated = await resolve_access_token(session, token_value=bearer_token)
        if not authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or expired access token",
            )
        tenant_roles = {membership.tenant_id: membership.role for membership in authenticated.memberships}
        return ActorContext(
            actor_id=authenticated.user.id,
            role=_highest_role(list(tenant_roles.values())),
            source="bearer",
            email=authenticated.user.email,
            token_id=authenticated.access_token.id,
            tenant_roles=tenant_roles,
        )

    if authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid authorization header",
        )

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


def require_tenant_permission(actor: ActorContext, tenant_id: str, permission: Permission) -> None:
    if actor.source != "bearer":
        require_permission(actor, permission)
        return

    tenant_role = actor.role_for_tenant(tenant_id)
    if tenant_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant membership required",
        )

    if permission not in ROLE_PERMISSIONS.get(tenant_role, set()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"permission required: {permission.value}",
        )
