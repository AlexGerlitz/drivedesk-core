from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "apps/admin/public-demo"


def _demo_data() -> dict[str, object]:
    source = (DEMO_DIR / "demo-data.js").read_text(encoding="utf-8")
    match = re.search(r"window\.DRIVEDESK_DEMO_DATA\s*=\s*(\{.*\});\s*$", source, flags=re.DOTALL)
    assert match, "demo data assignment not found"
    return json.loads(match.group(1))


def test_public_demo_files_exist() -> None:
    expected = {
        "README.md",
        "index.html",
        "styles.css",
        "demo-data.js",
        "app.js",
    }

    for relative in expected:
        assert (DEMO_DIR / relative).is_file(), relative


def test_public_demo_html_links_static_assets() -> None:
    html = (DEMO_DIR / "index.html").read_text(encoding="utf-8")

    assert "./styles.css" in html
    assert "./demo-data.js" in html
    assert "./app.js" in html
    assert 'data-demo-api-path="/demo/public"' in html
    assert 'id="metricGrid"' in html
    assert 'id="workQueueRows"' in html
    assert 'id="integrationHealthRows"' in html
    assert 'id="adapterRows"' in html
    assert 'id="syncJobRows"' in html
    assert 'id="outboxRows"' in html


def test_public_demo_data_is_synthetic_and_product_shaped() -> None:
    payload = _demo_data()

    assert payload["schemaVersion"] == 1
    assert payload["dataSource"] == "static.fallback"
    assert payload["apiContract"]["path"] == "/demo/public"
    assert payload["apiContract"]["data_profile"] == "synthetic_fake_data"
    assert payload["tenant"]["slug"] == "demo-academy"
    assert payload["tenant"]["status"] == "active"
    assert len(payload["metrics"]) >= 4
    assert len(payload["workQueue"]) >= 4
    assert len(payload["members"]) >= 3
    assert len(payload["auditEvents"]) >= 3
    assert len(payload["adapters"]) >= 3
    assert len(payload["integrationJobs"]) >= 3
    assert len(payload["integrationHealth"]) >= 4
    assert len(payload["outbox"]) >= 3
    assert {event["status"] for event in payload["outbox"]} >= {"processed", "pending"}
    assert {job["status"] for job in payload["integrationJobs"]} >= {"processed", "retry", "dead_letter"}
    assert {item["state"] for item in payload["integrationHealth"]} >= {
        "processed",
        "retry",
        "dead_letter",
    }


def test_public_demo_can_load_api_backed_data_with_static_fallback() -> None:
    script = (DEMO_DIR / "app.js").read_text(encoding="utf-8")

    assert "loadApiBackedDemoData" in script
    assert "demoApi" in script
    assert "data-demo-api-path" not in script
    assert "dataset.demoApiPath" in script
    assert "/demo/public" in script
    assert "static.fallback" not in script
    assert "api.synthetic" not in script
    assert "fetch(url" in script
    assert "return fallbackData" in script


def test_public_demo_api_scripts_and_examples_exist() -> None:
    expected = {
        "scripts/run_public_demo_local.sh",
        "scripts/check_public_demo_api.sh",
        "examples/curl/demo-public.sh",
        "examples/python/demo_public_client.py",
        "examples/js/demo-public-fetch.js",
    }

    for relative in expected:
        assert (ROOT / relative).is_file(), relative


def test_public_demo_api_scripts_and_examples_target_demo_contract() -> None:
    scripts = {
        "scripts/run_public_demo_local.sh": ["uvicorn", "/demo/public"],
        "scripts/check_public_demo_api.sh": ["/health", "/ready", "/demo/public", "/openapi.json"],
        "examples/curl/demo-public.sh": ["/demo/public", "api.synthetic"],
        "examples/python/demo_public_client.py": ["/demo/public", "api.synthetic"],
        "examples/js/demo-public-fetch.js": ["/demo/public", "api.synthetic"],
    }

    for relative, required_fragments in scripts.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for fragment in required_fragments:
            assert fragment in text, f"{fragment} missing from {relative}"


def test_public_demo_has_no_private_runtime_markers() -> None:
    private_patterns = [
        r"auto\s*school\s*54",
        r"auto" r"school54",
        r"duck" r"dns",
        r"land" r"vps",
        r"215" r"689",
        r"185" r"\.80\.",
        r"152" r"\.53\.",
        r"2a0a:",
        r"/opt/",
        r"\.env",
        r"xr" r"ay",
        r"telegram token",
        r"private key",
        r"password",
    ]
    ipv4_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    for path in DEMO_DIR.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for pattern in private_patterns:
            assert not re.search(pattern, lowered), f"{pattern} found in {path}"
        assert not ipv4_pattern.search(text), f"IPv4 address found in {path}"
