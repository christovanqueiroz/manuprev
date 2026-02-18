async function requestJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let detail = "Erro ao processar solicitação";
    try {
      const body = await response.json();
      detail = body.error || JSON.stringify(body);
    } catch (_e) {
      detail = await response.text();
    }
    throw new Error(detail);
  }

  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return null;
}

function isoDateTimeLocalToIso(value) {
  if (!value) return value;
  return new Date(value).toISOString().slice(0, 19);
}

function setFeedback(elementId, message, type = "ok") {
  const node = document.getElementById(elementId);
  node.textContent = message;
  node.className = `feedback ${type}`;
}

function renderList(elementId, items, mapper) {
  const list = document.getElementById(elementId);
  list.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = mapper(item);
    list.appendChild(li);
  });
}

async function loadEquipments() {
  const rows = await requestJSON("/equipments");
  renderList(
    "equipment-list",
    rows,
    (item) => `#${item.id} - ${item.name} (${item.category}) | Série: ${item.serial_number} | Local: ${item.location}`,
  );
}

async function loadPlans() {
  const rows = await requestJSON("/preventive-plans");
  renderList(
    "plan-list",
    rows,
    (item) =>
      `Plano #${item.id} | Eq:${item.equipment_id} | ${item.frequency_days} dias | Próxima: ${item.next_due_date} | Ativo: ${item.active}`,
  );
}

async function loadCorrectives() {
  const rows = await requestJSON("/corrective-records");
  renderList(
    "corrective-list",
    rows,
    (item) =>
      `#${item.id} Eq:${item.equipment_id} | Falha: ${item.description} | Início: ${item.failure_start} | Fim: ${item.repair_end}`,
  );
}

async function loadIndicators() {
  const eq = document.getElementById("indicator-equipment-id").value;
  const url = eq ? `/indicators?equipment_id=${encodeURIComponent(eq)}` : "/indicators";
  const data = await requestJSON(url);
  const rows = Array.isArray(data) ? data : [data];
  renderList(
    "indicator-list",
    rows,
    (item) => `Eq:${item.equipment_id} | MTBF: ${item.mtbf_hours ?? "N/A"}h | MTTR: ${item.mttr_hours ?? "N/A"}h`,
  );
}

function formToObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function onSubmitEquipment(event) {
  event.preventDefault();
  try {
    const payload = formToObject(event.target);
    await requestJSON("/equipments", { method: "POST", body: JSON.stringify(payload) });
    event.target.reset();
    setFeedback("equipment-feedback", "Equipamento cadastrado com sucesso.");
    await loadEquipments();
  } catch (error) {
    setFeedback("equipment-feedback", error.message, "error");
  }
}

async function onSubmitPlan(event) {
  event.preventDefault();
  try {
    const payload = formToObject(event.target);
    payload.equipment_id = Number(payload.equipment_id);
    payload.frequency_days = Number(payload.frequency_days);
    payload.active = event.target.active.checked;
    await requestJSON("/preventive-plans", { method: "POST", body: JSON.stringify(payload) });
    event.target.reset();
    event.target.active.checked = true;
    setFeedback("plan-feedback", "Plano preventivo cadastrado com sucesso.");
    await loadPlans();
  } catch (error) {
    setFeedback("plan-feedback", error.message, "error");
  }
}

async function onSubmitCorrective(event) {
  event.preventDefault();
  try {
    const payload = formToObject(event.target);
    payload.equipment_id = Number(payload.equipment_id);
    payload.failure_start = isoDateTimeLocalToIso(payload.failure_start);
    payload.repair_end = isoDateTimeLocalToIso(payload.repair_end);
    await requestJSON("/corrective-records", { method: "POST", body: JSON.stringify(payload) });
    event.target.reset();
    setFeedback("corrective-feedback", "Corretiva registrada com sucesso.");
    await loadCorrectives();
    await loadIndicators();
  } catch (error) {
    setFeedback("corrective-feedback", error.message, "error");
  }
}

async function initialize() {
  document.getElementById("equipment-form").addEventListener("submit", onSubmitEquipment);
  document.getElementById("plan-form").addEventListener("submit", onSubmitPlan);
  document.getElementById("corrective-form").addEventListener("submit", onSubmitCorrective);
  document.getElementById("indicator-load").addEventListener("click", async () => {
    try {
      await loadIndicators();
    } catch (error) {
      setFeedback("corrective-feedback", error.message, "error");
    }
  });

  try {
    await Promise.all([loadEquipments(), loadPlans(), loadCorrectives(), loadIndicators()]);
  } catch (error) {
    setFeedback("equipment-feedback", `Falha ao carregar dados iniciais: ${error.message}`, "error");
  }
}

initialize();
