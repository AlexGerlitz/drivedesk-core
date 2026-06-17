from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from drivedesk_api.db import AccessToken, AuthAttempt, Membership, User
from drivedesk_api.schemas import AuthSessionRead


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


async def _tenant_ids_by_user(
    session: AsyncSession,
    user_ids: Iterable[str],
    *,
    allowed_tenant_ids: Iterable[str] | None = None,
) -> dict[str, list[str]]:
    user_id_list = _dedupe(user_ids)
    if not user_id_list:
        return {}

    query = select(Membership.user_id, Membership.tenant_id).where(
        Membership.user_id.in_(user_id_list),
        Membership.status == "active",
    )
    allowed_tenant_id_list = _dedupe(allowed_tenant_ids or [])
    if allowed_tenant_ids is not None:
        if not allowed_tenant_id_list:
            return {}
        query = query.where(Membership.tenant_id.in_(allowed_tenant_id_list))

    result = await session.execute(query.order_by(Membership.created_at.desc()))
    tenant_ids_by_user: dict[str, list[str]] = {}
    for user_id, tenant_id in result.all():
        tenant_ids_by_user.setdefault(user_id, []).append(tenant_id)
    return {user_id: _dedupe(tenant_ids) for user_id, tenant_ids in tenant_ids_by_user.items()}


async def list_auth_sessions(
    session: AsyncSession,
    *,
    allowed_tenant_ids: Iterable[str] | None = None,
) -> list[AuthSessionRead]:
    allowed_tenant_id_list = _dedupe(allowed_tenant_ids or [])
    if allowed_tenant_ids is not None and not allowed_tenant_id_list:
        return []

    query = (
        select(AccessToken, User)
        .join(User, User.id == AccessToken.user_id)
        .order_by(AccessToken.created_at.desc())
    )
    if allowed_tenant_ids is not None:
        query = query.join(Membership, Membership.user_id == User.id).where(
            Membership.tenant_id.in_(allowed_tenant_id_list),
            Membership.status == "active",
        )

    result = await session.execute(query)
    rows = []
    seen_tokens: set[str] = set()
    user_ids: list[str] = []
    for token, user in result.all():
        if token.id in seen_tokens:
            continue
        seen_tokens.add(token.id)
        rows.append((token, user))
        user_ids.append(user.id)

    tenant_ids_by_user = await _tenant_ids_by_user(
        session,
        user_ids,
        allowed_tenant_ids=allowed_tenant_id_list if allowed_tenant_ids is not None else None,
    )

    return [
        AuthSessionRead(
            token_id=token.id,
            user_id=user.id,
            user_email=user.email,
            user_display_name=user.display_name,
            status=token.status,
            created_at=token.created_at,
            expires_at=token.expires_at,
            last_used_at=token.last_used_at,
            revoked_at=token.revoked_at,
            tenant_ids=tenant_ids_by_user.get(user.id, []),
        )
        for token, user in rows
    ]


async def get_auth_session(
    session: AsyncSession,
    *,
    token_id: str,
    allowed_tenant_ids: Iterable[str] | None = None,
) -> AuthSessionRead | None:
    query = select(AccessToken, User).join(User, User.id == AccessToken.user_id).where(AccessToken.id == token_id)
    result = await session.execute(query)
    row = result.one_or_none()
    if row is None:
        return None

    token, user = row
    tenant_ids_by_user = await _tenant_ids_by_user(
        session,
        [user.id],
        allowed_tenant_ids=allowed_tenant_ids,
    )
    tenant_ids = tenant_ids_by_user.get(user.id, [])
    if allowed_tenant_ids is not None and not tenant_ids:
        return None

    return AuthSessionRead(
        token_id=token.id,
        user_id=user.id,
        user_email=user.email,
        user_display_name=user.display_name,
        status=token.status,
        created_at=token.created_at,
        expires_at=token.expires_at,
        last_used_at=token.last_used_at,
        revoked_at=token.revoked_at,
        tenant_ids=tenant_ids,
    )


async def count_auth_sessions_by_status(session: AsyncSession) -> dict[str, int]:
    result = await session.execute(
        select(AccessToken.status, func.count()).group_by(AccessToken.status)
    )
    return {status: int(count or 0) for status, count in result.all()}


async def count_auth_attempts_by_outcome(session: AsyncSession) -> dict[str, int]:
    result = await session.execute(
        select(AuthAttempt.outcome, func.count()).group_by(AuthAttempt.outcome)
    )
    return {outcome: int(count or 0) for outcome, count in result.all()}
