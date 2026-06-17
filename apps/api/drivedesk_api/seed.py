from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from drivedesk_api.db import Membership, Tenant, User
from drivedesk_api.rbac import ActorContext
from drivedesk_api.schemas import MembershipCreate, TenantCreate, UserCreate
from drivedesk_api.services import create_membership, create_tenant, create_user
from drivedesk_api.session import SessionLocal


async def seed_fake_data(session_factory: async_sessionmaker[AsyncSession] = SessionLocal) -> dict[str, object]:
    actor = ActorContext(actor_id="seed", role="owner")

    async with session_factory() as session:
        existing = await session.execute(select(Tenant).where(Tenant.slug == "demo-business"))
        tenant = existing.scalar_one_or_none()

        if tenant is None:
            tenant = await create_tenant(
                session,
                TenantCreate(slug="demo-business", name="Demo Business"),
                actor,
            )
            tenant_created = True
        else:
            tenant_created = False

        user_result = await session.execute(select(User).where(User.email == "owner@example.test"))
        user = user_result.scalar_one_or_none()

        if user is None:
            user = await create_user(
                session,
                UserCreate(email="owner@example.test", display_name="Demo Owner"),
                actor,
            )
            user_created = True
        else:
            user_created = False

        membership_result = await session.execute(
            select(Membership).where(Membership.tenant_id == tenant.id, Membership.user_id == user.id)
        )
        membership = membership_result.scalar_one_or_none()

        if membership is None:
            membership = await create_membership(
                session,
                tenant_id=tenant.id,
                payload=MembershipCreate(user_id=user.id, role="owner"),
                actor=actor,
            )
            membership_created = True
            membership_id = membership.id
        else:
            membership_created = False
            membership_id = "already-present"

    return {
        "tenant_id": tenant.id,
        "tenant_created": tenant_created,
        "user_id": user.id,
        "user_created": user_created,
        "membership_id": membership_id,
        "membership_created": membership_created,
    }


async def main() -> None:
    result = await seed_fake_data()
    print(result, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
