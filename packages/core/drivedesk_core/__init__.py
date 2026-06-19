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
    MockAccountingExportAdapter,
    MockCrmDealAdapter,
    build_adapter_execution_timeline,
    build_adapter_mapping_preview,
    build_adapter_connection_diagnostics,
    build_adapter_runtime_plan,
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
from drivedesk_core.lifecycle import (
    LifecyclePolicy,
    LifecycleTransition,
    describe_lifecycle_policy,
    list_lifecycle_policies,
    preview_lifecycle_transition,
)
from drivedesk_core.runbooks import IntegrationRunbook, list_integration_runbooks, select_integration_runbook

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
    "IntegrationRunbook",
    "LifecyclePolicy",
    "LifecycleTransition",
    "MockAccountingExportAdapter",
    "MockCrmDealAdapter",
    "TenantRef",
    "build_adapter_execution_timeline",
    "build_adapter_mapping_preview",
    "build_adapter_connection_diagnostics",
    "build_adapter_runtime_plan",
    "build_event",
    "describe_adapter",
    "execute_adapter",
    "list_adapter_descriptors",
    "list_integration_runbooks",
    "list_lifecycle_policies",
    "normalize_adapter_records",
    "preview_lifecycle_transition",
    "resolve_adapter",
    "resolve_adapter_connection_scopes",
    "select_integration_runbook",
    "describe_lifecycle_policy",
    "validate_adapter_connection_scope",
    "validate_adapter_connection_profile",
]

__version__ = "0.1.0"
