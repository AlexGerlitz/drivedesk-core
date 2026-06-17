#!/usr/bin/env node
import { pathToFileURL } from "node:url";

export const PUBLIC_DEMO_PATH = "/demo/public";
export const OPERATION_ID = "public_demo_demo_public_get";
export const REQUIRED_FIELDS = [
  "schemaVersion",
  "generatedAt",
  "dataSource",
  "apiContract",
  "tenant",
  "health",
  "metrics",
  "workQueue",
  "members",
  "auditEvents",
  "outbox",
  "adapters",
  "integrationJobs",
  "integrationHealth",
  "integrationReadiness",
  "workflow",
  "timeline",
  "domainEvents"
];

export class DriveDeskPublicDemoClient {
  constructor(baseUrl = "http://localhost:8080", options = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = options.fetchImpl || globalThis.fetch;
    if (!this.fetchImpl) {
      throw new Error("fetch is not available in this JavaScript runtime");
    }
  }

  async getPublicDemo() {
    const response = await this.fetchImpl(`${this.baseUrl}${PUBLIC_DEMO_PATH}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`GET ${PUBLIC_DEMO_PATH} failed: ${response.status}`);
    }

    const payload = await response.json();
    validatePublicDemoPayload(payload);
    return payload;
  }
}

export function validatePublicDemoPayload(payload) {
  const missing = REQUIRED_FIELDS.filter((field) => !(field in payload));
  if (missing.length > 0) {
    throw new Error(`missing required fields: ${missing.join(", ")}`);
  }

  if (payload.schemaVersion !== 1) {
    throw new Error(`unexpected schemaVersion: ${payload.schemaVersion}`);
  }

  if (payload.dataSource !== "api.synthetic") {
    throw new Error(`unexpected dataSource: ${payload.dataSource}`);
  }

  if (payload.apiContract?.path !== PUBLIC_DEMO_PATH) {
    throw new Error(`unexpected apiContract.path: ${payload.apiContract?.path}`);
  }

  if (payload.tenant?.slug !== "demo-academy") {
    throw new Error(`unexpected tenant.slug: ${payload.tenant?.slug}`);
  }

  if (payload.workflow?.id !== "wf-demo-lead-to-student") {
    throw new Error(`unexpected workflow.id: ${payload.workflow?.id}`);
  }

  if (payload.workflow?.currentStage !== "student_sync") {
    throw new Error(`unexpected workflow.currentStage: ${payload.workflow?.currentStage}`);
  }

  if (!Array.isArray(payload.workflow?.stages) || payload.workflow.stages.length < 5) {
    throw new Error("workflow.stages is missing or too short");
  }

  if (!Array.isArray(payload.domainEvents)) {
    throw new Error("domainEvents is missing");
  }

  const eventNames = new Set(payload.domainEvents.map((event) => event?.event));
  for (const requiredEvent of ["lead.created", "student.created", "contract.generated", "student.sync.requested"]) {
    if (!eventNames.has(requiredEvent)) {
      throw new Error(`domainEvents does not include required event: ${requiredEvent}`);
    }
  }
}

async function main() {
  const baseUrlIndex = process.argv.indexOf("--base-url");
  const baseUrl =
    baseUrlIndex >= 0 && process.argv[baseUrlIndex + 1]
      ? process.argv[baseUrlIndex + 1]
      : process.env.BASE_URL || "http://localhost:8080";
  const client = new DriveDeskPublicDemoClient(baseUrl);
  const payload = await client.getPublicDemo();
  console.log(
    "generated js SDK ok:",
    payload.tenant.slug,
    payload.dataSource,
    `workflow=${payload.workflow.currentStage}`,
    `operation=${OPERATION_ID}`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
