const API = "http://127.0.0.1:8000";

let inventory = [];
let profiles = {};
let activeSection = "dashboard";
let metricsHistory = [];
let evaluationDashboardData = null;

const titles = {
  dashboard: ["Dashboard", "Resumen general del sistema"],
  inventory: ["Inventario", "Gestión de productos"],
  chat: ["Chat bot", "Prueba del flujo principal"],
  history: ["Historial", "Mensajes procesados por el backend"],
  copilots: ["Copilotos", "Perfiles especializados del LLM"],
  metrics: ["Métricas", "Panel de observabilidad, rendimiento y costos"],
  evaluation: ["Evaluación", "Pruebas de intención, precisión y rendimiento"]
};

function $(id) {
  return document.getElementById(id);
}

function esc(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setDot(id, ok) {
  if ($(id)) {
    $(id).className = ok ? "dot ok" : "dot bad";
  }
}

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || data.message || "Error del backend");
  }

  return data;
}

function showSection(section) {
  activeSection = section;

  document.querySelectorAll(".section").forEach((el) => {
    el.classList.toggle("active", el.id === section);
  });

  if (section === "metrics") {
    loadMetricsDashboard();
  }

  if (section === "evaluation") {
    loadEvaluation();
  }

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.section === section);
  });

  $("pageTitle").textContent = titles[section][0];
  $("pageSubtitle").textContent = titles[section][1];

  if (section === "dashboard") loadDashboard();
  if (section === "inventory") loadInventory();
  if (section === "history") loadHistory();
}

async function checkStatus() {
  try {
    await fetchJSON(`${API}/health`);
    setDot("dotBackend", true);
  } catch {
    setDot("dotBackend", false);
  }

  try {
    const res = await fetch("http://localhost:11434/api/tags");
    setDot("dotOllama", res.ok);
  } catch {
    setDot("dotOllama", false);
  }

  try {
    await fetchJSON(`${API}/chat/health`);
    setDot("dotChat", true);
  } catch {
    setDot("dotChat", false);
  }
}

async function loadSystemHealth() {
  let backendOk = false;
  let chatOk = false;
  let ollamaOk = false;
  let sqliteOk = false;

  try {
    await fetchJSON(`${API}/health`);
    backendOk = true;
  } catch {
    backendOk = false;
  }

  try {
    await fetchJSON(`${API}/chat/health`);
    chatOk = true;
  } catch {
    chatOk = false;
  }

  try {
    const res = await fetch("http://localhost:11434/api/tags");
    ollamaOk = res.ok;
  } catch {
    ollamaOk = false;
  }

  try {
    await fetchJSON(`${API}/metrics/real-chat-analysis`);
    sqliteOk = true;
  } catch {
    sqliteOk = false;
  }

  setDot("healthBackendDot", backendOk);
  setDot("healthChatDot", chatOk);
  setDot("healthOllamaDot", ollamaOk);
  setDot("healthSQLiteDot", sqliteOk);

  $("healthBackendText").textContent = backendOk ? "Online" : "Sin conexión";
  $("healthChatText").textContent = chatOk ? "Disponible" : "No disponible";
  $("healthOllamaText").textContent = ollamaOk ? "Modelo local disponible" : "Ollama no responde";
  $("healthSQLiteText").textContent = sqliteOk ? "Operativo" : "No verificado";
}

async function loadDashboard() {
  await Promise.allSettled([
    loadInventory(false),
    loadHistory(false)
  ]);

  $("statProducts").textContent = inventory.length;

  $("statLowStock").textContent = inventory.filter((item) => {
    return Number(item.quantity) <= 2;
  }).length;

  $("dashInventory").innerHTML =
    inventory
      .slice(-6)
      .reverse()
      .map((item) => `
        <div class="mini-item">
          <div class="meta">${esc(item.source || "inventario")}</div>
          <strong>${esc(item.name)}</strong>
          <br>
          cantidad: ${esc(item.quantity)}
        </div>
      `)
      .join("") ||
    `<div class="mini-item">Inventario vacío</div>`;
}

async function loadInventory(render = true) {
  const data = await fetchJSON(`${API}/inventory/db`);
  inventory = data.inventory || [];

  if (render) {
    renderInventory();
  }
}

function renderInventory() {
  const query = $("inventorySearch").value.toLowerCase().trim();

  const filtered = inventory.filter((item) => {
    return item.name.toLowerCase().includes(query);
  });

  if (!filtered.length) {
    $("inventoryTable").innerHTML = `
      <tr>
        <td colspan="6">No hay productos para mostrar.</td>
      </tr>
    `;
    return;
  }

  $("inventoryTable").innerHTML = filtered.map((item) => {
    const qty = Number(item.quantity);

    const badge =
      qty <= 0
        ? `<span class="badge zero">Agotado</span>`
        : qty <= 2
          ? `<span class="badge low">Bajo</span>`
          : `<span class="badge ok">OK</span>`;

    return `
      <tr>
        <td><strong>${esc(item.name)}</strong></td>
        <td>${esc(item.quantity)}</td>
        <td>${esc(item.source || "—")}</td>
        <td>${esc(item.last_update || "—")}</td>
        <td>${badge}</td>
        <td>
          <button
            class="btn danger"
            onclick="removeProduct('${esc(item.name)}')"
          >
            Quitar
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

async function addProduct(event) {
  event.preventDefault();

  const nombre = $("productName").value.trim();
  const cantidad = Number($("productQuantity").value);
  const fuente = $("productSource").value;

  if (!nombre || cantidad <= 0) {
    return;
  }

  await fetchJSON(`${API}/inventory/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      nombre,
      cantidad,
      fuente
    })
  });

  $("productName").value = "";
  $("productQuantity").value = "1";

  await loadInventory();
  await loadDashboard();
}

async function removeProduct(nombre) {
  const cantidad = Number(
    prompt(`¿Cuántas unidades quieres quitar de "${nombre}"?`, "1")
  );

  if (!cantidad || cantidad <= 0) {
    return;
  }

  await fetchJSON(`${API}/inventory/remove`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      nombre,
      cantidad,
      fuente: "frontend"
    })
  });

  await loadInventory();
  await loadDashboard();
}

function addBubble(containerId, role, text, type = "bot") {
  const div = document.createElement("div");

  div.className = `bubble ${type}`;
  div.innerHTML = `
    <strong>${esc(role)}</strong>
    <br>
    ${esc(text)}
  `;

  $(containerId).appendChild(div);
  $(containerId).scrollTop = $(containerId).scrollHeight;
}

async function sendMainChat(event) {
  event.preventDefault();

  const mensaje = $("chatInput").value.trim();
  const numero = $("chatNumber").value.trim() || "demo_frontend";

  if (!mensaje) {
    return;
  }

  addBubble("chatWindow", "Tú", mensaje, "user");
  $("chatInput").value = "";

  try {
    const data = await fetchJSON(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        numero,
        mensaje
      })
    });

    addBubble("chatWindow", "Bot", data.respuesta, "bot");

    await loadInventory(false);
    await loadDashboard();

    if (activeSection === "metrics") {
      await loadMetricsDashboard();
    }
  } catch (error) {
    addBubble("chatWindow", "Error", error.message, "error");
  }
}

async function loadHistory(render = true) {
  const data = await fetchJSON(`${API}/chat/historial`);
  const mensajes = data.mensajes || [];

  $("statMessages").textContent = mensajes.length;

  $("dashHistory").innerHTML =
    mensajes
      .slice(-5)
      .reverse()
      .map((item) => `
        <div class="mini-item">
          <div class="meta">${esc(item.numero)}</div>
          <strong>Usuario:</strong> ${esc(item.mensaje)}
        </div>
      `)
      .join("") ||
    `<div class="mini-item">Sin mensajes todavía</div>`;

  if (!render) {
    return;
  }

  $("historyList").innerHTML =
    mensajes
      .slice()
      .reverse()
      .map((item) => `
        <div class="history-item">
          <div class="meta">${esc(item.numero)}</div>
          <p><strong>Usuario:</strong><br>${esc(item.mensaje)}</p>
          <p><strong>Bot:</strong><br>${esc(item.respuesta)}</p>
        </div>
      `)
      .join("") ||
    `<div class="history-item">No hay historial todavía.</div>`;
}

async function loadProfiles() {
  profiles = await fetchJSON(`${API}/profiles`);

  $("copilotProfile").innerHTML =
    Object
      .entries(profiles)
      .map(([id, profile]) => `
        <option value="${esc(id)}">
          ${esc(profile.label)}
        </option>
      `)
      .join("");

  applyProfile();
}

function applyProfile() {
  const id = $("copilotProfile").value;
  $("systemPrompt").value = profiles[id]?.system_prompt || "";
}

async function sendCopilot(event) {
  event.preventDefault();

  const message = $("copilotInput").value.trim();

  if (!message) {
    return;
  }

  addBubble("copilotWindow", "Tú", message, "user");
  $("copilotInput").value = "";

  const payload = {
    message,
    model: $("copilotModel").value,
    copilot_profile: $("copilotProfile").value,
    system_prompt: $("systemPrompt").value,
    temperature: Number($("temperature").value),
    top_p: Number($("topP").value),
    num_predict: Number($("numPredict").value),
    num_ctx: 4096,
    repeat_penalty: Number($("repeatPenalty").value)
  };

  try {
    const data = await fetchJSON(`${API}/chat/admin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    addBubble(
      "copilotWindow",
      `Copiloto — ${data.copilot_label}`,
      data.reply,
      "bot"
    );

    renderMetrics(data.metrics);
  } catch (error) {
    addBubble("copilotWindow", "Error", error.message, "error");
  }
}

function renderMetrics(metrics) {
  $("metricsPanel").classList.remove("hidden");

  $("metricsPanel").innerHTML = `
    <div class="metric">
      <span>Tiempo</span>
      <strong>${metrics.wall_time_s}s</strong>
    </div>
    <div class="metric">
      <span>Tokens/s</span>
      <strong>${metrics.tokens_per_second}</strong>
    </div>
    <div class="metric">
      <span>Entrada</span>
      <strong>${metrics.prompt_eval_count}</strong>
    </div>
    <div class="metric">
      <span>Salida</span>
      <strong>${metrics.eval_count}</strong>
    </div>
  `;
}

function bindEvents() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      showSection(btn.dataset.section);
    });
  });

  if ($("reloadMetricsBtn")) {
    $("reloadMetricsBtn").addEventListener("click", loadMetricsDashboard);
  }

  if ($("reloadHealthBtn")) {
    $("reloadHealthBtn").addEventListener("click", loadSystemHealth);
  }

  if ($("reloadEvaluationMatrixBtn")) {
    $("reloadEvaluationMatrixBtn").addEventListener(
      "click",
      loadEvaluationMatrix
    );
  }

  if ($("reloadEvaluationBtn")) {
    $("reloadEvaluationBtn").addEventListener("click", loadEvaluation);
  }

  if ($("runInventoryTestsBtn")) {
    $("runInventoryTestsBtn").addEventListener("click", runInventoryTests);
  }

  document.querySelectorAll(".preset").forEach((btn) => {
    btn.addEventListener("click", () => {
      $("chatInput").value = btn.dataset.msg;
    });
  });

  $("refreshBtn").addEventListener("click", refreshAll);
  $("reloadInventoryBtn").addEventListener("click", loadInventory);
  $("reloadHistoryBtn").addEventListener("click", loadHistory);
  $("inventorySearch").addEventListener("input", renderInventory);
  $("addInventoryForm").addEventListener("submit", addProduct);
  $("chatForm").addEventListener("submit", sendMainChat);
  $("copilotForm").addEventListener("submit", sendCopilot);
  $("copilotProfile").addEventListener("change", applyProfile);
}

async function refreshAll() {
  await checkStatus();
  await loadDashboard();

  if (activeSection === "inventory") {
    await loadInventory();
  }

  if (activeSection === "history") {
    await loadHistory();
  }

  if (activeSection === "metrics") {
    await loadMetricsDashboard();
  }

  if (activeSection === "evaluation") {
    await loadEvaluation();
  }
}

async function init() {
  bindEvents();

  await checkStatus();
  await loadProfiles();
  await loadDashboard();

  addBubble(
    "chatWindow",
    "Bot",
    "Hola. Puedes probar comandos como: dame el inventario, agrega productos, elimina productos, dame una receta o hazme un plan semanal.",
    "bot"
  );

  setInterval(checkStatus, 10000);
}

async function loadMetricsDashboard() {
  await Promise.allSettled([
    loadSystemHealth(),
    loadInventoryMetrics(),
    loadEvaluationMatrix()
  ]);
}

async function loadInventoryMetrics() {
  const summaryData = await fetchJSON(`${API}/metrics/inventory-summary`);
  const historyData = await fetchJSON(`${API}/metrics/real-chat-analysis`);

  const summary = summaryData.summary || {};
  metricsHistory = historyData.history || [];

  $("metricInventoryTotal").textContent =
    summary.total_queries ?? 0;

  $("metricInventoryAvg").textContent =
    summary.avg_latency
      ? Number(summary.avg_latency).toFixed(4)
      : "0";

  $("metricIntentPrecision").textContent =
    summary.intent_precision
      ? `${(Number(summary.intent_precision) * 100).toFixed(1)}%`
      : "0%";

  $("metricResponseRate").textContent =
    summary.response_rate
      ? `${(Number(summary.response_rate) * 100).toFixed(1)}%`
      : "0%";

  renderExecutionHistory();
  renderIntentChart();
  renderLatencyChart();
}

function getExecutionStatus(item) {
  const hasResponse = item.respuesta && item.respuesta.trim().length > 0;
  const isSuccess = Number(item.success) === 1;
  const isSlow = Number(item.latency_seconds || 0) > 20;
  const isGeneral = item.intent === "general";

  if (!isSuccess) {
    return {
      text: "Error backend",
      className: "badge zero"
    };
  }

  if (!hasResponse) {
    return {
      text: "Sin respuesta",
      className: "badge zero"
    };
  }

  if (isGeneral) {
    return {
      text: "Intent general",
      className: "badge zero"
    };
  }

  if (isSlow) {
    return {
      text: "Latencia alta",
      className: "badge low"
    };
  }

  return {
    text: "OK",
    className: "badge ok"
  };
}

function renderExecutionHistory() {
  $("inventoryMetricsTable").innerHTML =
    metricsHistory.map((item, index) => {
      const status = getExecutionStatus(item);

      return `
        <tr>
          <td>${esc(item.created_at || "—")}</td>
          <td>${esc(shortText(item.mensaje || "—", 80))}</td>
          <td>${esc(item.intent || "—")}</td>
          <td>${Number(item.latency_seconds || 0).toFixed(4)} s</td>
          <td><span class="${status.className}">${status.text}</span></td>
          <td>
            <button class="btn ghost" onclick="showMetricDetail(${index})">
              Ver detalle
            </button>
          </td>
        </tr>
      `;
    }).join("") ||
    `<tr><td colspan="6">No hay métricas reales todavía.</td></tr>`;
}

async function loadEvaluation() {
  const data = await fetchJSON(`${API}/metrics/intent-tests`);

  const summary = data.summary || {};
  const tests = data.tests || [];

  const total = summary.total_tests || 0;
  const accuracy = summary.accuracy || 0;
  const responseRate = summary.response_rate || 0;
  const avgLatency = summary.avg_latency || 0;

  $("evalTotalTests").textContent = total;
  $("evalAccuracy").textContent = `${(accuracy * 100).toFixed(1)}%`;
  $("evalResponseRate").textContent = `${(responseRate * 100).toFixed(1)}%`;
  $("evalAvgLatency").textContent = `${Number(avgLatency).toFixed(4)} s`;

  $("evaluationTable").innerHTML =
    tests.map((item) => {
      const isCorrect = Number(item.is_correct) === 1;
      const hasResponse = Number(item.has_response) === 1;

      const resultText = isCorrect && hasResponse
        ? "Correcto"
        : "Revisar";

      const resultClass = isCorrect && hasResponse
        ? "badge ok"
        : "badge zero";

      return `
        <tr>
          <td>${esc(item.message || "—")}</td>
          <td>${esc(item.expected_intent || "—")}</td>
          <td>${esc(item.detected_intent || "—")}</td>
          <td>${Number(item.latency_seconds || 0).toFixed(4)} s</td>
          <td>${esc(shortText(item.response || "", 140))}</td>
          <td><span class="${resultClass}">${resultText}</span></td>
        </tr>
      `;
    }).join("") ||
    `
      <tr>
        <td colspan="6">Todavía no hay pruebas registradas.</td>
      </tr>
    `;
}

async function runInventoryTests() {
  await fetchJSON(`${API}/metrics/run-inventory-tests`, {
    method: "POST"
  });

  await loadEvaluation();
  await loadEvaluationMatrix();
}

async function loadEvaluationMatrix() {
  const data = await fetchJSON(`${API}/metrics/evaluation-dashboard`);
  evaluationDashboardData = data;

  const quality = data.quality || {};
  const structured = data.structured_output || {};
  const architecture = data.architecture || {};
  const operation = data.operation || {};

  const accuracy = Number(quality.accuracy || 0) * 100;
  const precision = Number(quality.precision || 0) * 100;
  const recall = Number(quality.recall || 0) * 100;
  const f1 = Number(quality.f1_score || 0) * 100;

  const jsonValidity =
    Number(structured.json_validity_rate || 0) * 100;

  const schemaValidity =
    Number(structured.schema_valid_rate || 0) * 100;

  const architectureSuccess =
    Number(architecture.architecture_success_rate || 0) * 100;

  const avgLatency =
    Number(operation.chat?.avg_latency || 0);

  const totalTokens =
    Number(operation.llm?.total_tokens || 0);

  const promptTokens =
    Number(operation.llm?.prompt_tokens || 0);

  const completionTokens =
    Number(operation.llm?.completion_tokens || 0);

  const tokensPerSecond =
    Number(operation.llm?.avg_tokens_per_second || 0);

  const avgConfidence =
    Number(operation.orchestrator?.avg_confidence || 0) * 100;

  const modelName =
    metricsHistory.find((item) => item.orchestrator_model)?.orchestrator_model ||
    "llama3.2:3b";

  $("modelName").textContent = modelName;
  $("modelTokensTotal").textContent = totalTokens;
  $("modelConfidenceAvg").textContent = `${avgConfidence.toFixed(1)}%`;
  $("modelTokensPerSecond").textContent = tokensPerSecond.toFixed(2);

  $("evaluationMatrixTable").innerHTML = `
    <tr>
      <td>Calidad de decisión</td>
      <td>¿El orquestador clasificó correctamente la intención?</td>
      <td>Accuracy, precision, recall, F1-score</td>
      <td>
        Accuracy: ${accuracy.toFixed(1)}%<br>
        Precision: ${precision.toFixed(1)}%<br>
        Recall: ${recall.toFixed(1)}%<br>
        F1-score: ${f1.toFixed(1)}%
      </td>
    </tr>

    <tr>
      <td>Salida estructurada</td>
      <td>¿El LLM devolvió JSON válido y compatible con el esquema?</td>
      <td>JSON validity rate, schema valid rate</td>
      <td>
        JSON válido: ${jsonValidity.toFixed(1)}%<br>
        Schema válido: ${schemaValidity.toFixed(1)}%
      </td>
    </tr>

    <tr>
      <td>Arquitectura</td>
      <td>¿El backend ejecutó correctamente el flujo?</td>
      <td>Success rate, respuesta no vacía, error rate</td>
      <td>
        Solicitudes: ${architecture.total_requests || 0}<br>
        Éxito arquitectura: ${architectureSuccess.toFixed(1)}%
      </td>
    </tr>

    <tr>
      <td>Operación</td>
      <td>¿Cuánto tarda, cuántos tokens usa y cuánto costaría?</td>
      <td>Latencia, tokens, tokens/s, costo</td>
      <td>
        Latencia promedio: ${avgLatency.toFixed(4)} s<br>
        Prompt tokens: ${promptTokens}<br>
        Completion tokens: ${completionTokens}<br>
        Tokens totales: ${totalTokens}<br>
        Tokens/s promedio: ${tokensPerSecond.toFixed(2)}<br>
        Costo local Ollama: $0
      </td>
    </tr>
  `;

  renderTokenChart(promptTokens, completionTokens, totalTokens);
  renderCostChart(promptTokens, completionTokens);
}

function showMetricDetail(index) {
  const item = metricsHistory[index];

  if (!item) {
    return;
  }

  const jsonValid = Number(item.orchestrator_json_valid) === 1;
  const schemaValid = Number(item.orchestrator_schema_valid) === 1;
  const serviceName = getServiceName(item.intent);
  const status = getExecutionStatus(item);

  $("executionDetailPanel").classList.remove("hidden");

  $("executionDetailContent").innerHTML = `
    <div class="pipeline">
      <div class="pipeline-node">
        <span>1</span>
        <strong>Usuario</strong>
        <small>Mensaje recibido</small>
      </div>

      <div class="pipeline-arrow">→</div>

      <div class="pipeline-node">
        <span>2</span>
        <strong>Backend</strong>
        <small>FastAPI /chat</small>
      </div>

      <div class="pipeline-arrow">→</div>

      <div class="pipeline-node">
        <span>3</span>
        <strong>Orquestador</strong>
        <small>${esc(item.orchestrator_model || "—")}</small>
      </div>

      <div class="pipeline-arrow">→</div>

      <div class="pipeline-node">
        <span>4</span>
        <strong>Servicio</strong>
        <small>${esc(item.intent || "—")}</small>
      </div>

      <div class="pipeline-arrow">→</div>

      <div class="pipeline-node">
        <span>5</span>
        <strong>Respuesta</strong>
        <small>${status.text}</small>
      </div>
    </div>

    <div class="grid-2">
      <div class="mini-item">
        <div class="meta">Usuario</div>
        <p>${esc(item.mensaje || "—")}</p>
        <p><strong>Número:</strong> ${esc(item.numero || "—")}</p>
      </div>

      <div class="mini-item">
        <div class="meta">Backend</div>
        <p><strong>Fecha:</strong> ${esc(item.created_at || "—")}</p>
        <p><strong>Latencia total:</strong> ${Number(item.latency_seconds || 0).toFixed(4)} s</p>
        <p><strong>Resultado:</strong> <span class="${status.className}">${status.text}</span></p>
      </div>

      <div class="mini-item">
        <div class="meta">Orquestador LLM</div>
        <p><strong>Modelo:</strong> ${esc(item.orchestrator_model || "—")}</p>
        <p><strong>Intent LLM:</strong> ${esc(item.orchestrator_intent || "—")}</p>
        <p><strong>Confianza:</strong> ${Number(item.orchestrator_confidence || 0).toFixed(2)}</p>
        <p><strong>Tokens:</strong> ${esc(item.orchestrator_tokens || 0)}</p>
        <p><strong>JSON válido:</strong> ${jsonValid ? "Sí" : "No"}</p>
        <p><strong>Schema válido:</strong> ${schemaValid ? "Sí" : "No"}</p>
      </div>

      <div class="mini-item">
        <div class="meta">Servicio ejecutado</div>
        <p><strong>Servicio:</strong> ${esc(serviceName)}</p>
        <p><strong>Intent final:</strong> ${esc(item.intent || "—")}</p>
        <p><strong>Éxito:</strong> ${Number(item.success) === 1 ? "Sí" : "No"}</p>
        <p><strong>Error:</strong> ${esc(item.error || "—")}</p>
      </div>
    </div>

    <div class="mini-item" style="margin-top: 14px;">
      <div class="meta">Respuesta enviada al usuario</div>
      <p>${esc(item.respuesta || "—")}</p>
    </div>
  `;

  $("executionDetailPanel").scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}

function renderIntentChart() {
  const counts = {};

  metricsHistory.forEach((item) => {
    const intent = item.intent || "unknown";
    counts[intent] = (counts[intent] || 0) + 1;
  });

  renderBarList(
    "intentChart",
    Object.entries(counts).map(([label, value]) => ({
      label,
      value
    }))
  );
}

function renderLatencyChart() {
  const lastItems = metricsHistory.slice(0, 8).reverse();

  renderBarList(
    "latencyChart",
    lastItems.map((item, index) => ({
      label: `#${index + 1}`,
      value: Number(item.latency_seconds || 0),
      suffix: "s"
    }))
  );
}

function renderTokenChart(promptTokens, completionTokens, totalTokens) {
  renderBarList(
    "tokenChart",
    [
      { label: "Prompt", value: promptTokens },
      { label: "Completion", value: completionTokens },
      { label: "Total", value: totalTokens }
    ]
  );
}

function renderCostChart(promptTokens, completionTokens) {
  const costs = estimateCosts(promptTokens, completionTokens);

  renderBarList(
    "costChart",
    [
      { label: "Ollama local", value: 0, prefix: "$" },
      { label: "GPT-4o-mini", value: costs["gpt-4o-mini"], prefix: "$" },
      { label: "GPT-4o", value: costs["gpt-4o"], prefix: "$" },
      { label: "Claude 3.5", value: costs["claude-3-5-sonnet"], prefix: "$" },
      { label: "Gemini 1.5 Pro", value: costs["gemini-1.5-pro"], prefix: "$" }
    ],
    6
  );
}

function renderBarList(containerId, rows, decimals = 2) {
  const container = $(containerId);

  if (!container) return;

  if (!rows || !rows.length) {
    container.innerHTML = `<div class="empty-chart">Sin datos todavía.</div>`;
    return;
  }

  const maxValue = Math.max(...rows.map((row) => Number(row.value || 0)), 1);

  container.innerHTML = rows.map((row) => {
    const value = Number(row.value || 0);
    const width = Math.max(4, (value / maxValue) * 100);
    const prefix = row.prefix || "";
    const suffix = row.suffix || "";

    const displayValue = Number.isInteger(value)
      ? `${prefix}${value}${suffix}`
      : `${prefix}${value.toFixed(decimals)}${suffix}`;

    return `
      <div style="display:grid; gap:6px; margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; gap:12px; font-size:14px;">
          <span style="color:#6b7a72; font-weight:800;">${esc(row.label)}</span>
          <strong style="color:#1a7a4a;">${displayValue}</strong>
        </div>

        <div style="width:100%; height:12px; background:#edf8f1; border-radius:999px; overflow:hidden;">
          <div style="height:100%; width:${width}%; background:#1a7a4a; border-radius:999px;"></div>
        </div>
      </div>
    `;
  }).join("");
}

function estimateCosts(promptTokens, completionTokens) {
  const prompt = Number(promptTokens || 0) / 1_000_000;
  const completion = Number(completionTokens || 0) / 1_000_000;

  return {
    "gpt-4o-mini": prompt * 0.15 + completion * 0.60,
    "gpt-4o": prompt * 5.00 + completion * 15.00,
    "claude-3-5-sonnet": prompt * 3.00 + completion * 15.00,
    "gemini-1.5-pro": prompt * 3.50 + completion * 10.50
  };
}

function getServiceName(intent) {
  const services = {
    inventory: "InventoryService.handle_inventory()",
    add_inventory: "InventoryService.add_food()",
    remove_inventory: "InventoryService.remove_food()",
    rename_inventory: "InventoryService.rename_food()",
    recipe: "RecipeService.generate_recipe()",
    shopping: "ShoppingService.generate_shopping_list()",
    meal_plan: "MealPlanService.generate_text_meal_plan()",
    nutrition: "NutritionService.generate_profile()",
    reminders: "InventoryService.get_consumption_reminders()",
    profile_register: "UserRepository.create()",
    general: "LLMService.generate()"
  };

  return services[intent] || "Servicio no identificado";
}

function shortText(text, maxLength = 120) {
  const clean = String(text || "")
    .replace(/\s+/g, " ")
    .trim();

  if (clean.length <= maxLength) {
    return clean;
  }

  return clean.slice(0, maxLength) + "...";
}

init();