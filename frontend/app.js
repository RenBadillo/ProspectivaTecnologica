const API = "http://127.0.0.1:8000";

let inventory = [];
let profiles = {};
let activeSection = "dashboard";

const titles = {
    dashboard: ["Dashboard", "Resumen general del sistema"],
    inventory: ["Inventario", "Gestión de productos"],
    chat: ["Chat bot", "Prueba del flujo principal"],
    history: ["Historial", "Mensajes procesados por el backend"],
    copilots: ["Copilotos", "Perfiles especializados del LLM"]
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
    $(id).className = ok ? "dot ok" : "dot bad";
}

async function fetchJSON(url, options = {}) {
    const res = await fetch(url, options);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
        throw new Error(
            data.detail ||
            data.message ||
            "Error del backend"
        );
    }

    return data;
}

function showSection(section) {
    activeSection = section;

    document.querySelectorAll(".section").forEach((el) => {
        el.classList.toggle("active", el.id === section);
    });

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
        headers: {"Content-Type": "application/json"},
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
        headers: {"Content-Type": "application/json"},
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
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                numero,
                mensaje
            })
        });

        addBubble("chatWindow", "Bot", data.respuesta, "bot");

        await loadInventory(false);
        await loadDashboard();
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
            headers: {"Content-Type": "application/json"},
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

init();
