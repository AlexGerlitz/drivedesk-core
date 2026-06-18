# Generated Public Demo SDK

This folder is generated from `docs/openapi.json` by:

```bash
python scripts/generate_public_demo_sdk.py --openapi docs/openapi.json --out sdk/generated/public-demo
```

Generated clients:

- `python/drivedesk_public_demo_client.py`
- `javascript/drivedesk-public-demo-client.mjs`
- `typescript/drivedesk-public-demo-client.d.ts`

The clients target:

```text
GET /demo/public
operationId: public_demo_demo_public_get
```

Run the SDK smoke:

```bash
bash scripts/check_public_demo_sdk.sh
```

Engineering summary: this is the public-safe integration proof. DriveDesk
publishes an OpenAPI contract and generates a small SDK from it instead of
relying on hand-written request examples only.
