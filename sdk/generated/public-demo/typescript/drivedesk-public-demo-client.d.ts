// Generated from DriveDesk Core OpenAPI. Do not edit by hand.
export const PUBLIC_DEMO_PATH: "/demo/public";
export const CONNECTOR_REPLAY_PATH: "/demo/connector-fixture-replay";
export const CONNECTOR_CERTIFICATION_PATH: "/demo/connector-certification";
export const PROVIDER_ONBOARDING_PATH: "/demo/provider-onboarding";
export const INTEGRATION_REPAIR_PATH: "/demo/integration-repair";
export const BUSINESS_SCENARIO_REPLAY_PATH: "/demo/business-scenario-replay";
export const OPERATION_ID: "public_demo_demo_public_get";
export const CONNECTOR_REPLAY_OPERATION_ID: "connector_fixture_replay_demo_demo_connector_fixture_replay_get";
export const CONNECTOR_CERTIFICATION_OPERATION_ID: "connector_certification_demo_demo_connector_certification_get";
export const PROVIDER_ONBOARDING_OPERATION_ID: "provider_onboarding_demo_demo_provider_onboarding_get";
export const INTEGRATION_REPAIR_OPERATION_ID: "integration_repair_demo_demo_integration_repair_get";
export const BUSINESS_SCENARIO_REPLAY_OPERATION_ID: "business_scenario_replay_demo_demo_business_scenario_replay_get";
export const REQUIRED_FIELDS: Array<"schemaVersion" | "generatedAt" | "dataSource" | "apiContract" | "tenant" | "health" | "metrics" | "workQueue" | "members" | "auditEvents" | "outbox" | "adapters" | "adapterScenarios" | "adapterStudio" | "connectorCertification" | "providerOnboarding" | "integrationRuntime" | "integrationExecution" | "integrationRepair" | "connectorFixtureReplay" | "businessIntakePipeline" | "businessTaskHandoff" | "businessNotificationChannels" | "businessContextAssistant" | "businessActionExecution" | "businessApprovalGateway" | "integrationJobs" | "integrationHealth" | "integrationReadiness" | "recoveryEvidence" | "alertRouting" | "incidentResponse" | "businessControlTower" | "businessScenarioReplay" | "engineeringProof" | "workflow" | "workflowScenarios" | "endToEndScenario" | "timeline" | "domainEvents">;
export const CONNECTOR_REPLAY_REQUIRED_FIELDS: Array<"status" | "command" | "fixtureFile" | "evidenceFile" | "summary" | "outcomes" | "boundaries" | "docs">;
export const CONNECTOR_CERTIFICATION_REQUIRED_FIELDS: Array<"status" | "command" | "certificationLevel" | "adapterCount" | "privateReadyCount" | "summary" | "providerProfiles" | "certificationStages" | "certificationGates" | "implementationPath" | "dataBoundaries" | "api" | "docs">;
export const PROVIDER_ONBOARDING_REQUIRED_FIELDS: Array<"status" | "command" | "onboardingLevel" | "providerKey" | "providerName" | "providerCategory" | "summary" | "providerProfile" | "onboardingStages" | "mappingPreview" | "preflightChecks" | "sandboxContract" | "rolloutPlan" | "dataBoundaries" | "api" | "docs">;
export const INTEGRATION_REPAIR_REQUIRED_FIELDS: Array<"status" | "command" | "repairLevel" | "incidentCount" | "criticalCount" | "safeActionCount" | "summary" | "incidentMatrix" | "repairRunbooks" | "impactAnalysis" | "repairActions" | "safeExecutionPlan" | "dataBoundaries" | "api" | "docs">;
export const BUSINESS_SCENARIO_REPLAY_REQUIRED_FIELDS: Array<"status" | "command" | "summary" | "scenarios" | "flow" | "docs">;

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

export interface ConnectorCertificationPayload {
  status: "validated";
  command: string;
  certificationLevel: "public_contract_certified";
  adapterCount: number;
  privateReadyCount: number;
  summary: Array<Record<string, unknown>>;
  providerProfiles: Array<Record<string, unknown>>;
  certificationStages: Array<Record<string, unknown>>;
  certificationGates: Array<Record<string, unknown>>;
  implementationPath: Array<Record<string, unknown>>;
  dataBoundaries: Array<Record<string, unknown>>;
  api: Record<string, string>;
  docs: Array<Record<string, string>>;
}

export interface ProviderOnboardingPayload {
  status: "previewed";
  command: string;
  onboardingLevel: "sandbox_onboarding_ready";
  providerKey: string;
  providerName: string;
  providerCategory: string;
  summary: Array<Record<string, unknown>>;
  providerProfile: Record<string, unknown>;
  onboardingStages: Array<Record<string, unknown>>;
  mappingPreview: Record<string, unknown>;
  preflightChecks: Array<Record<string, unknown>>;
  sandboxContract: Record<string, unknown>;
  rolloutPlan: Array<Record<string, unknown>>;
  dataBoundaries: Array<Record<string, unknown>>;
  api: Record<string, string>;
  docs: Array<Record<string, string>>;
}

export interface IntegrationRepairPayload {
  status: "previewed";
  command: string;
  repairLevel: "operator_repair_ready";
  incidentCount: 3;
  criticalCount: 2;
  safeActionCount: 1;
  summary: Array<Record<string, unknown>>;
  incidentMatrix: Array<Record<string, unknown>>;
  repairRunbooks: Array<Record<string, unknown>>;
  impactAnalysis: Array<Record<string, unknown>>;
  repairActions: Array<Record<string, unknown>>;
  safeExecutionPlan: Array<Record<string, unknown>>;
  dataBoundaries: Array<Record<string, unknown>>;
  api: Record<string, string>;
  docs: Array<Record<string, string>>;
}

export interface BusinessScenarioReplayPayload {
  status: "validated";
  command: string;
  summary: Array<Record<string, unknown>>;
  scenarios: Array<{
    id: string;
    title: string;
    status: string;
    riskLevel: string;
    operatorRole: string;
    trigger: string;
    decision: string;
    sourceSystems: string[];
    normalizedFacts: Array<Record<string, string>>;
    recommendedActions: Array<Record<string, string>>;
    automationCandidates: Array<Record<string, unknown>>;
    evidence: string[];
    dataBoundary: string[];
  }>;
  flow: Array<Record<string, string>>;
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
  connectorCertification: ConnectorCertificationPayload;
  providerOnboarding: ProviderOnboardingPayload;
  integrationRepair: IntegrationRepairPayload;
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
  businessScenarioReplay: BusinessScenarioReplayPayload;
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
  getConnectorCertification(): Promise<ConnectorCertificationPayload>;
  getProviderOnboarding(): Promise<ProviderOnboardingPayload>;
  getIntegrationRepair(): Promise<IntegrationRepairPayload>;
  getBusinessScenarioReplay(): Promise<BusinessScenarioReplayPayload>;
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
export function validateConnectorCertificationPayload(payload: ConnectorCertificationPayload): void;
export function validateProviderOnboardingPayload(payload: ProviderOnboardingPayload): void;
export function validateIntegrationRepairPayload(payload: IntegrationRepairPayload): void;
export function validateBusinessScenarioReplayPayload(payload: BusinessScenarioReplayPayload): void;
