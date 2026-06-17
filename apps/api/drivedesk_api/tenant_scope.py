from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drivedesk_api.db import Membership, Tenant, User
from drivedesk_api.rbac import ActorContext


def actor_member_tenant_ids(actor: ActorContext) -> list[str]:
    if actor.source != "bearer":
        return []
    return list((actor.tenant_roles or {}).keys())


async def list_tenants_for_actor(session: AsyncSession, actor: ActorContext) -> list[Tenant]:
    if actor.source != "bearer" or actor.is_platform_admin():
        result = await session.execute(select(Tenant).order_by(Tenant.created_at.desc()))
        return list(result.scalars().all())

    tenant_ids = actor_member_tenant_ids(actor)
    if not tenant_ids:
        return []

    result = await session.execute(select(Tenant).where(Tenant.id.in_(tenant_ids)).order_by(Tenant.created_at.desc()))
    return list(result.scalars().all())


async def list_users_for_actor(session: AsyncSession, actor: ActorContext) -> list[User]:
    if actor.source != "bearer" or actor.is_platform_admin():
        result = await session.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    tenant_ids = actor_member_tenant_ids(actor)
    if not tenant_ids:
        return []

    result = await session.execute(
        select(User)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.tenant_id.in_(tenant_ids), Membership.status == "active")
        .distinct()
        .order_by(User.created_at.desc())
    )
    return list(result.scalars().all())
