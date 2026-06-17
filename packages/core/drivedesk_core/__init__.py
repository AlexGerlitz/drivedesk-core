"""DriveDesk Core package.

The package contains domain primitives that should stay independent from HTTP,
Telegram, worker runtime, and external integrations.
"""

from drivedesk_core.adapters import (
    AdapterExecutionError,
    AdapterResult,
    FakeFileImportAdapter,
    IntegrationAdapter,
    execute_adapter,
    resolve_adapter,
)
from drivedesk_core.domain import ActorRef, DomainEvent, TenantRef, build_event

__all__ = [
    "ActorRef",
    "AdapterExecutionError",
    "AdapterResult",
    "DomainEvent",
    "FakeFileImportAdapter",
    "IntegrationAdapter",
    "TenantRef",
    "build_event",
    "execute_adapter",
    "resolve_adapter",
]

__version__ = "0.1.0"
