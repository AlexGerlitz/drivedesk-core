from __future__ import annotations

import logging
from datetime import timedelta
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response

from drivedesk_api.db import AuditEvent, Membership, OutboxEvent, Tenant, User
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
    record_auth_attempt,
    revoke_access_token,
    write_auth_audit,
)
from drivedesk_api.rbac import (
    ActorContext,
    Permission,
    actor_context,
    require_permission,
    require_platform_bootstrap_permission,
    require_tenant_permission,
)
from drivedesk_api.schemas import (
    AccessTokenRead,
    AuditEventRead,
    AuthMeRead,
    FileImportCreate,
    LoginRequest,
    MembershipCreate,
    MembershipRead,
    OutboxEventRead,
    PublicDemoRead,
    TenantCreate,
    TenantRead,
    TokenRevocationRead,
    UserCreate,
    UserRead,
)
from drivedesk_api.services import (
    count_outbox_by_status,
    create_file_import_job,
    create_membership,
    create_tenant,
    create_user,
    ensure_tenant_exists,
    summarize_integration_outbox,
)
from drivedesk_api.session import get_session
from drivedesk_api.settings import Settings, get_settings
from drivedesk_api.tenant_repository import list_tenant_owned
from drivedesk_api.tenant_scope import list_tenants_for_actor, list_users_for_actor
from drivedesk_core import __version__ as core_version


request_logger = logging.getLogger("drivedesk.api.requests")


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

    @api.get("/metrics", include_in_schema=False)
    async def metrics(session: AsyncSession = Depends(get_session)) -> PlainTextResponse:
        outbox_counts = await count_outbox_by_status(session)
        integration_rows = await summarize_integration_outbox(session)
        return PlainTextResponse(
            build_metrics_text(
                resolved_settings,
                core_version,
                outbox_counts=outbox_counts,
                integration_rows=integration_rows,
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
        return AuthMeRead(user=user, memberships=memberships)

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

    return api


app = build_app()
