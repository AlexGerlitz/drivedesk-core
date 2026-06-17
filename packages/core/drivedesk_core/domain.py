from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class TenantRef:
    """Stable tenant identity used by core modules and adapters."""

    tenant_id: str
    slug: str


@dataclass(frozen=True)
class ActorRef:
    """User, system, or integration that initiated an operation."""

    actor_id: str
    actor_type: str
    display_name: str | None = None


@dataclass(frozen=True)
class DomainEvent:
    """Small immutable event envelope for future outbox and integration work."""

    event_id: str
    event_type: str
    tenant: TenantRef
    actor: ActorRef | None
    occurred_at: datetime
    payload: dict[str, object] = field(default_factory=dict)
    correlation_id: str | None = None


def build_event(
    *,
    event_type: str,
    tenant: TenantRef,
    actor: ActorRef | None = None,
    payload: dict[str, object] | None = None,
    correlation_id: str | None = None,
) -> DomainEvent:
    return DomainEvent(
        event_id=str(uuid4()),
        event_type=event_type,
        tenant=tenant,
        actor=actor,
        occurred_at=datetime.now(UTC),
        payload=payload or {},
        correlation_id=correlation_id,
    )
