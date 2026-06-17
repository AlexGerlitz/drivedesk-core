"""DriveDesk Core package.

The package contains domain primitives that should stay independent from HTTP,
Telegram, worker runtime, and external integrations.
"""

from drivedesk_core.adapters import (
    AdapterDescriptor,
    AdapterExecutionError,
    AdapterResult,
    AdapterValidationError,
    FakeFileImportAdapter,
    IntegrationAdapter,
    describe_adapter,
    execute_adapter,
    list_adapter_descriptors,
    resolve_adapter,
    validate_adapter_connection_profile,
)
from drivedesk_core.domain import ActorRef, DomainEvent, TenantRef, build_event

__all__ = [
    "ActorRef",
    "AdapterDescriptor",
    "AdapterExecutionError",
    "AdapterResult",
    "AdapterValidationError",
    "DomainEvent",
    "FakeFileImportAdapter",
    "IntegrationAdapter",
    "TenantRef",
    "build_event",
    "describe_adapter",
    "execute_adapter",
    "list_adapter_descriptors",
    "resolve_adapter",
    "validate_adapter_connection_profile",
]

__version__ = "0.1.0"
