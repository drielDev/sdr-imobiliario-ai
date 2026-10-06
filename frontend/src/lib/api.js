const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

async function requisitar(caminho, opcoes = {}) {
  let resposta;

  try {
    resposta = await fetch(`${API_BASE_URL}${caminho}`, {
      headers: { "Content-Type": "application/json" },
      ...opcoes,
    });
  } catch {
    throw new Error(
      "Não foi possível conectar à API. Verifique se o backend está rodando.",
    );
  }

  if (!resposta.ok) {
    let detalhe = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      if (typeof corpo.detail === "string") detalhe = corpo.detail;
    } catch {
      // resposta sem JSON: mantém a mensagem genérica
    }
    throw new Error(detalhe);
  }

  return resposta.json();
}

function semCamposVazios(filtros) {
  return Object.fromEntries(
    Object.entries(filtros).filter(
      ([, valor]) => valor !== "" && valor !== null && valor !== undefined,
    ),
  );
}

// --- Catálogo ---------------------------------------------------------

export function listarImoveis() {
  return requisitar("/imoveis/");
}

export function buscarImovelPorId(id) {
  return requisitar(`/imoveis/${encodeURIComponent(id)}`);
}

export function buscarImoveis(filtros) {
  return requisitar("/imoveis/buscar", {
    method: "POST",
    body: JSON.stringify(semCamposVazios(filtros)),
  });
}

// --- Chat -------------------------------------------------------------

export async function enviarMensagem(sessaoId, mensagem) {
  const dados = await requisitar("/chat/", {
    method: "POST",
    body: JSON.stringify({ sessao_id: sessaoId, mensagem }),
  });
  return dados.resposta;
}

export function obterHistorico(sessaoId) {
  return requisitar(`/chat/${encodeURIComponent(sessaoId)}/historico`);
}

export function buscarMensagensPendentes(sessaoId) {
  return requisitar(`/chat/${encodeURIComponent(sessaoId)}/pendentes`);
}

export function reiniciarConversa(sessaoId) {
  return requisitar(`/chat/${encodeURIComponent(sessaoId)}/reiniciar`, {
    method: "POST",
  });
}

// --- Dashboard --------------------------------------------------------

export function obterMetricas() {
  return requisitar("/dashboard/metricas");
}

export function listarLeadsDashboard() {
  return requisitar("/dashboard/leads");
}

export function listarAgendamentos() {
  return requisitar("/dashboard/agendamentos");
}

export function obterDetalheLead(leadId, comIa = false) {
  const query = comIa ? "?com_ia=true" : "";
  return requisitar(`/dashboard/leads/${encodeURIComponent(leadId)}${query}`);
}

export function dispararFollowUp(leadId) {
  return requisitar(`/dashboard/leads/${encodeURIComponent(leadId)}/followup`, {
    method: "POST",
  });
}

export function executarFollowUpsPendentes() {
  return requisitar("/dashboard/followup/executar", { method: "POST" });
}
