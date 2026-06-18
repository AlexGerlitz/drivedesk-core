(function () {
  "use strict";

  var fallbackData = window.DRIVEDESK_DEMO_DATA;
  var data = fallbackData;

  function text(value) {
    return document.createTextNode(String(value));
  }

  function clear(element) {
    while (element.firstChild) {
      element.removeChild(element.firstChild);
    }
  }

  function chip(label, tone) {
    var node = document.createElement("span");
    node.className = "chip";
    node.dataset.tone = tone || "blue";
    node.appendChild(text(label));
    return node;
  }

  function demoApiUrl() {
    var params = new URLSearchParams(window.location.search);
    var explicitUrl = params.get("demoApi");
    if (explicitUrl) {
      return explicitUrl;
    }
    if (params.get("api") === "1") {
      return document.body.dataset.demoApiPath || "/demo/public";
    }
    if (window.DRIVEDESK_DEMO_API_URL) {
      return window.DRIVEDESK_DEMO_API_URL;
    }
    return "";
  }

  function isValidDemoPayload(payload) {
    return Boolean(
      payload &&
        payload.schemaVersion === 1 &&
        payload.tenant &&
        Array.isArray(payload.metrics) &&
        Array.isArray(payload.workQueue) &&
        payload.workflow &&
        Array.isArray(payload.workflow.stages) &&
        Array.isArray(payload.timeline) &&
        Array.isArray(payload.domainEvents) &&
        Array.isArray(payload.integrationJobs) &&
        Array.isArray(payload.integrationHealth) &&
        Array.isArray(payload.recoveryEvidence) &&
        payload.engineeringProof &&
        Array.isArray(payload.engineeringProof.summary) &&
        Array.isArray(payload.engineeringProof.gates) &&
        Array.isArray(payload.engineeringProof.evidence)
    );
  }

  async function loadApiBackedDemoData() {
    var url = demoApiUrl();
    if (!url || !window.fetch) {
      return fallbackData;
    }

    try {
      var response = await window.fetch(url, {
        cache: "no-store",
        headers: {
          Accept: "application/json",
        },
      });
      if (!response.ok) {
        return fallbackData;
      }
      var payload = await response.json();
      return isValidDemoPayload(payload) ? payload : fallbackData;
    } catch (error) {
      return fallbackData;
    }
  }

  function fillMetricGrid() {
    var grid = document.getElementById("metricGrid");
    clear(grid);
    data.metrics.forEach(function (metric) {
      var card = document.createElement("article");
      card.className = "metric-card";
      card.dataset.tone = metric.tone;

      var label = document.createElement("span");
      label.className = "muted";
      label.appendChild(text(metric.label));

      var value = document.createElement("strong");
      value.appendChild(text(metric.value));

      var detail = document.createElement("span");
      detail.className = "muted";
      detail.appendChild(text(metric.detail));

      card.append(label, value, detail);
      grid.appendChild(card);
    });
  }

  function fillWorkQueue() {
    var rows = document.getElementById("workQueueRows");
    clear(rows);
    data.workQueue.forEach(function (task) {
      var row = document.createElement("tr");
      [task.title, task.owner].forEach(function (value) {
        var cell = document.createElement("td");
        cell.appendChild(text(value));
        row.appendChild(cell);
      });

      var statusCell = document.createElement("td");
      statusCell.appendChild(chip(task.status, statusTone(task.status)));
      row.appendChild(statusCell);

      var priorityCell = document.createElement("td");
      priorityCell.appendChild(chip(task.priority, priorityTone(task.priority)));
      row.appendChild(priorityCell);

      rows.appendChild(row);
    });
  }

  function fillIntegrations() {
    var rows = document.getElementById("integrationRows");
    clear(rows);
    data.integrationReadiness.forEach(function (item) {
      var row = document.createElement("article");
      row.className = "progress-row";

      var top = document.createElement("div");
      top.className = "progress-top";

      var name = document.createElement("strong");
      name.appendChild(text(item.name));
      top.appendChild(name);
      top.appendChild(chip(item.state, statusTone(item.state)));

      var bar = document.createElement("div");
      bar.className = "progress-bar";
      var fill = document.createElement("span");
      fill.style.setProperty("--progress", item.progress + "%");
      bar.appendChild(fill);

      row.append(top, bar);
      rows.appendChild(row);
    });
  }

  function fillAdapterContracts() {
    var rows = document.getElementById("adapterRows");
    clear(rows);
    data.adapters.forEach(function (adapter) {
      var row = document.createElement("article");
      row.className = "adapter-row";

      var top = document.createElement("div");
      top.className = "adapter-top";
      var name = document.createElement("strong");
      name.appendChild(text(adapter.name));
      top.append(name, chip(adapter.status, statusTone(adapter.status)));

      var key = document.createElement("code");
      key.appendChild(text(adapter.key));

      var contract = document.createElement("p");
      contract.className = "muted";
      contract.appendChild(text(adapter.contract));

      var meta = document.createElement("span");
      meta.className = "muted";
      meta.appendChild(
        text(
          (adapter.direction || "adapter") +
            " · " +
            (adapter.connectionProfileSupported ? "connection profile supported" : "no connection profile")
        )
      );

      var mapping = document.createElement("span");
      mapping.className = "muted";
      var requiredMappingKeys = adapter.requiredMappingKeys || [];
      mapping.appendChild(
        text(requiredMappingKeys.length ? "mapping: " + requiredMappingKeys.join(", ") : "mapping: none")
      );

      var scopes = document.createElement("span");
      scopes.className = "muted";
      var supportedScopes = adapter.supportedConnectionScopes || [];
      scopes.appendChild(text(supportedScopes.length ? "scopes: " + supportedScopes.join(", ") : "scopes: none"));

      var operations = document.createElement("span");
      operations.className = "muted";
      var operationContracts = adapter.operationContracts || [];
      operations.appendChild(
        text(
          operationContracts.length
            ? "operations: " + operationContracts.map(function (operation) { return operation.key; }).join(", ")
            : "operations: none"
        )
      );

      row.append(top, key, contract, meta, mapping, scopes, operations);
      rows.appendChild(row);
    });
  }

  function fillSyncJobs() {
    var rows = document.getElementById("syncJobRows");
    clear(rows);
    data.integrationJobs.forEach(function (job) {
      var row = document.createElement("article");
      row.className = "event-row";

      var top = document.createElement("div");
      top.className = "event-top";
      var name = document.createElement("strong");
      name.appendChild(text(job.event));
      top.append(name, chip(job.status, statusTone(job.status)));

      var detail = document.createElement("span");
      detail.className = "muted";
      detail.appendChild(
        text(job.adapter + " - attempts " + job.attempts + " - " + job.summary)
      );

      row.append(top, detail);
      rows.appendChild(row);
    });
  }

  function fillIntegrationHealth() {
    var rows = document.getElementById("integrationHealthRows");
    clear(rows);
    data.integrationHealth.forEach(function (item) {
      var row = document.createElement("article");
      row.className = "integration-health-card";

      var top = document.createElement("div");
      top.className = "integration-health-top";

      var label = document.createElement("span");
      label.className = "muted";
      label.appendChild(text(item.label));
      top.append(label, chip(item.state, statusTone(item.state)));

      var value = document.createElement("strong");
      value.appendChild(text(item.value));

      var detail = document.createElement("span");
      detail.className = "muted";
      detail.appendChild(text(item.detail));

      var metric = document.createElement("code");
      metric.appendChild(text(item.metric));

      row.append(top, value, detail, metric);
      rows.appendChild(row);
    });
  }

  function fillMembers() {
    var rows = document.getElementById("memberRows");
    clear(rows);
    data.members.forEach(function (member) {
      var row = document.createElement("article");
      row.className = "member-row";

      var top = document.createElement("div");
      top.className = "member-top";

      var identity = document.createElement("div");
      var name = document.createElement("strong");
      name.appendChild(text(member.name));
      var email = document.createElement("div");
      email.className = "muted";
      email.appendChild(text(member.email));
      identity.append(name, email);

      top.append(identity, chip(member.role, "blue"));
      row.append(top);
      rows.appendChild(row);
    });
  }

  function fillWorkflow() {
    var meta = document.getElementById("workflowMeta");
    meta.textContent = data.workflow.owner + " - " + data.workflow.currentStage;

    var rows = document.getElementById("workflowStageRows");
    clear(rows);
    data.workflow.stages.forEach(function (stage) {
      var row = document.createElement("article");
      row.className = "workflow-stage-card";
      row.dataset.state = stage.state;

      var top = document.createElement("div");
      top.className = "workflow-stage-top";

      var label = document.createElement("strong");
      label.appendChild(text(stage.label));
      top.append(label, chip(stage.state, statusTone(stage.state)));

      var owner = document.createElement("span");
      owner.className = "muted";
      owner.appendChild(text(stage.owner));

      var evidence = document.createElement("code");
      evidence.appendChild(text(stage.evidence));

      row.append(top, owner, evidence);
      rows.appendChild(row);
    });
  }

  function fillWorkflowTimeline() {
    var rows = document.getElementById("workflowTimelineRows");
    clear(rows);
    data.timeline.forEach(function (event) {
      var row = document.createElement("li");
      var time = document.createElement("time");
      time.appendChild(text(event.time + " " + event.actor));
      var title = document.createElement("strong");
      title.appendChild(text(event.title));
      var detail = document.createElement("span");
      detail.className = "muted";
      detail.appendChild(text(event.detail));
      var code = document.createElement("code");
      code.appendChild(text(event.event));
      row.append(time, title, detail, code);
      rows.appendChild(row);
    });
  }

  function fillDomainEvents() {
    var rows = document.getElementById("domainEventRows");
    clear(rows);
    data.domainEvents.forEach(function (event) {
      var row = document.createElement("article");
      row.className = "event-row";

      var top = document.createElement("div");
      top.className = "event-top";
      var name = document.createElement("strong");
      name.appendChild(text(event.event));
      top.append(name, chip(event.status, statusTone(event.status)));

      var detail = document.createElement("span");
      detail.className = "muted";
      detail.appendChild(text(event.producer + " -> " + event.consumer));

      row.append(top, detail);
      rows.appendChild(row);
    });
  }

  function fillAudit() {
    var rows = document.getElementById("auditRows");
    clear(rows);
    data.auditEvents.forEach(function (event) {
      var row = document.createElement("li");
      var time = document.createElement("time");
      time.appendChild(text(event.time + " " + event.actor));
      var title = document.createElement("strong");
      title.appendChild(text(event.event));
      var summary = document.createElement("span");
      summary.className = "muted";
      summary.appendChild(text(event.summary));
      row.append(time, title, summary);
      rows.appendChild(row);
    });
  }

  function fillOutbox() {
    var rows = document.getElementById("outboxRows");
    clear(rows);
    data.outbox.forEach(function (event) {
      var row = document.createElement("article");
      row.className = "event-row";

      var top = document.createElement("div");
      top.className = "event-top";
      var name = document.createElement("strong");
      name.appendChild(text(event.event));
      top.append(name, chip(event.status, statusTone(event.status)));

      var attempts = document.createElement("span");
      attempts.className = "muted";
      attempts.appendChild(text("Attempts: " + event.attempts));

      row.append(top, attempts);
      rows.appendChild(row);
    });
  }

  function fillHealth() {
    var rows = document.getElementById("healthRows");
    clear(rows);
    Object.keys(data.health).forEach(function (key) {
      var row = document.createElement("article");
      row.className = "health-card";

      var top = document.createElement("div");
      top.className = "health-top";

      var label = document.createElement("strong");
      label.appendChild(text(key));
      top.append(label, chip(data.health[key], statusTone(data.health[key])));

      row.appendChild(top);
      rows.appendChild(row);
    });
  }

  function fillRecoveryEvidence() {
    var rows = document.getElementById("recoveryRows");
    clear(rows);
    data.recoveryEvidence.forEach(function (item) {
      var row = document.createElement("article");
      row.className = "event-row";

      var top = document.createElement("div");
      top.className = "event-top";
      var name = document.createElement("strong");
      name.appendChild(text(item.name));
      top.append(name, chip(item.state, statusTone(item.state)));

      var detail = document.createElement("span");
      detail.className = "muted";
      detail.appendChild(text(item.detail));

      var evidence = document.createElement("code");
      evidence.appendChild(text(item.evidence));

      row.append(top, detail, evidence);
      rows.appendChild(row);
    });
  }

  function fillEngineeringProof() {
    var proof = data.engineeringProof;
    var meta = document.getElementById("proofMeta");
    meta.textContent = proof.milestone + " - " + proof.status + " - " + proof.updatedAt;

    var summaryRows = document.getElementById("proofSummaryRows");
    clear(summaryRows);
    proof.summary.forEach(function (item) {
      var card = document.createElement("article");
      card.className = "metric-card";
      card.dataset.tone = item.tone || "blue";

      var label = document.createElement("span");
      label.className = "muted";
      label.appendChild(text(item.label));

      var value = document.createElement("strong");
      value.appendChild(text(item.value));

      var detail = document.createElement("span");
      detail.className = "muted";
      detail.appendChild(text(item.detail));

      card.append(label, value, detail);
      summaryRows.appendChild(card);
    });

    var gateRows = document.getElementById("proofGateRows");
    clear(gateRows);
    proof.gates.forEach(function (gate) {
      var row = document.createElement("article");
      row.className = "event-row";

      var top = document.createElement("div");
      top.className = "event-top";
      var name = document.createElement("strong");
      name.appendChild(text(gate.name));
      top.append(name, chip(gate.status, statusTone(gate.status)));

      var command = document.createElement("code");
      command.appendChild(text(gate.command));

      var evidence = document.createElement("span");
      evidence.className = "muted";
      evidence.appendChild(text(gate.evidence));

      row.append(top, command, evidence);
      gateRows.appendChild(row);
    });

    var evidenceRows = document.getElementById("proofEvidenceRows");
    clear(evidenceRows);
    proof.evidence.forEach(function (item) {
      var row = document.createElement("article");
      row.className = "event-row";

      var top = document.createElement("div");
      top.className = "event-top";
      var title = document.createElement("strong");
      title.appendChild(text(item.title));
      top.append(title, chip(item.kind, "blue"));

      var path = document.createElement("code");
      path.appendChild(text(item.path));

      var summary = document.createElement("span");
      summary.className = "muted";
      summary.appendChild(text(item.summary));

      row.append(top, path, summary);
      evidenceRows.appendChild(row);
    });
  }

  function statusTone(status) {
    if (
      ["done", "ready", "online", "validated", "processed", "green", "active", "success", "observed", "matched", "resolved", "passed"].indexOf(status) >= 0
    ) {
      return "green";
    }
    if (["blocked", "waiting", "pending", "retry", "partial_success", "current", "open", "acknowledged"].indexOf(status) >= 0) {
      return "amber";
    }
    if (["high", "dead_letter"].indexOf(status) >= 0) {
      return "red";
    }
    return "blue";
  }

  function priorityTone(priority) {
    if (priority === "high") {
      return "red";
    }
    if (priority === "medium") {
      return "amber";
    }
    return "blue";
  }

  function setupTabs() {
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".nav-tab"));
    var views = Array.prototype.slice.call(document.querySelectorAll(".view"));

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var target = tab.dataset.view;
        tabs.forEach(function (item) {
          item.classList.toggle("is-active", item === tab);
        });
        views.forEach(function (view) {
          view.classList.toggle("is-visible", view.id === "view-" + target);
        });
      });
    });
  }

  function render() {
    document.getElementById("tenantName").textContent = data.tenant.name;
    document.getElementById("tenantMeta").textContent = data.tenant.plan + " - " + data.tenant.status;
    document.getElementById("apiStatus").textContent = "API " + data.health.api;
    document.getElementById("workerStatus").textContent = "Worker " + data.health.worker;
    fillMetricGrid();
    fillWorkQueue();
    fillWorkflow();
    fillWorkflowTimeline();
    fillDomainEvents();
    fillIntegrations();
    fillAdapterContracts();
    fillSyncJobs();
    fillIntegrationHealth();
    fillMembers();
    fillAudit();
    fillOutbox();
    fillHealth();
    fillRecoveryEvidence();
    fillEngineeringProof();
  }

  async function init() {
    data = await loadApiBackedDemoData();
    render();
    setupTabs();
  }

  init();
})();
