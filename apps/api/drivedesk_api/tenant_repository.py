from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


T = TypeVar("T")


def _tenant_id_column(model: type[T]) -> Any:
    tenant_id = getattr(model, "tenant_id", None)
    if tenant_id is None:
        raise ValueError(f"{model.__name__} is not a tenant-owned model")
    return tenant_id


def tenant_owned_select(
    model: type[T],
    tenant_id: str,
    *,
    order_by: Any | Sequence[Any] | None = None,
) -> Select[tuple[T]]:
    query = select(model).where(_tenant_id_column(model) == tenant_id)
    if order_by is None:
        return query
    if isinstance(order_by, Sequence) and not isinstance(order_by, (str, bytes)):
        return query.order_by(*order_by)
    return query.order_by(order_by)


async def list_tenant_owned(
    session: AsyncSession,
    model: type[T],
    tenant_id: str,
    *,
    order_by: Any | Sequence[Any] | None = None,
) -> list[T]:
    result = await session.execute(tenant_owned_select(model, tenant_id, order_by=order_by))
    return list(result.scalars().all())
