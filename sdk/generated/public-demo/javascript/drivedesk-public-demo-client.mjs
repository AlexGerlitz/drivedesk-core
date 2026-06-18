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
  "recoveryEvidence",
  "alertRouting",
  "incidentResponse",
  "engineeringProof",
  "workflow",
  "workflowScenarios",
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

  if (!Array.isArray(payload.workflowScenarios) || payload.workflowScenarios.length < 3) {
    throw new Error("workflowScenarios is missing or too short");
  }

  const scenarioIds = new Set(payload.workflowScenarios.map((scenario) => scenario?.id));
  for (const requiredScenario of ["scenario-contract-approval-sync", "scenario-signature-task", "scenario-accounting-export"]) {
    if (!scenarioIds.has(requiredScenario)) {
      throw new Error(`workflowScenarios does not include required scenario: ${requiredScenario}`);
    }
  }

  const actionTypes = new Set(payload.workflowScenarios.map((scenario) => scenario?.actionType));
  for (const requiredAction of ["emit_outbox_event", "create_task_record", "request_adapter_sync"]) {
    if (!actionTypes.has(requiredAction)) {
      throw new Error(`workflowScenarios does not include required action: ${requiredAction}`);
    }
  }

  const scenarioOutputs = new Set(payload.workflowScenarios.flatMap((scenario) => scenario?.outputs || []));
  for (const requiredOutput of ["audit_event", "outbox_event", "task_record", "integration_job", "action_run"]) {
    if (!scenarioOutputs.has(requiredOutput)) {
      throw new Error(`workflowScenarios does not include required output: ${requiredOutput}`);
    }
  }

  if (payload.engineeringProof?.milestone !== "engineering_70") {
    throw new Error(`unexpected engineeringProof.milestone: ${payload.engineeringProof?.milestone}`);
  }

  if (!Array.isArray(payload.engineeringProof?.gates) || payload.engineeringProof.gates.length < 5) {
    throw new Error("engineeringProof.gates is missing or too short");
  }

  if (!Array.isArray(payload.alertRouting?.routes) || payload.alertRouting.routes.length < 3) {
    throw new Error("alertRouting.routes is missing or too short");
  }

  if (!Array.isArray(payload.alertRouting?.bindings) || payload.alertRouting.bindings.length < 5) {
    throw new Error("alertRouting.bindings is missing or too short");
  }

  const alertNames = new Set(payload.alertRouting.bindings.map((binding) => binding?.alert));
  for (const requiredAlert of ["DriveDeskApiTargetDown", "DriveDeskIntegrationDeadLetters", "DriveDeskScheduledValidationMissed"]) {
    if (!alertNames.has(requiredAlert)) {
      throw new Error(`alertRouting.bindings does not include required alert: ${requiredAlert}`);
    }
  }

  if (!Array.isArray(payload.incidentResponse?.incidents) || payload.incidentResponse.incidents.length < 3) {
    throw new Error("incidentResponse.incidents is missing or too short");
  }

  const incidentStatuses = new Set(payload.incidentResponse.incidents.map((incident) => incident?.status));
  for (const requiredStatus of ["open", "acknowledged", "resolved"]) {
    if (!incidentStatuses.has(requiredStatus)) {
      throw new Error(`incidentResponse.incidents does not include required status: ${requiredStatus}`);
    }
  }

  if (!Array.isArray(payload.incidentResponse?.timeline) || payload.incidentResponse.timeline.length < 5) {
    throw new Error("incidentResponse.timeline is missing or too short");
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
