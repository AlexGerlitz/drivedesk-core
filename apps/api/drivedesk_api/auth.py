from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from drivedesk_api.db import AccessToken, AuditEvent, AuthAttempt, Membership, User

_CREDENTIAL_ALGORITHM = "pbkdf2_sha256"
_CREDENTIAL_ITERATIONS = 210_000
_TOKEN_TTL = timedelta(hours=12)


@dataclass(frozen=True)
class AuthenticatedUser:
    user: User
    access_token: AccessToken
    memberships: list[Membership]


def _new_id() -> str:
    return str(uuid4())


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_credential(secret: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt,
        _CREDENTIAL_ITERATIONS,
    )
    return "$".join(
        [
            _CREDENTIAL_ALGORITHM,
            str(_CREDENTIAL_ITERATIONS),
            _b64encode(salt),
            _b64encode(digest),
        ]
    )


def verify_credential(secret: str, encoded_hash: str | None) -> bool:
    if not encoded_hash:
        return False
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = encoded_hash.split("$", 3)
        if algorithm != _CREDENTIAL_ALGORITHM:
            return False
        iterations = int(iterations_raw)
        salt = _b64decode(salt_raw)
        expected_digest = _b64decode(digest_raw)
    except (ValueError, TypeError):
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def generate_access_token_value() -> str:
    return secrets.token_urlsafe(32)


def hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def parse_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.strip().partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


async def authenticate_user(session: AsyncSession, *, email: str, secret: str) -> User | None:
    result = await session.execute(select(User).where(User.email == normalize_email(email), User.status == "active"))
    user = result.scalar_one_or_none()
    if not user or not verify_credential(secret, user.credential_hash):
        return None
    return user


async def issue_access_token(
    session: AsyncSession,
    *,
    user: User,
    ttl: timedelta = _TOKEN_TTL,
) -> tuple[str, AccessToken]:
    token_value = generate_access_token_value()
    now = datetime.now(UTC)
    token = AccessToken(
        id=_new_id(),
        user_id=user.id,
        token_hash=hash_access_token(token_value),
        status="active",
        expires_at=now + ttl,
    )
    session.add(token)
    await session.commit()
    return token_value, token


async def revoke_access_token(
    session: AsyncSession,
    *,
    token_id: str,
    user_id: str,
) -> AccessToken | None:
    token = await session.get(AccessToken, token_id)
    if not token or token.user_id != user_id:
        return None
    token.status = "revoked"
    token.revoked_at = datetime.now(UTC)
    return token


async def resolve_access_token(session: AsyncSession, *, token_value: str) -> AuthenticatedUser | None:
    token_hash = hash_access_token(token_value)
    result = await session.execute(
        select(AccessToken).where(AccessToken.token_hash == token_hash, AccessToken.status == "active")
    )
    access_token = result.scalar_one_or_none()
    if not access_token:
        return None

    now = datetime.now(UTC)
    if _as_utc(access_token.expires_at) <= now or access_token.revoked_at is not None:
        return None

    user = await session.get(User, access_token.user_id)
    if not user or user.status != "active":
        return None

    memberships = await list_active_memberships(session, user_id=user.id)
    access_token.last_used_at = now
    await session.commit()
    return AuthenticatedUser(user=user, access_token=access_token, memberships=memberships)


async def list_active_memberships(session: AsyncSession, *, user_id: str) -> list[Membership]:
    result = await session.execute(
        select(Membership)
        .where(Membership.user_id == user_id, Membership.status == "active")
        .order_by(Membership.created_at.desc())
    )
    return list(result.scalars().all())


async def count_recent_failed_attempts(
    session: AsyncSession,
    *,
    email: str,
    window_seconds: int,
) -> int:
    since = datetime.now(UTC) - timedelta(seconds=window_seconds)
    result = await session.execute(
        select(func.count())
        .select_from(AuthAttempt)
        .where(
            AuthAttempt.email == normalize_email(email),
            AuthAttempt.outcome == "failure",
            AuthAttempt.created_at >= since,
        )
    )
    return int(result.scalar_one())


async def is_login_guard_active(
    session: AsyncSession,
    *,
    email: str,
    failed_login_limit: int,
    window_seconds: int,
) -> bool:
    if failed_login_limit <= 0:
        return False
    failed_attempts = await count_recent_failed_attempts(
        session,
        email=email,
        window_seconds=window_seconds,
    )
    return failed_attempts >= failed_login_limit


async def record_auth_attempt(
    session: AsyncSession,
    *,
    email: str,
    outcome: str,
    reason: str | None = None,
    user_id: str | None = None,
) -> AuthAttempt:
    attempt = AuthAttempt(
        id=_new_id(),
        email=normalize_email(email),
        user_id=user_id,
        outcome=outcome,
        reason=reason,
        created_at=datetime.now(UTC),
    )
    session.add(attempt)
    return attempt


async def write_auth_audit(
    session: AsyncSession,
    *,
    event_type: str,
    email: str,
    summary: str,
    user_id: str | None = None,
    token_id: str | None = None,
    reason: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        id=_new_id(),
        tenant_id="platform",
        actor_id=user_id or normalize_email(email),
        event_type=event_type,
        entity_type="auth_session",
        entity_id=token_id or user_id,
        summary=summary,
        metadata_json=json.dumps(
            {
                "email": normalize_email(email),
                "reason": reason,
                "token_id": token_id,
                "user_id": user_id,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        created_at=datetime.now(UTC),
    )
    session.add(event)
    return event
