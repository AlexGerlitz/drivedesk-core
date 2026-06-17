"""DriveDesk Core package.

The package contains domain primitives that should stay independent from HTTP,
Telegram, worker runtime, and external integrations.
"""

from drivedesk_core.domain import ActorRef, DomainEvent, TenantRef, build_event

__all__ = ["ActorRef", "DomainEvent", "TenantRef", "build_event"]

__version__ = "0.1.0"
