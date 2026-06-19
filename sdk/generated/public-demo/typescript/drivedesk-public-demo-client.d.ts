// Generated from DriveDesk Core OpenAPI. Do not edit by hand.
export const PUBLIC_DEMO_PATH: "/demo/public";
export const CONNECTOR_REPLAY_PATH: "/demo/connector-fixture-replay";
export const OPERATION_ID: "public_demo_demo_public_get";
export const CONNECTOR_REPLAY_OPERATION_ID: "connector_fixture_replay_demo_demo_connector_fixture_replay_get";
export const REQUIRED_FIELDS: Array<"schemaVersion" | "generatedAt" | "dataSource" | "apiContract" | "tenant" | "health" | "metrics" | "workQueue" | "members" | "auditEvents" | "outbox" | "adapters" | "adapterScenarios" | "adapterStudio" | "connectorFixtureReplay" | "integrationJobs" | "integrationHealth" | "integrationReadiness" | "recoveryEvidence" | "alertRouting" | "incidentResponse" | "businessControlTower" | "engineeringProof" | "workflow" | "workflowScenarios" | "endToEndScenario" | "timeline" | "domainEvents">;
export const CONNECTOR_REPLAY_REQUIRED_FIELDS: Array<"status" | "command" | "fixtureFile" | "evidenceFile" | "summary" | "outcomes" | "boundaries" | "docs">;

export type AdapterScenarioPhase = "preview" | "execute" | "retry" | "operator_review";

export interface AdapterScenario {
  id: string;
  title: string;
  adapter: "file.import.fake" | "crm.bitrix24.mock" | "accounting.export.mock" | string;
  operation: string;
  phase: AdapterScenarioPhase;
  endpoint: string;
  requiredScope: string;
  status: string;
  detail: string;
  inputs: string[];
  outputs: string[];
  evidence: string;
}

export interface AdapterOperationPlan {
  scenarioId: string;
  adapter: string;
  operation: string;
  phase: AdapterScenarioPhase;
  executionMode: "contract_only";
  safeToRunAgainstPublicDemo: false;
  request: {
    method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "WORKER";
    path: string;
    headers: Record<string, string>;
    body: Record<string, unknown> | null;
  };
  expectedResponse: {
    status: string;
    outputs: string[];
    evidence: string;
    sideEffects: string[];
  };
}

export interface ConnectorFixtureReplayPayload {
  status: "validated";
  command: string;
  fixtureFile: string;
  evidenceFile: string;
  summary: Array<Record<string, unknown>>;
  outcomes: Array<{
    group: string;
    stage: string;
    status: string;
    detail: string;
    evidence: string;
  }>;
  boundaries: Array<Record<string, unknown>>;
  docs: Array<Record<string, string>>;
}

export interface PublicDemoPayload {
  schemaVersion: 1;
  generatedAt: string;
  dataSource: "api.synthetic";
  apiContract: Record<string, string>;
  tenant: Record<string, string>;
  health: Record<string, string>;
  metrics: Array<Record<string, unknown>>;
  workQueue: Array<Record<string, unknown>>;
  members: Array<Record<string, string>>;
  auditEvents: Array<Record<string, string>>;
  outbox: Array<Record<string, unknown>>;
  adapters: Array<Record<string, string>>;
  adapterScenarios: AdapterScenario[];
  adapterStudio: Record<string, unknown>;
  connectorFixtureReplay: ConnectorFixtureReplayPayload;
  integrationJobs: Array<Record<string, unknown>>;
  integrationHealth: Array<Record<string, string>>;
  integrationReadiness: Array<Record<string, unknown>>;
  recoveryEvidence: Array<Record<string, string>>;
  alertRouting: {
    summary: Array<Record<string, string>>;
    routes: Array<Record<string, string>>;
    bindings: Array<Record<string, string>>;
    runbookActions: Array<Record<string, string>>;
  };
  incidentResponse: {
    summary: Array<Record<string, string>>;
    incidents: Array<Record<string, string>>;
    timeline: Array<Record<string, string>>;
    recoveryActions: Array<Record<string, string>>;
    resolutionEvidence: Array<Record<string, string>>;
  };
  engineeringProof: {
    milestone: "engineering_70";
    status: "validated";
    updatedAt: string;
    summary: Array<Record<string, string>>;
    gates: Array<Record<string, string>>;
    evidence: Array<Record<string, string>>;
  };
  workflow: {
    id: "wf-demo-lead-to-student";
    currentStage: "student_sync";
    stages: Array<Record<string, string>>;
    [key: string]: unknown;
  };
  workflowScenarios: Array<{
    id: string;
    title: string;
    trigger: string;
    actionType: "emit_outbox_event" | "create_task_record" | "request_adapter_sync";
    owner: string;
    status: string;
    detail: string;
    outputs: string[];
    evidence: string;
  }>;
  timeline: Array<Record<string, string>>;
  domainEvents: Array<Record<string, string>>;
}

export class DriveDeskPublicDemoClient {
  constructor(baseUrl?: string, options?: { fetchImpl?: typeof fetch });
  getPublicDemo(): Promise<PublicDemoPayload>;
  getConnectorFixtureReplay(): Promise<ConnectorFixtureReplayPayload>;
  getAdapterOperationPlan(
    scenarioId: string,
    options?: { requestId?: string },
  ): Promise<AdapterOperationPlan>;
}

export function getAdapterScenario(payload: PublicDemoPayload, scenarioId: string): AdapterScenario;
export function buildAdapterOperationPlan(
  payload: PublicDemoPayload,
  scenarioId: string,
  options?: { requestId?: string },
): AdapterOperationPlan;
export function validatePublicDemoPayload(payload: PublicDemoPayload): void;
export function validateConnectorFixtureReplayPayload(payload: ConnectorFixtureReplayPayload): void;
