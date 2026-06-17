(function () {
  "use strict";

  var data = window.DRIVEDESK_DEMO_DATA;

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

  function statusTone(status) {
    if (["done", "ready", "online", "validated", "processed", "green", "active"].indexOf(status) >= 0) {
      return "green";
    }
    if (["blocked", "waiting", "pending"].indexOf(status) >= 0) {
      return "amber";
    }
    if (["high"].indexOf(status) >= 0) {
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

  function init() {
    document.getElementById("tenantName").textContent = data.tenant.name;
    document.getElementById("tenantMeta").textContent = data.tenant.plan + " - " + data.tenant.status;
    document.getElementById("apiStatus").textContent = "API " + data.health.api;
    document.getElementById("workerStatus").textContent = "Worker " + data.health.worker;
    fillMetricGrid();
    fillWorkQueue();
    fillIntegrations();
    fillMembers();
    fillAudit();
    fillOutbox();
    fillHealth();
    setupTabs();
  }

  init();
})();

