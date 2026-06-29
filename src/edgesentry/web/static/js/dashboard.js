// Polls recent events + LLM health for the dashboard.
(function () {
  const tbody = document.querySelector("#events tbody");
  const status = document.getElementById("llm-status");

  async function refreshEvents() {
    try {
      const res = await fetch("/api/events?limit=25");
      const rows = await res.json();
      tbody.innerHTML = "";
      for (const r of rows) {
        const tr = document.createElement("tr");
        const t = new Date(r.ts).toLocaleTimeString();
        tr.innerHTML =
          `<td>${t}</td><td>${r.person_id || "—"}</td>` +
          `<td>${r.zone || "—"}</td><td>${r.kind}</td>`;
        tbody.appendChild(tr);
      }
    } catch (_) {
      /* keep last good table on transient errors */
    }
  }

  async function refreshHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      status.textContent = data.llm_ok ? "LLM online" : "LLM offline";
      status.className = "status " + (data.llm_ok ? "ok" : "bad");
    } catch (_) {
      status.textContent = "LLM offline";
      status.className = "status bad";
    }
  }

  refreshEvents();
  refreshHealth();
  setInterval(refreshEvents, 5000);
  setInterval(refreshHealth, 15000);
})();
