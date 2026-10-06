import { useCallback, useEffect, useState } from "react";
import BadgeTemperatura from "../components/dashboard/BadgeTemperatura";
import DistribuicaoTemperatura from "../components/dashboard/DistribuicaoTemperatura";
import LeadDetalhe from "../components/dashboard/LeadDetalhe";
import StatTile from "../components/dashboard/StatTile";
import { IconRefresh } from "../components/icons";
import {
  executarFollowUpsPendentes,
  listarAgendamentos,
  listarLeadsDashboard,
  obterMetricas,
} from "../lib/api";
import { formatarDataHora, formatarTempoRelativo } from "../lib/format";
import {
  LABEL_INTENCAO,
  LABEL_STATUS_LEAD,
  LABEL_TIPO_AGENDAMENTO,
  TEMPERATURAS,
} from "../lib/tipos";

const INTERVALO_ATUALIZACAO_MS = 10000;

const FILTROS_TEMPERATURA = [
  { chave: "", label: "Todos" },
  ...TEMPERATURAS.map((t) => ({ chave: t.chave, label: t.label })),
];

export default function DashboardPage() {
  const [metricas, setMetricas] = useState(null);
  const [leads, setLeads] = useState([]);
  const [agendamentos, setAgendamentos] = useState([]);
  const [erro, setErro] = useState(null);
  const [atualizadoEm, setAtualizadoEm] = useState(null);
  const [filtroTemperatura, setFiltroTemperatura] = useState("");
  const [leadSelecionadoId, setLeadSelecionadoId] = useState(null);
  const [executandoFollowUp, setExecutandoFollowUp] = useState(false);
  const [aviso, setAviso] = useState(null);

  const carregar = useCallback(async () => {
    try {
      const [m, l, a] = await Promise.all([
        obterMetricas(),
        listarLeadsDashboard(),
        listarAgendamentos(),
      ]);
      setMetricas(m);
      setLeads(l);
      setAgendamentos(a);
      setErro(null);
      setAtualizadoEm(new Date().toISOString());
    } catch (e) {
      setErro(e.message);
    }
  }, []);

  useEffect(() => {
    carregar();
    const intervalo = setInterval(carregar, INTERVALO_ATUALIZACAO_MS);
    return () => clearInterval(intervalo);
  }, [carregar]);

  async function handleExecutarFollowUps() {
    setExecutandoFollowUp(true);
    try {
      const { leads_contatados } = await executarFollowUpsPendentes();
      setAviso(
        leads_contatados.length === 0
          ? "Nenhum lead está no momento de receber follow-up."
          : `Follow-up enviado para ${leads_contatados.length} lead(s).`,
      );
      await carregar();
    } catch (e) {
      setAviso(e.message);
    } finally {
      setExecutandoFollowUp(false);
    }
  }

  const leadsFiltrados = filtroTemperatura
    ? leads.filter((l) => l.temperatura === filtroTemperatura)
    : leads;

  const leadSelecionado = leads.find((l) => l.id === leadSelecionadoId);

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Painel do corretor
          </h1>
          <p className="mt-1 text-slate-500 dark:text-slate-400">
            Leads atendidos pela Bia, qualificação, agendamentos e follow-ups.
            {atualizadoEm && (
              <span className="ml-1 text-xs">
                Atualizado {formatarTempoRelativo(atualizadoEm)}.
              </span>
            )}
          </p>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={carregar}
            aria-label="Atualizar"
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-300 text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <IconRefresh className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={handleExecutarFollowUps}
            disabled={executandoFollowUp}
            className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-700 disabled:opacity-50"
          >
            {executandoFollowUp ? "Executando..." : "Rodar follow-ups agora"}
          </button>
        </div>
      </div>

      {erro && (
        <p className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {erro}
        </p>
      )}

      {aviso && (
        <p className="mb-6 rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          {aviso}
        </p>
      )}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatTile
          titulo="Leads"
          valor={metricas?.total_leads ?? "—"}
          destaque
        />
        <StatTile
          titulo="Leads quentes"
          valor={metricas?.por_temperatura.quente ?? "—"}
        />
        <StatTile
          titulo="Qualificados"
          valor={metricas?.leads_qualificados ?? "—"}
          detalhe="todos os dados obrigatórios"
        />
        <StatTile
          titulo="Agendamentos"
          valor={metricas?.agendamentos_ativos ?? "—"}
          detalhe="visitas e reuniões ativas"
        />
        <StatTile
          titulo="Follow-ups pendentes"
          valor={metricas?.followups_pendentes ?? "—"}
          detalhe={
            metricas ? `${metricas.followups_enviados} já enviados` : undefined
          }
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_340px]">
        <div className="min-w-0 rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
            <h2 className="font-semibold text-slate-900 dark:text-white">
              Leads
            </h2>
            <div className="flex gap-1">
              {FILTROS_TEMPERATURA.map((f) => (
                <button
                  key={f.chave}
                  type="button"
                  onClick={() => setFiltroTemperatura(f.chave)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                    filtroTemperatura === f.chave
                      ? "bg-violet-600 text-white"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {leadsFiltrados.length === 0 ? (
            <p className="border-t border-slate-200 px-5 py-10 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
              {leads.length === 0
                ? "Nenhum lead ainda. Converse com a Bia pelo chat para gerar o primeiro."
                : "Nenhum lead com essa temperatura."}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-y border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-400">
                  <tr>
                    <th className="px-5 py-2.5 font-medium">Cliente</th>
                    <th className="px-3 py-2.5 font-medium">Intenção</th>
                    <th className="px-3 py-2.5 font-medium">Temperatura</th>
                    <th className="px-3 py-2.5 font-medium">Status</th>
                    <th className="px-5 py-2.5 text-right font-medium">
                      Última interação
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {leadsFiltrados.map((lead) => (
                    <tr
                      key={lead.id}
                      onClick={() => setLeadSelecionadoId(lead.id)}
                      className="cursor-pointer transition hover:bg-violet-50/60 dark:hover:bg-violet-500/5"
                    >
                      <td className="px-5 py-3">
                        <p className="font-medium text-slate-900 dark:text-white">
                          {lead.nome || "Cliente sem nome"}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {lead.regiao || lead.contato}
                        </p>
                      </td>
                      <td className="px-3 py-3 text-slate-700 dark:text-slate-200">
                        {LABEL_INTENCAO[lead.intencao] ?? lead.intencao}
                      </td>
                      <td className="px-3 py-3">
                        <BadgeTemperatura temperatura={lead.temperatura} />
                      </td>
                      <td className="px-3 py-3 text-slate-700 dark:text-slate-200">
                        {LABEL_STATUS_LEAD[lead.status] ?? lead.status}
                        {lead.tentativas_followup > 0 && (
                          <span className="ml-1 text-xs text-slate-500 dark:text-slate-400">
                            ({lead.tentativas_followup}/
                            {lead.max_tentativas_followup} follow-ups)
                          </span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-5 py-3 text-right text-slate-500 dark:text-slate-400">
                        {formatarTempoRelativo(lead.ultima_interacao_em)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <DistribuicaoTemperatura
            porTemperatura={metricas?.por_temperatura}
            total={metricas?.total_leads ?? 0}
          />

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="font-semibold text-slate-900 dark:text-white">
              Próximos agendamentos
            </h2>
            {agendamentos.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Nenhum agendamento ainda.
              </p>
            ) : (
              <ul className="mt-3 space-y-3">
                {agendamentos.map(({ agendamento, lead_nome, lead_contato }) => (
                  <li key={agendamento.id}>
                    <button
                      type="button"
                      onClick={() => setLeadSelecionadoId(agendamento.lead_id)}
                      className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-left transition hover:border-violet-300 dark:border-slate-800 dark:hover:border-violet-500/40"
                    >
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">
                        {formatarDataHora(agendamento.inicio)}
                      </p>
                      <p className="text-sm text-slate-600 dark:text-slate-300">
                        {LABEL_TIPO_AGENDAMENTO[agendamento.tipo] ??
                          agendamento.tipo}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {lead_nome || lead_contato || agendamento.lead_id}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {leadSelecionado && (
        <LeadDetalhe
          lead={leadSelecionado}
          onFechar={() => setLeadSelecionadoId(null)}
          onAtualizado={carregar}
        />
      )}
    </div>
  );
}
