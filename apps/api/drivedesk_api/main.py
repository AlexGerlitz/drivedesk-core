from __future__ import annotations

import logging
from datetime import timedelta
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response

from drivedesk_api.db import (
    AuditEvent,
    BusinessException,
    BusinessRecord,
    BusinessStateObservation,
    IntegrationConnection,
    IntegrationConnectionCheck,
    IntegrationIncident,
    IntegrationReconciliation,
    Membership,
    OutboxEvent,
    PlatformAdmin,
    RepairAction,
    Tenant,
    User,
    WorkflowActionRun,
    WorkflowRule,
)
from drivedesk_api.demo import build_public_demo_payload
from drivedesk_api.observability import (
    build_health_payload,
    build_metrics_text,
    build_ready_payload,
    log_json,
    record_http_request,
    route_template_for_scope,
)
from drivedesk_api.auth import (
    authenticate_user,
    is_login_guard_active,
    issue_access_token,
    list_active_memberships,
    list_active_platform_admins,
    record_auth_attempt,
    revoke_access_token,
    revoke_access_token_by_id,
    write_auth_audit,
)
from drivedesk_api.auth_sessions import (
    count_auth_attempts_by_outcome,
    count_auth_sessions_by_status,
    get_auth_session,
    list_auth_sessions,
)
from drivedesk_api.rbac import (
    ActorContext,
    Permission,
    actor_context,
    require_permission,
    require_platform_bootstrap_permission,
    require_tenant_permission,
    tenant_ids_with_permission,
)
from drivedesk_api.schemas import (
    AccessTokenRead,
    AccountingExportCreate,
    AdapterContractRead,
    AuditEventRead,
    AuthMeRead,
    AuthSessionRead,
    BusinessBriefingPreviewCreate,
    BusinessBriefingRead,
    BusinessDetectionPreviewCreate,
    BusinessDetectionPreviewRead,
    BusinessExceptionCreate,
    BusinessExceptionRead,
    BusinessExceptionStatusChange,
    BusinessRecordCreate,
    BusinessRecordLifecyclePolicyRead,
    BusinessRecordLifecyclePreviewCreate,
    BusinessRecordLifecyclePreviewRead,
    BusinessRecordRead,
    BusinessRecordTransition,
    BusinessRecordType,
    BusinessStateObservationCreate,
    BusinessStateObservationRead,
    FileImportCreate,
    IntegrationConnectionCheckCreate,
    IntegrationConnectionCheckRead,
    IntegrationConnectionCreate,
    IntegrationConnectionHealthRead,
    IntegrationConnectionRead,
    IntegrationIncidentCreate,
    IntegrationIncidentRead,
    IntegrationIncidentStatusChange,
    IntegrationMappingPreviewCreate,
    IntegrationMappingPreviewRead,
    IntegrationOperatorReviewItemRead,
    IntegrationReconciliationCreate,
    IntegrationReconciliationRead,
    IntegrationRunbookRead,
    LoginRequest,
    MembershipCreate,
    MembershipRead,
    OutboxEventRead,
    OutboxEventRetryRequest,
    PlatformAdminCreate,
    PlatformAdminRead,
    PublicDemoRead,
    RepairActionExecutionRequest,
    RepairActionPropose,
    RepairActionRead,
    TenantCreate,
    TenantRead,
    TokenRevocationRead,
    UserCreate,
    UserRead,
    WorkflowActionRunRead,
    WorkflowRuleCreate,
    WorkflowRuleRead,
)
from drivedesk_api.services import (
    approve_repair_action,
    build_business_briefing,
    change_business_exception_status,
    count_business_records_by_type_status,
    count_business_exceptions_by_type_severity_status,
    count_business_state_observations_by_system_state,
    count_integration_connection_checks_by_adapter_status,
    count_integration_connections_by_adapter_status,
    count_integration_incidents_by_adapter_severity_status,
    count_integration_reconciliations_by_adapter_status,
    count_outbox_by_status,
    count_repair_actions_by_action_status,
    count_workflow_action_runs_by_action_status,
    count_workflow_rules_by_status_trigger_action,
    change_integration_incident_status,
    create_accounting_export_job,
    create_business_exception,
    create_business_record,
    create_business_state_observation,
    create_file_import_job,
    create_integration_incident,
    create_integration_connection,
    create_integration_reconciliation,
    create_membership,
    create_platform_admin,
    create_tenant,
    create_user,
    create_workflow_rule,
    ensure_tenant_exists,
    execute_repair_action,
    get_integration_connection_health,
    list_business_exceptions,
    list_business_records,
    list_business_state_observations,
    list_integration_connection_checks,
    list_integration_connections,
    list_integration_incidents,
    list_integration_operator_review,
    list_integration_reconciliations,
    list_platform_admins,
    list_repair_actions,
    list_workflow_action_runs,
    list_workflow_rules,
    preview_business_detections,
    preview_integration_mapping,
    propose_repair_action,
    retry_outbox_event,
    run_integration_connection_check,
    summarize_integration_outbox,
    transition_business_record,
    write_audit,
)
from drivedesk_api.session import get_session
from drivedesk_api.settings import Settings, get_settings
from drivedesk_api.tenant_repository import list_tenant_owned
from drivedesk_api.tenant_scope import list_tenants_for_actor, list_users_for_actor
from drivedesk_core import __version__ as core_version
from drivedesk_core import (
    list_adapter_descriptors,
    list_integration_runbooks,
    list_lifecycle_policies,
    preview_lifecycle_transition,
)


request_logger = logging.getLogger("drivedesk.api.requests")
metrics_logger = logging.getLogger("drivedesk.api.metrics")


def build_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    api = FastAPI(title="DriveDesk Core API", version=core_version)
    api.state.settings = resolved_settings

    @api.middleware("http")
    async def log_request(request: Request, call_next) -> Response:
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_seconds = perf_counter() - started_at
            duration_ms = round(duration_seconds * 1000, 3)
            path = route_template_for_scope(request.scope, request.url.path)
            record_http_request(
                method=request.method,
                path=path,
                status_code=status_code,
                duration_seconds=duration_seconds,
            )
            log_json(
                request_logger,
                "http.request",
                service=resolved_settings.service_name,
                environment=resolved_settings.environment,
                core_version=core_version,
                method=request.method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )

    @api.get("/health")
    async def health() -> dict[str, str]:
        return build_health_payload(resolved_settings, core_version)

    @api.get("/ready")
    async def ready() -> dict[str, object]:
        return build_ready_payload(resolved_settings)

    @api.get("/demo/public", response_model=PublicDemoRead, tags=["demo"])
    async def public_demo() -> JSONResponse:
        return JSONResponse(
            build_public_demo_payload(),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=60",
            },
        )

    @api.get("/integration-adapters", response_model=list[AdapterContractRead], tags=["integrations"])
    async def list_integration_adapters_endpoint() -> list[dict[str, object]]:
        return list_adapter_descriptors()

    @api.get("/integration-runbooks", response_model=list[IntegrationRunbookRead], tags=["integrations"])
    async def list_integration_runbooks_endpoint() -> list[dict[str, object]]:
        return list_integration_runbooks()

    @api.get(
        "/business-record-lifecycle-policies",
        response_model=list[BusinessRecordLifecyclePolicyRead],
        tags=["business-records"],
    )
    async def list_business_record_lifecycle_policies_endpoint() -> list[dict[str, object]]:
        return list_lifecycle_policies()

    @api.get("/metrics", include_in_schema=False)
    async def metrics(session: AsyncSession = Depends(get_session)) -> PlainTextResponse:
        storage_available = True
        try:
            outbox_counts = await count_outbox_by_status(session)
            integration_rows = await summarize_integration_outbox(session)
            auth_session_counts = await count_auth_sessions_by_status(session)
            auth_attempt_counts = await count_auth_attempts_by_outcome(session)
            business_record_rows = await count_business_records_by_type_status(session)
            workflow_rule_rows = await count_workflow_rules_by_status_trigger_action(session)
            workflow_action_run_rows = await count_workflow_action_runs_by_action_status(session)
            business_state_observation_rows = await count_business_state_observations_by_system_state(session)
            business_exception_rows = await count_business_exceptions_by_type_severity_status(session)
            repair_action_rows = await count_repair_actions_by_action_status(session)
            integration_connection_rows = await count_integration_connections_by_adapter_status(session)
            integration_connection_check_rows = await count_integration_connection_checks_by_adapter_status(session)
            integration_reconciliation_rows = await count_integration_reconciliations_by_adapter_status(session)
            integration_incident_rows = await count_integration_incidents_by_adapter_severity_status(session)
        except Exception as exc:
            # Keep Prometheus scrapeable even when storage-backed aggregates degrade.
            storage_available = False
            await session.rollback()
            outbox_counts = {}
            integration_rows = []
            auth_session_counts = {}
            auth_attempt_counts = {}
            business_record_rows = []
            workflow_rule_rows = []
            workflow_action_run_rows = []
            business_state_observation_rows = []
            business_exception_rows = []
            repair_action_rows = []
            integration_connection_rows = []
            integration_connection_check_rows = []
            integration_reconciliation_rows = []
            integration_incident_rows = []
            log_json(
                metrics_logger,
                "metrics.storage_unavailable",
                service=resolved_settings.service_name,
                environment=resolved_settings.environment,
                core_version=core_version,
                reason=exc.__class__.__name__,
            )
        return PlainTextResponse(
            build_metrics_text(
                resolved_settings,
                core_version,
                outbox_counts=outbox_counts,
                integration_rows=integration_rows,
                auth_session_counts=auth_session_counts,
                auth_attempt_counts=auth_attempt_counts,
                business_record_rows=business_record_rows,
                workflow_rule_rows=workflow_rule_rows,
                workflow_action_run_rows=workflow_action_run_rows,
                business_state_observation_rows=business_state_observation_rows,
                business_exception_rows=business_exception_rows,
                repair_action_rows=repair_action_rows,
                integration_connection_rows=integration_connection_rows,
                integration_connection_check_rows=integration_connection_check_rows,
                integration_reconciliation_rows=integration_reconciliation_rows,
                integration_incident_rows=integration_incident_rows,
                storage_available=storage_available,
            ),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    @api.post("/auth/login", response_model=AccessTokenRead, tags=["auth"])
    async def login_endpoint(
        payload: LoginRequest,
        session: AsyncSession = Depends(get_session),
    ) -> AccessTokenRead:
        if await is_login_guard_active(
            session,
            email=payload.email,
            failed_login_limit=resolved_settings.auth_failed_login_limit,
            window_seconds=resolved_settings.auth_failed_login_window_seconds,
        ):
            await record_auth_attempt(
                session,
                email=payload.email,
                outcome="locked",
                reason="too_many_failed_attempts",
            )
            await write_auth_audit(
                session,
                event_type="auth.login.locked",
                email=payload.email,
                summary="Login blocked by failed-attempt guard.",
                reason="too_many_failed_attempts",
            )
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="too many failed login attempts",
            )

        user = await authenticate_user(session, email=payload.email, secret=payload.password)
        if not user:
            await record_auth_attempt(
                session,
                email=payload.email,
                outcome="failure",
                reason="invalid_credentials",
            )
            await write_auth_audit(
                session,
                event_type="auth.login.failed",
                email=payload.email,
                summary="Login failed.",
                reason="invalid_credentials",
            )
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid credentials",
            )

        access_token, token_row = await issue_access_token(
            session,
            user=user,
            ttl=timedelta(seconds=resolved_settings.auth_token_ttl_seconds),
        )
        await record_auth_attempt(
            session,
            email=user.email,
            outcome="success",
            reason="credentials_verified",
            user_id=user.id,
        )
        await write_auth_audit(
            session,
            event_type="auth.login.succeeded",
            email=user.email,
            summary="Login succeeded.",
            user_id=user.id,
            token_id=token_row.id,
            reason="credentials_verified",
        )
        await session.commit()
        return AccessTokenRead(access_token=access_token, expires_at=token_row.expires_at, user=user)

    @api.get("/auth/me", response_model=AuthMeRead, tags=["auth"])
    async def me_endpoint(
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> AuthMeRead:
        if actor.source != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="bearer token required",
            )
        user = await session.get(User, actor.actor_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid access token subject",
            )
        memberships = await list_active_memberships(session, user_id=user.id)
        platform_admins = await list_active_platform_admins(session, user_id=user.id)
        return AuthMeRead(
            user=user,
            memberships=memberships,
            platform_roles=[admin.role for admin in platform_admins],
        )

    @api.post("/auth/logout", response_model=TokenRevocationRead, tags=["auth"])
    async def logout_endpoint(
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> TokenRevocationRead:
        if actor.source != "bearer" or not actor.token_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="bearer token required",
            )
        token = await revoke_access_token(session, token_id=actor.token_id, user_id=actor.actor_id)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid access token subject",
            )
        await write_auth_audit(
            session,
            event_type="auth.token.revoked",
            email=actor.email or actor.actor_id,
            summary="Access token revoked.",
            user_id=actor.actor_id,
            token_id=token.id,
            reason="user_logout",
        )
        await session.commit()
        return TokenRevocationRead(revoked=True, token_id=token.id, status="revoked")

    @api.get("/auth/sessions", response_model=list[AuthSessionRead], tags=["auth"])
    async def list_auth_sessions_endpoint(
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[AuthSessionRead]:
        if actor.source != "bearer":
            require_permission(actor, Permission.AUTH_SESSION_READ)
            return await list_auth_sessions(session)

        if actor.is_platform_admin():
            require_permission(actor, Permission.AUTH_SESSION_READ)
            return await list_auth_sessions(session)

        allowed_tenant_ids = tenant_ids_with_permission(actor, Permission.AUTH_SESSION_READ)
        if not allowed_tenant_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"permission required: {Permission.AUTH_SESSION_READ.value}",
            )
        return await list_auth_sessions(session, allowed_tenant_ids=allowed_tenant_ids)

    @api.post("/auth/sessions/{session_id}/revoke", response_model=TokenRevocationRead, tags=["auth"])
    async def revoke_auth_session_endpoint(
        session_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> TokenRevocationRead:
        if actor.source != "bearer":
            require_permission(actor, Permission.AUTH_SESSION_WRITE)
            auth_session = await get_auth_session(session, token_id=session_id)
        elif actor.is_platform_admin():
            require_permission(actor, Permission.AUTH_SESSION_WRITE)
            auth_session = await get_auth_session(session, token_id=session_id)
        else:
            allowed_tenant_ids = tenant_ids_with_permission(actor, Permission.AUTH_SESSION_WRITE)
            if not allowed_tenant_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"permission required: {Permission.AUTH_SESSION_WRITE.value}",
                )
            auth_session = await get_auth_session(
                session,
                token_id=session_id,
                allowed_tenant_ids=allowed_tenant_ids,
            )

        if auth_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="auth session not found",
            )

        token = await revoke_access_token_by_id(session, token_id=auth_session.token_id)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="auth session not found",
            )

        await write_audit(
            session,
            tenant_id="platform",
            actor=actor,
            event_type="auth.token.admin_revoked",
            entity_type="auth_session",
            entity_id=token.id,
            summary="Auth session revoked by admin.",
            metadata={
                "target_user_id": auth_session.user_id,
                "target_user_email": auth_session.user_email,
                "visible_tenant_ids": auth_session.tenant_ids,
            },
        )
        await session.commit()
        return TokenRevocationRead(revoked=True, token_id=token.id, status="revoked")

    @api.post("/platform/admins", response_model=PlatformAdminRead, status_code=201, tags=["platform"])
    async def create_platform_admin_endpoint(
        payload: PlatformAdminCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> PlatformAdmin:
        require_platform_bootstrap_permission(actor, Permission.PLATFORM_ADMIN_WRITE)
        return await create_platform_admin(session, payload, actor)

    @api.get("/platform/admins", response_model=list[PlatformAdminRead], tags=["platform"])
    async def list_platform_admins_endpoint(
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[PlatformAdmin]:
        require_platform_bootstrap_permission(actor, Permission.PLATFORM_ADMIN_READ)
        return await list_platform_admins(session)

    @api.post("/tenants", response_model=TenantRead, status_code=201)
    async def create_tenant_endpoint(
        payload: TenantCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> Tenant:
        require_platform_bootstrap_permission(actor, Permission.TENANT_WRITE)
        return await create_tenant(session, payload, actor)

    @api.get("/tenants", response_model=list[TenantRead])
    async def list_tenants_endpoint(
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[Tenant]:
        require_permission(actor, Permission.TENANT_READ)
        return await list_tenants_for_actor(session, actor)

    @api.get("/tenants/{tenant_id}", response_model=TenantRead)
    async def get_tenant_endpoint(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> Tenant:
        tenant = await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return tenant

    @api.post("/users", response_model=UserRead, status_code=201)
    async def create_user_endpoint(
        payload: UserCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> User:
        require_platform_bootstrap_permission(actor, Permission.USER_WRITE)
        return await create_user(session, payload, actor)

    @api.get("/users", response_model=list[UserRead])
    async def list_users_endpoint(
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[User]:
        require_permission(actor, Permission.USER_READ)
        return await list_users_for_actor(session, actor)

    @api.post("/tenants/{tenant_id}/memberships", response_model=MembershipRead, status_code=201)
    async def create_membership_endpoint(
        tenant_id: str,
        payload: MembershipCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> Membership:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.MEMBERSHIP_WRITE)
        return await create_membership(session, tenant_id=tenant_id, payload=payload, actor=actor)

    @api.get("/tenants/{tenant_id}/memberships", response_model=list[MembershipRead])
    async def list_memberships_endpoint(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[Membership]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.MEMBERSHIP_READ)
        return await list_tenant_owned(session, Membership, tenant_id, order_by=Membership.created_at.desc())

    @api.get("/tenants/{tenant_id}/audit-events", response_model=list[AuditEventRead])
    async def list_audit_events_endpoint(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[AuditEvent]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.AUDIT_READ)
        return await list_tenant_owned(session, AuditEvent, tenant_id, order_by=AuditEvent.created_at.desc())

    @api.get("/tenants/{tenant_id}/outbox-events", response_model=list[OutboxEventRead])
    async def list_outbox_events_endpoint(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[OutboxEvent]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.OUTBOX_READ)
        return await list_tenant_owned(session, OutboxEvent, tenant_id, order_by=OutboxEvent.created_at.desc())

    @api.post("/tenants/{tenant_id}/outbox-events/{event_id}/retry", response_model=OutboxEventRead)
    async def retry_outbox_event_endpoint(
        tenant_id: str,
        event_id: str,
        payload: OutboxEventRetryRequest,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> OutboxEvent:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.OUTBOX_READ)
        return await retry_outbox_event(
            session,
            tenant_id=tenant_id,
            event_id=event_id,
            payload=payload,
            actor=actor,
        )

    @api.get(
        "/tenants/{tenant_id}/integration-operator-review",
        response_model=list[IntegrationOperatorReviewItemRead],
        tags=["integrations"],
    )
    async def list_integration_operator_review_endpoint(
        tenant_id: str,
        status_filter: str | None = Query(default=None, alias="status"),
        adapter_key: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[dict[str, object]]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.OUTBOX_READ)
        return await list_integration_operator_review(
            session,
            tenant_id=tenant_id,
            status_filter=status_filter,
            adapter_key=adapter_key,
            limit=limit,
        )

    @api.post(
        "/tenants/{tenant_id}/integration-reconciliations",
        response_model=IntegrationReconciliationRead,
        status_code=201,
        tags=["integrations"],
    )
    async def create_integration_reconciliation_endpoint(
        tenant_id: str,
        payload: IntegrationReconciliationCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> IntegrationReconciliation:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_WRITE)
        return await create_integration_reconciliation(
            session,
            tenant_id=tenant_id,
            payload=payload,
            actor=actor,
        )

    @api.get(
        "/tenants/{tenant_id}/integration-reconciliations",
        response_model=list[IntegrationReconciliationRead],
        tags=["integrations"],
    )
    async def list_integration_reconciliations_endpoint(
        tenant_id: str,
        status_filter: str | None = Query(default=None, alias="status"),
        adapter_key: str | None = Query(default=None),
        outbox_event_id: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[IntegrationReconciliation]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return await list_integration_reconciliations(
            session,
            tenant_id=tenant_id,
            status_filter=status_filter,
            adapter_key=adapter_key,
            outbox_event_id=outbox_event_id,
            limit=limit,
        )

    @api.post(
        "/tenants/{tenant_id}/integration-incidents",
        response_model=IntegrationIncidentRead,
        status_code=201,
        tags=["integrations"],
    )
    async def create_integration_incident_endpoint(
        tenant_id: str,
        payload: IntegrationIncidentCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> IntegrationIncident:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_WRITE)
        return await create_integration_incident(
            session,
            tenant_id=tenant_id,
            payload=payload,
            actor=actor,
        )

    @api.get(
        "/tenants/{tenant_id}/integration-incidents",
        response_model=list[IntegrationIncidentRead],
        tags=["integrations"],
    )
    async def list_integration_incidents_endpoint(
        tenant_id: str,
        status_filter: str | None = Query(default=None, alias="status"),
        severity: str | None = Query(default=None),
        adapter_key: str | None = Query(default=None),
        source_type: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[IntegrationIncident]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return await list_integration_incidents(
            session,
            tenant_id=tenant_id,
            status_filter=status_filter,
            severity=severity,
            adapter_key=adapter_key,
            source_type=source_type,
            limit=limit,
        )

    @api.post(
        "/tenants/{tenant_id}/integration-incidents/{incident_id}/status",
        response_model=IntegrationIncidentRead,
        tags=["integrations"],
    )
    async def change_integration_incident_status_endpoint(
        tenant_id: str,
        incident_id: str,
        payload: IntegrationIncidentStatusChange,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> IntegrationIncident:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_WRITE)
        return await change_integration_incident_status(
            session,
            tenant_id=tenant_id,
            incident_id=incident_id,
            payload=payload,
            actor=actor,
        )

    @api.post(
        "/tenants/{tenant_id}/integration-connections",
        response_model=IntegrationConnectionRead,
        status_code=201,
    )
    async def create_integration_connection_endpoint(
        tenant_id: str,
        payload: IntegrationConnectionCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> IntegrationConnection:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_WRITE)
        return await create_integration_connection(
            session,
            tenant_id=tenant_id,
            payload=payload,
            actor=actor,
        )

    @api.get("/tenants/{tenant_id}/integration-connections", response_model=list[IntegrationConnectionRead])
    async def list_integration_connections_endpoint(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[IntegrationConnection]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return await list_integration_connections(session, tenant_id=tenant_id)

    @api.post(
        "/tenants/{tenant_id}/integration-connections/{connection_id}/health-checks",
        response_model=IntegrationConnectionCheckRead,
        status_code=201,
        tags=["integrations"],
    )
    async def run_integration_connection_check_endpoint(
        tenant_id: str,
        connection_id: str,
        payload: IntegrationConnectionCheckCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> IntegrationConnectionCheck:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_WRITE)
        return await run_integration_connection_check(
            session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            payload=payload,
            actor=actor,
        )

    @api.get(
        "/tenants/{tenant_id}/integration-connections/{connection_id}/health-checks",
        response_model=list[IntegrationConnectionCheckRead],
        tags=["integrations"],
    )
    async def list_integration_connection_checks_endpoint(
        tenant_id: str,
        connection_id: str,
        limit: int = Query(default=25, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[IntegrationConnectionCheck]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return await list_integration_connection_checks(
            session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            limit=limit,
        )

    @api.get(
        "/tenants/{tenant_id}/integration-connections/{connection_id}/health",
        response_model=IntegrationConnectionHealthRead,
        tags=["integrations"],
    )
    async def get_integration_connection_health_endpoint(
        tenant_id: str,
        connection_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> dict[str, object]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return await get_integration_connection_health(session, tenant_id=tenant_id, connection_id=connection_id)

    @api.post(
        "/tenants/{tenant_id}/integration-mapping-preview",
        response_model=IntegrationMappingPreviewRead,
        tags=["integrations"],
    )
    async def preview_integration_mapping_endpoint(
        tenant_id: str,
        payload: IntegrationMappingPreviewCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> dict[str, object]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return await preview_integration_mapping(session, tenant_id=tenant_id, payload=payload)

    @api.post("/tenants/{tenant_id}/business-records", response_model=BusinessRecordRead, status_code=201)
    async def create_business_record_endpoint(
        tenant_id: str,
        payload: BusinessRecordCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> BusinessRecord:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_WRITE)
        return await create_business_record(session, tenant_id=tenant_id, payload=payload, actor=actor)

    @api.get("/tenants/{tenant_id}/business-records", response_model=list[BusinessRecordRead])
    async def list_business_records_endpoint(
        tenant_id: str,
        record_type: BusinessRecordType | None = Query(default=None),
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[BusinessRecord]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_READ)
        return await list_business_records(session, tenant_id=tenant_id, record_type=record_type)

    @api.post(
        "/tenants/{tenant_id}/business-records/lifecycle-preview",
        response_model=BusinessRecordLifecyclePreviewRead,
        tags=["business-records"],
    )
    async def preview_business_record_lifecycle_endpoint(
        tenant_id: str,
        payload: BusinessRecordLifecyclePreviewCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> dict[str, object]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_READ)
        return preview_lifecycle_transition(
            payload.record_type,
            from_status=payload.from_status,
            to_status=payload.to_status,
        )

    @api.post(
        "/tenants/{tenant_id}/business-records/{record_id}/transition",
        response_model=BusinessRecordRead,
    )
    async def transition_business_record_endpoint(
        tenant_id: str,
        record_id: str,
        payload: BusinessRecordTransition,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> BusinessRecord:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_WRITE)
        return await transition_business_record(
            session,
            tenant_id=tenant_id,
            record_id=record_id,
            payload=payload,
            actor=actor,
        )

    @api.post(
        "/tenants/{tenant_id}/business-detections/preview",
        response_model=BusinessDetectionPreviewRead,
        tags=["business-control"],
    )
    async def preview_business_detections_endpoint(
        tenant_id: str,
        payload: BusinessDetectionPreviewCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> dict[str, object]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_READ)
        return await preview_business_detections(session, tenant_id=tenant_id, payload=payload)

    @api.post(
        "/tenants/{tenant_id}/business-briefings/preview",
        response_model=BusinessBriefingRead,
        tags=["business-control"],
    )
    async def build_business_briefing_endpoint(
        tenant_id: str,
        payload: BusinessBriefingPreviewCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> dict[str, object]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_READ)
        return await build_business_briefing(session, tenant_id=tenant_id, payload=payload)

    @api.post(
        "/tenants/{tenant_id}/business-state/observations",
        response_model=BusinessStateObservationRead,
        status_code=201,
        tags=["business-control"],
    )
    async def create_business_state_observation_endpoint(
        tenant_id: str,
        payload: BusinessStateObservationCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> BusinessStateObservation:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_WRITE)
        return await create_business_state_observation(
            session,
            tenant_id=tenant_id,
            payload=payload,
            actor=actor,
        )

    @api.get(
        "/tenants/{tenant_id}/business-state/observations",
        response_model=list[BusinessStateObservationRead],
        tags=["business-control"],
    )
    async def list_business_state_observations_endpoint(
        tenant_id: str,
        system_key: str | None = Query(default=None),
        subject_type: str | None = Query(default=None),
        subject_id: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[BusinessStateObservation]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_READ)
        return await list_business_state_observations(
            session,
            tenant_id=tenant_id,
            system_key=system_key,
            subject_type=subject_type,
            subject_id=subject_id,
            limit=limit,
        )

    @api.post(
        "/tenants/{tenant_id}/business-exceptions",
        response_model=BusinessExceptionRead,
        status_code=201,
        tags=["business-control"],
    )
    async def create_business_exception_endpoint(
        tenant_id: str,
        payload: BusinessExceptionCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> BusinessException:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_WRITE)
        return await create_business_exception(
            session,
            tenant_id=tenant_id,
            payload=payload,
            actor=actor,
        )

    @api.get(
        "/tenants/{tenant_id}/business-exceptions",
        response_model=list[BusinessExceptionRead],
        tags=["business-control"],
    )
    async def list_business_exceptions_endpoint(
        tenant_id: str,
        status_filter: str | None = Query(default=None, alias="status"),
        severity: str | None = Query(default=None),
        exception_type: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[BusinessException]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_READ)
        return await list_business_exceptions(
            session,
            tenant_id=tenant_id,
            status_filter=status_filter,
            severity=severity,
            exception_type=exception_type,
            limit=limit,
        )

    @api.post(
        "/tenants/{tenant_id}/business-exceptions/{business_exception_id}/status",
        response_model=BusinessExceptionRead,
        tags=["business-control"],
    )
    async def change_business_exception_status_endpoint(
        tenant_id: str,
        business_exception_id: str,
        payload: BusinessExceptionStatusChange,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> BusinessException:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_WRITE)
        return await change_business_exception_status(
            session,
            tenant_id=tenant_id,
            business_exception_id=business_exception_id,
            payload=payload,
            actor=actor,
        )

    @api.post(
        "/tenants/{tenant_id}/business-exceptions/{business_exception_id}/repair-actions",
        response_model=RepairActionRead,
        status_code=201,
        tags=["business-control"],
    )
    async def propose_repair_action_endpoint(
        tenant_id: str,
        business_exception_id: str,
        payload: RepairActionPropose,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> RepairAction:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_WRITE)
        return await propose_repair_action(
            session,
            tenant_id=tenant_id,
            business_exception_id=business_exception_id,
            payload=payload,
            actor=actor,
        )

    @api.get(
        "/tenants/{tenant_id}/repair-actions",
        response_model=list[RepairActionRead],
        tags=["business-control"],
    )
    async def list_repair_actions_endpoint(
        tenant_id: str,
        business_exception_id: str | None = Query(default=None),
        status_filter: str | None = Query(default=None, alias="status"),
        limit: int = Query(default=50, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[RepairAction]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_READ)
        return await list_repair_actions(
            session,
            tenant_id=tenant_id,
            business_exception_id=business_exception_id,
            status_filter=status_filter,
            limit=limit,
        )

    @api.post(
        "/tenants/{tenant_id}/repair-actions/{repair_action_id}/approve",
        response_model=RepairActionRead,
        tags=["business-control"],
    )
    async def approve_repair_action_endpoint(
        tenant_id: str,
        repair_action_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> RepairAction:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_WRITE)
        return await approve_repair_action(
            session,
            tenant_id=tenant_id,
            repair_action_id=repair_action_id,
            actor=actor,
        )

    @api.post(
        "/tenants/{tenant_id}/repair-actions/{repair_action_id}/execute",
        response_model=RepairActionRead,
        tags=["business-control"],
    )
    async def execute_repair_action_endpoint(
        tenant_id: str,
        repair_action_id: str,
        payload: RepairActionExecutionRequest,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> RepairAction:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.BUSINESS_RECORD_WRITE)
        return await execute_repair_action(
            session,
            tenant_id=tenant_id,
            repair_action_id=repair_action_id,
            payload=payload,
            actor=actor,
        )

    @api.post("/tenants/{tenant_id}/workflow-rules", response_model=WorkflowRuleRead, status_code=201)
    async def create_workflow_rule_endpoint(
        tenant_id: str,
        payload: WorkflowRuleCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> WorkflowRule:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_WRITE)
        return await create_workflow_rule(session, tenant_id=tenant_id, payload=payload, actor=actor)

    @api.get("/tenants/{tenant_id}/workflow-rules", response_model=list[WorkflowRuleRead])
    async def list_workflow_rules_endpoint(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[WorkflowRule]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return await list_workflow_rules(session, tenant_id=tenant_id)

    @api.get("/tenants/{tenant_id}/workflow-action-runs", response_model=list[WorkflowActionRunRead])
    async def list_workflow_action_runs_endpoint(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> list[WorkflowActionRun]:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_READ)
        return await list_workflow_action_runs(session, tenant_id=tenant_id)

    @api.post("/tenants/{tenant_id}/integration-imports/file", response_model=OutboxEventRead, status_code=202)
    async def create_file_import_endpoint(
        tenant_id: str,
        payload: FileImportCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> OutboxEvent:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_WRITE)
        return await create_file_import_job(session, tenant_id=tenant_id, payload=payload, actor=actor)

    @api.post(
        "/tenants/{tenant_id}/integration-exports/accounting",
        response_model=OutboxEventRead,
        status_code=202,
        tags=["integrations"],
    )
    async def create_accounting_export_endpoint(
        tenant_id: str,
        payload: AccountingExportCreate,
        session: AsyncSession = Depends(get_session),
        actor: ActorContext = Depends(actor_context),
    ) -> OutboxEvent:
        await ensure_tenant_exists(session, tenant_id)
        require_tenant_permission(actor, tenant_id, Permission.TENANT_WRITE)
        return await create_accounting_export_job(session, tenant_id=tenant_id, payload=payload, actor=actor)

    return api


app = build_app()
