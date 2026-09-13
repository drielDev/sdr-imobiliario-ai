import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import PropertyCard from "../components/PropertyCard";
import { IconArrowRight, IconChat, IconSearch } from "../components/icons";
import { useChatWidget } from "../context/ChatContext";
import { listarImoveis } from "../lib/api";

const PASSOS = [
  {
    titulo: "Conte o que você procura",
    texto:
      'Fale com a Bia como falaria com um corretor: "quero alugar um studio até R$ 2.500 perto do metrô".',
  },
  {
    titulo: "A IA entende e filtra o catálogo",
    texto:
      "A Bia identifica se é compra, aluguel ou investimento e busca no catálogo real de imóveis.",
  },
  {
    titulo: "Você recebe opções de verdade",
    texto:
      "Sem enrolação: imóveis reais, com preço, bairro e características, prontos para avaliar.",
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const { abrirChat } = useChatWidget();

  const [imoveis, setImoveis] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [finalidade, setFinalidade] = useState("compra");
  const [busca, setBusca] = useState("");

  useEffect(() => {
    listarImoveis()
      .then(setImoveis)
      .catch(() => setImoveis([]))
      .finally(() => setCarregando(false));
  }, []);

  const disponiveis = useMemo(
    () => imoveis.filter((i) => i.disponivel),
    [imoveis],
  );

  const destaques = useMemo(() => disponiveis.slice(0, 6), [disponiveis]);

  const totalBairros = useMemo(
    () => new Set(imoveis.map((i) => i.bairro)).size,
    [imoveis],
  );

  const totalCidades = useMemo(
    () => new Set(imoveis.map((i) => i.cidade)).size,
    [imoveis],
  );

  function handleBuscar(e) {
    e.preventDefault();
    const params = new URLSearchParams({ finalidade });
    if (busca.trim()) params.set("bairro", busca.trim());
    navigate(`/imoveis?${params.toString()}`);
  }

  return (
    <div>
      <section className="relative overflow-hidden bg-gradient-to-br from-violet-600 via-violet-700 to-slate-900">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
          <p className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-violet-100">
            <IconChat className="h-3.5 w-3.5" />
            Com assistente virtual por IA
          </p>

          <h1 className="mt-4 max-w-2xl text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Encontre o imóvel ideal para comprar, alugar ou investir
          </h1>
          <p className="mt-4 max-w-xl text-lg text-violet-100">
            Converse com a Bia, nossa assistente virtual, ou explore direto o
            catálogo de imóveis disponíveis.
          </p>

          <form
            onSubmit={handleBuscar}
            className="mt-8 flex max-w-2xl flex-col gap-2 rounded-2xl bg-white p-2 shadow-xl sm:flex-row sm:items-center dark:bg-slate-900"
          >
            <select
              value={finalidade}
              onChange={(e) => setFinalidade(e.target.value)}
              className="rounded-xl border-0 bg-slate-100 px-3.5 py-3 text-sm font-medium text-slate-700 outline-none dark:bg-slate-800 dark:text-slate-200"
            >
              <option value="compra">Comprar</option>
              <option value="aluguel">Alugar</option>
            </select>

            <div className="flex flex-1 items-center gap-2 px-2">
              <IconSearch className="h-4 w-4 shrink-0 text-slate-400" />
              <input
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Bairro, cidade ou tipo de imóvel..."
                className="w-full border-0 bg-transparent py-3 text-sm text-slate-800 outline-none placeholder:text-slate-400 dark:text-slate-100"
              />
            </div>

            <button
              type="submit"
              className="flex items-center justify-center gap-1.5 rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet-700"
            >
              Buscar
              <IconArrowRight className="h-4 w-4" />
            </button>
          </form>

          <button
            type="button"
            onClick={() => abrirChat()}
            className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-violet-100 underline underline-offset-4 hover:text-white"
          >
            ou converse com a Bia para uma busca mais específica
          </button>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="grid grid-cols-2 gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-4 dark:border-slate-800 dark:bg-slate-900">
          {[
            [imoveis.length || "—", "imóveis no catálogo"],
            [disponiveis.length || "—", "disponíveis agora"],
            [totalBairros || "—", "bairros atendidos"],
            [totalCidades || "—", "cidade(s) atendida(s)"],
          ].map(([numero, label]) => (
            <div key={label} className="text-center">
              <p className="text-2xl font-bold text-violet-600 dark:text-violet-400">
                {numero}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {label}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
              Imóveis em destaque
            </h2>
            <p className="mt-1 text-slate-500 dark:text-slate-400">
              Uma amostra do que temos disponível agora.
            </p>
          </div>
          <a
            href="/imoveis"
            className="hidden items-center gap-1 text-sm font-semibold text-violet-600 hover:text-violet-700 sm:flex dark:text-violet-400"
          >
            Ver todos <IconArrowRight className="h-4 w-4" />
          </a>
        </div>

        {carregando ? (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-72 animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800"
              />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {destaques.map((imovel) => (
              <PropertyCard key={imovel.id} imovel={imovel} />
            ))}
          </div>
        )}

        <a
          href="/imoveis"
          className="mt-8 flex items-center justify-center gap-1 text-sm font-semibold text-violet-600 hover:text-violet-700 sm:hidden dark:text-violet-400"
        >
          Ver todos os imóveis <IconArrowRight className="h-4 w-4" />
        </a>
      </section>

      <section className="border-y border-slate-200 bg-white py-16 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-center text-2xl font-bold text-slate-900 dark:text-white">
            Como funciona a busca com IA
          </h2>
          <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-3">
            {PASSOS.map((passo, i) => (
              <div key={passo.titulo} className="text-center sm:text-left">
                <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-violet-600 text-sm font-bold text-white sm:mx-0">
                  {i + 1}
                </div>
                <h3 className="mt-3 font-semibold text-slate-900 dark:text-white">
                  {passo.titulo}
                </h3>
                <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
                  {passo.texto}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-10 flex justify-center">
            <button
              type="button"
              onClick={() => abrirChat()}
              className="flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700"
            >
              <IconChat className="h-5 w-5" />
              Conversar com a Bia agora
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
