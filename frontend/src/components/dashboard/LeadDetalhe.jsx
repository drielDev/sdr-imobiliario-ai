import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { dispararFollowUp, obterDetalheLead } from "../../lib/api";
import { formatarDataHora, formatarPreco } from "../../lib/format";
import {
  LABEL_CAMPO_LEAD,
  LABEL_INTENCAO,
  LABEL_STATUS_LEAD,
  LABEL_TIPO_AGENDAMENTO,
} from "../../lib/tipos";
import { IconClose, IconSparkles } from "../icons";
import BadgeTemperatura from "./BadgeTemperatura";

const LABEL_URGENCIA = {
  alta: "Alta",
  media: "Média",
  baixa: "Baixa",
  indefinida: "Não informada",
};

function faixaDePreco({ preco_min, preco_max }) {
  if (preco_min && preco_max)
    return `${formatarPreco(preco_min)} a ${formatarPreco(preco_max)}`;
  if (preco_max) return `até ${formatarPreco(preco_max)}`;
  if (preco_min) return `a partir de ${formatarPreco(preco_min)}`;
  return null;
}

function Campo({ label, valor }) {
  return (
    <div>
      <dt className="text-xs text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="font-medium text-slate-900 dark:text-white">
        {valor ?? <span className="text-slate-400">—</span>}
      </dd>
    </div>
  );
}

function Secao({ titulo, children, acao }) {
  return (
    <section className="border-t border-slate-200 px-5 py-4 dark:border-slate-800">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
          {titulo}
        </h3>
        {acao}
      </div>
      {children}
    </section>
  );
}

export default function LeadDetalhe({ lead, onFechar, onAtualizado }) {
  const [detalhe, setDetalhe] = useState(null);
  const [erro, setErro] = useState(null);
  const [gerandoIa, setGerandoIa] = useState(false);
  const [enviandoFollowUp, setEnviandoFollowUp] = useState(false);
  const [aviso, setAviso] = useState(null);

  useEffect(() => {
    setDetalhe(null);
    setErro(null);
    setAviso(null);
    obterDetalheLead(lead.id)
      .then(setDetalhe)
      .catch((e) => setErro(e.message));
  }, [lead.id, lead.ultima_interacao_em, lead.tentativas_followup]);

  async function handleGerarIa() {
    setGerandoIa(true);
    setAviso(null);
    try {
      setDetalhe(await obterDetalheLead(lead.id, true));
    } catch (e) {
      setAviso(e.message);
    } finally {
      setGerandoIa(false);
    }
  }

  async function handleFollowUp() {
    setEnviandoFollowUp(true);
    setAviso(null);
    try {
      await dispararFollowUp(lead.id);
      setAviso("Follow-up enviado no chat do cliente.");
      onAtualizado();
    } catch (e) {
      setAviso(e.message);
    } finally {
      setEnviandoFollowUp(false);
    }
  }

  const resumo = detalhe?.resumo;
  const ehInvestimento = resumo?.intencao === "investimento";
  const podeFollowUp =
    !["agendado", "inativo", "perdido"].includes(lead.status) &&
    lead.tentativas_followup < lead.max_tentativas_followup;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="Fechar detalhes"
        onClick={onFechar}
        className="absolute inset-0 bg-slate-900/40"
      />

      <aside className="relative flex h-full w-full max-w-lg flex-col overflow-y-auto bg-white shadow-2xl dark:bg-slate-900">
        <header className="flex items-start gap-3 px-5 py-4">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium uppercase tracking-wide text-violet-600 dark:text-violet-400">
              Resumo para o corretor
            </p>
            <h2 className="truncate text-lg font-semibold text-slate-900 dark:text-white">
              {lead.nome || "Cliente sem nome"}
            </h2>
            <p className="truncate text-sm text-slate-500 dark:text-slate-400">
              {lead.contato} · {lead.canal}
            </p>
          </div>
          <button
            type="button"
            onClick={onFechar}
            aria-label="Fechar"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
          >
            <IconClose className="h-5 w-5" />
          </button>
        </header>

        {erro && <p className="px-5 pb-4 text-sm text-red-600">{erro}</p>}
        {!resumo && !erro && (
          <div className="mx-5 mb-4 h-40 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
        )}

        {resumo && (
          <>
            <div className="mx-5 mb-4 rounded-xl bg-violet-50 px-4 py-3 text-sm text-violet-900 dark:bg-violet-500/10 dark:text-violet-200">
              <span className="font-semibold">Próximo passo: </span>
              {resumo.proximo_passo_sugerido}
            </div>

            <Secao titulo="Perfil e interesse">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                <Campo label="Intenção" valor={LABEL_INTENCAO[resumo.intencao]} />
                <Campo
                  label="Status"
                  valor={LABEL_STATUS_LEAD[resumo.status] ?? resumo.status}
                />
                <Campo label="Região" valor={resumo.criterios.regiao} />
                <Campo
                  label="Urgência"
                  valor={LABEL_URGENCIA[resumo.urgencia] ?? resumo.urgencia}
                />
                {ehInvestimento ? (
                  <>
                    <Campo
                      label="Ticket"
                      valor={
                        resumo.ticket_investimento
                          ? formatarPreco(resumo.ticket_investimento)
                          : null
                      }
                    />
                    <Campo
                      label="Retorno esperado"
                      valor={resumo.expectativa_retorno}
                    />
                  </>
                ) : (
                  <>
                    <Campo
                      label="Orçamento"
                      valor={faixaDePreco(resumo.criterios)}
                    />
                    <Campo
                      label="Quartos (mín.)"
                      valor={resumo.criterios.quartos_min}
                    />
                  </>
                )}
                <div className="col-span-2">
                  <Campo label="Perfil" valor={resumo.perfil_cliente} />
                </div>
              </dl>
              {resumo.campos_faltantes.length > 0 && (
                <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                  Ainda falta:{" "}
                  {resumo.campos_faltantes
                    .map((c) => LABEL_CAMPO_LEAD[c] ?? c)
                    .join(", ")}
                </p>
              )}
            </Secao>

            <Secao
              titulo="Classificação"
              acao={<BadgeTemperatura temperatura={resumo.temperatura} />}
            >
              <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
                {resumo.motivos_classificacao.map((motivo) => (
                  <li key={motivo}>• {motivo}</li>
                ))}
              </ul>
            </Secao>

            <Secao titulo="Agendamento">
              {resumo.agendamento ? (
                <p className="text-sm text-slate-700 dark:text-slate-200">
                  {LABEL_TIPO_AGENDAMENTO[resumo.agendamento.tipo] ??
                    resumo.agendamento.tipo}{" "}
                  · {formatarDataHora(resumo.agendamento.inicio)} (
                  {resumo.agendamento.responsavel})
                </p>
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Nenhum agendamento.
                </p>
              )}
            </Secao>

            <Secao
              titulo="Pontos relevantes (IA)"
              acao={
                <button
                  type="button"
                  onClick={handleGerarIa}
                  disabled={gerandoIa || detalhe.conversa.length === 0}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-violet-200 px-2.5 py-1 text-xs font-semibold text-violet-700 transition hover:bg-violet-50 disabled:opacity-50 dark:border-violet-500/30 dark:text-violet-300 dark:hover:bg-violet-500/10"
                >
                  <IconSparkles className="h-3.5 w-3.5" />
                  {gerandoIa ? "Gerando..." : "Gerar com IA"}
                </button>
              }
            >
              {resumo.pontos_relevantes.length > 0 ? (
                <ul className="space-y-1 text-sm text-slate-700 dark:text-slate-200">
                  {resumo.pontos_relevantes.map((ponto) => (
                    <li key={ponto}>• {ponto}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  A IA lê a conversa e destaca o que o corretor precisa saber.
                </p>
              )}
            </Secao>

            <Secao
              titulo={`Follow-up (${lead.tentativas_followup}/${lead.max_tentativas_followup})`}
              acao={
                <button
                  type="button"
                  onClick={handleFollowUp}
                  disabled={!podeFollowUp || enviandoFollowUp}
                  className="rounded-lg bg-violet-600 px-2.5 py-1 text-xs font-semibold text-white transition hover:bg-violet-700 disabled:opacity-40"
                >
                  {enviandoFollowUp ? "Enviando..." : "Disparar agora"}
                </button>
              }
            >
              <p className="text-sm text-slate-500 dark:text-slate-400">
                O follow-up também roda sozinho quando o cliente para de
                responder.
              </p>
            </Secao>

            {aviso && (
              <p className="mx-5 mb-2 rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                {aviso}
              </p>
            )}

            <Secao titulo="Conversa">
              {detalhe.conversa.length === 0 ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Sem mensagens.
                </p>
              ) : (
                <ol className="space-y-2">
                  {detalhe.conversa.map((m, i) => (
                    <li
                      key={i}
                      className={`rounded-xl px-3 py-2 text-sm ${
                        m.papel === "user"
                          ? "ml-8 bg-violet-600 text-white"
                          : "mr-8 bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"
                      }`}
                    >
                      <ReactMarkdown>{m.texto}</ReactMarkdown>
                    </li>
                  ))}
                </ol>
              )}
            </Secao>
          </>
        )}
      </aside>
    </div>
  );
}
