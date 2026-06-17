"""DriveDesk Core package.

The package contains domain primitives that should stay independent from HTTP,
Telegram, worker runtime, and external integrations.
"""

from drivedesk_core.adapters import (
    AdapterDescriptor,
    AdapterExecutionError,
    AdapterOperationContract,
    AdapterResult,
    AdapterValidationError,
    FakeFileImportAdapter,
    IntegrationAdapter,
    build_adapter_mapping_preview,
    describe_adapter,
    execute_adapter,
    list_adapter_descriptors,
    normalize_adapter_records,
    resolve_adapter,
    resolve_adapter_connection_scopes,
    validate_adapter_connection_scope,
    validate_adapter_connection_profile,
)
from drivedesk_core.domain import ActorRef, DomainEvent, TenantRef, build_event

__all__ = [
    "ActorRef",
    "AdapterDescriptor",
    "AdapterExecutionError",
    "AdapterOperationContract",
    "AdapterResult",
    "AdapterValidationError",
    "DomainEvent",
    "FakeFileImportAdapter",
    "IntegrationAdapter",
    "TenantRef",
    "build_adapter_mapping_preview",
    "build_event",
    "describe_adapter",
    "execute_adapter",
    "list_adapter_descriptors",
    "normalize_adapter_records",
    "resolve_adapter",
    "resolve_adapter_connection_scopes",
    "validate_adapter_connection_scope",
    "validate_adapter_connection_profile",
]

__version__ = "0.1.0"
