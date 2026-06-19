from __future__ import annotations

import os
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SDK_PATH = ROOT / "sdk/generated/public-demo/python"
sys.path.insert(0, str(SDK_PATH))

from drivedesk_public_demo_client import DriveDeskPublicDemoClient


def main() -> None:
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    client = DriveDeskPublicDemoClient(base_url)
    plan = client.get_adapter_operation_plan(
        "adapter-file-import-preview",
        request_id="example-preview-001",
    )
    crm_plan = client.get_adapter_operation_plan(
        "adapter-crm-deal-preview",
        request_id="example-crm-preview-001",
    )

    assert plan["executionMode"] == "contract_only"
    assert plan["safeToRunAgainstPublicDemo"] is False
    assert plan["phase"] == "preview"
    assert plan["request"]["method"] == "POST"
    assert plan["request"]["headers"]["Idempotency-Key"] == (
        "adapter-file-import-preview:example-preview-001"
    )
    assert plan["request"]["body"]["dryRun"] is True
    assert "mapping_preview" in plan["expectedResponse"]["outputs"]

    assert crm_plan["executionMode"] == "contract_only"
    assert crm_plan["safeToRunAgainstPublicDemo"] is False
    assert crm_plan["adapter"] == "crm.bitrix24.mock"
    assert crm_plan["operation"] == "crm_deal_intake_preview"
    assert crm_plan["phase"] == "preview"
    assert crm_plan["request"]["method"] == "POST"
    assert crm_plan["request"]["path"] == "/tenants/{tenant_id}/business-provider-intake/preview"
    assert crm_plan["request"]["headers"]["Idempotency-Key"] == (
        "adapter-crm-deal-preview:example-crm-preview-001"
    )
    assert crm_plan["request"]["body"]["provider_key"] == "crm.bitrix24.mock"
    assert crm_plan["request"]["body"]["source_type"] == "crm_deal"
    assert crm_plan["request"]["body"]["provider_payload"]["access_token"] == "never-return-this"
    assert "safe_payload" in crm_plan["expectedResponse"]["outputs"]
    assert "normalized_observation" in crm_plan["expectedResponse"]["outputs"]
    assert "no_provider_call" in crm_plan["expectedResponse"]["outputs"]

    print(
        "python adapter plan ok:",
        plan["scenarioId"],
        plan["request"]["method"],
        plan["phase"],
        plan["executionMode"],
        "crm=" + crm_plan["operation"],
    )


if __name__ == "__main__":
    main()
