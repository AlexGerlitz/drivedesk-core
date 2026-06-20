#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = str(ROOT / "packages/core")
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)

from drivedesk_core import build_provider_sandbox_dry_run_plan, execute_provider_sandbox_dry_run


SANDBOX_ENV_KEYS = (
    "BITRIX24_CLIENT_SECRET",
    "BITRIX24_WEBHOOK_URL",
    "BITRIX24_TENANT_DOMAIN",
)

SUCCESS_STATUSES = {
    "ready_for_private_read_only_dry_run",
    "provider_call_prepared",
    "private_read_only_dry_run_completed",
}


def _sandbox_env(env: Mapping[str, str]) -> dict[str, str]:
    return {key: str(env.get(key) or "") for key in SANDBOX_ENV_KEYS}


def _json_http_transport(request: dict[str, object]) -> Mapping[str, object]:
    url = str(request.get("url") or "")
    method = str(request.get("method") or "POST")
    timeout_seconds = int(request.get("timeout_seconds") or 10)
    body = json.dumps(request.get("json") or {}).encode("utf-8")
    http_request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "DriveDeskProviderSandboxDryRun/1.0",
        },
    )

    try:
        with urllib.request.urlopen(http_request, timeout=timeout_seconds) as response:
            response_body = response.read(2_000_000)
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP_{exc.code}"}
    except urllib.error.URLError as exc:
        raise RuntimeError(exc.__class__.__name__) from exc

    try:
        parsed = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"error": "INVALID_JSON_RESPONSE"}
    if isinstance(parsed, Mapping):
        return parsed
    return {"error": "NON_OBJECT_RESPONSE"}


def _fake_transport(request: dict[str, object]) -> Mapping[str, object]:
    return {
        "result": [
            {
                "ID": "DEAL-PRIVATE-DRY-RUN-001",
                "STAGE_ID": "NEW",
                "ASSIGNED_BY_ID": "7",
                "OPPORTUNITY": "1500",
                "PHONE": "+70000000000",
                "CLIENT_NAME": "Hidden Person",
                "access_token": "secret-token",
            },
            {
                "ID": "",
                "STAGE_ID": "BROKEN",
                "EMAIL": "hidden@example.invalid",
            },
        ],
        "total": 2,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a DriveDesk provider sandbox dry-run without printing provider secrets.",
    )
    parser.add_argument("--adapter-key", default="crm.bitrix24.mock")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Only validate secret/config binding and print a sanitized request plan.",
    )
    parser.add_argument(
        "--execute-read-only",
        action="store_true",
        help="Execute one bounded read-only provider call. Requires explicit opt-in.",
    )
    parser.add_argument(
        "--transport",
        choices=("http", "fake"),
        default="http",
        help="Transport for --execute-read-only. Use fake for CI and public-safe checks.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for sanitized JSON evidence. The same JSON is still printed to stdout.",
    )
    return parser


def run_provider_sandbox_dry_run(
    argv: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    stdout: TextIO | None = None,
) -> int:
    args = _build_parser().parse_args(argv)
    output = stdout or sys.stdout
    env_values = _sandbox_env(env or os.environ)

    if args.execute_read_only:
        transport = _fake_transport if args.transport == "fake" else _json_http_transport
        payload = execute_provider_sandbox_dry_run(
            args.adapter_key,
            env=env_values,
            allow_provider_call=True,
            provider_transport=transport,
        )
        payload = {
            **payload,
            "operator_cli": {
                "script": "scripts/run_provider_sandbox_dry_run.py",
                "mode": "execute_read_only",
                "transport": args.transport,
                "secret_values_included": False,
                "raw_provider_payload_included": False,
            },
        }
    else:
        payload = build_provider_sandbox_dry_run_plan(
            args.adapter_key,
            env=env_values,
            allow_provider_call=False,
        )
        payload = {
            **payload,
            "operator_cli": {
                "script": "scripts/run_provider_sandbox_dry_run.py",
                "mode": "plan_only",
                "transport": "none",
                "secret_values_included": False,
                "raw_provider_payload_included": False,
            },
        }

    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    output.write(serialized + "\n")
    return 0 if str(payload.get("status")) in SUCCESS_STATUSES else 2


def main() -> None:
    raise SystemExit(run_provider_sandbox_dry_run())


if __name__ == "__main__":
    main()
