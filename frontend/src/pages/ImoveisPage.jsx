import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import PropertyCard from "../components/PropertyCard";
import { IconChat } from "../components/icons";
import { useChatWidget } from "../context/ChatContext";
import { buscarImoveis } from "../lib/api";

const FILTROS_VAZIOS = {
  finalidade: "",
  tipo: "",
  cidade: "",
  bairro: "",
  preco_min: "",
  preco_max: "",
  quartos_min: "",
  vagas_min: "",
};

export default function ImoveisPage() {
  const [searchParams] = useSearchParams();
  const { abrirChat } = useChatWidget();

  const [filtros, setFiltros] = useState({
    ...FILTROS_VAZIOS,
    ...Object.fromEntries(searchParams.entries()),
  });
  const [imoveis, setImoveis] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);

  const executarBusca = useCallback(async (filtrosAtuais) => {
    setCarregando(true);
    setErro(null);

    try {
      const resultado = await buscarImoveis(filtrosAtuais);
      setImoveis(resultado);
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    executarBusca(filtros);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleChange(campo, valor) {
    setFiltros((atual) => ({ ...atual, [campo]: valor }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    executarBusca(filtros);
  }

  function handleLimpar() {
    setFiltros(FILTROS_VAZIOS);
    executarBusca(FILTROS_VAZIOS);
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Imóveis disponíveis
        </h1>
        <p className="mt-1 text-slate-500 dark:text-slate-400">
          Filtre por critério exato, ou{" "}
          <button
            type="button"
            onClick={() => abrirChat()}
            className="font-medium text-violet-600 underline underline-offset-2 dark:text-violet-400"
          >
            converse com a Bia
          </button>{" "}
          para uma busca mais livre.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[260px_1fr]">
        <form
          onSubmit={handleSubmit}
          className="h-fit space-y-4 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
        >
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
              Finalidade
            </label>
            <select
              value={filtros.finalidade}
              onChange={(e) => handleChange("finalidade", e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            >
              <option value="">Qualquer</option>
              <option value="compra">Comprar</option>
              <option value="aluguel">Alugar</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
              Tipo
            </label>
            <select
              value={filtros.tipo}
              onChange={(e) => handleChange("tipo", e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            >
              <option value="">Qualquer</option>
              <option value="apartamento">Apartamento</option>
              <option value="casa">Casa</option>
              <option value="studio">Studio</option>
              <option value="loft">Loft</option>
              <option value="sobrado">Sobrado</option>
              <option value="cobertura">Cobertura</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
              Bairro
            </label>
            <input
              value={filtros.bairro}
              onChange={(e) => handleChange("bairro", e.target.value)}
              placeholder="ex: Pinheiros"
              className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
                Preço min.
              </label>
              <input
                type="number"
                value={filtros.preco_min}
                onChange={(e) => handleChange("preco_min", e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
                Preço máx.
              </label>
              <input
                type="number"
                value={filtros.preco_max}
                onChange={(e) => handleChange("preco_max", e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
                Quartos (mín.)
              </label>
              <select
                value={filtros.quartos_min}
                onChange={(e) => handleChange("quartos_min", e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="">Qualquer</option>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}+
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
                Vagas (mín.)
              </label>
              <select
                value={filtros.vagas_min}
                onChange={(e) => handleChange("vagas_min", e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="">Qualquer</option>
                {[1, 2, 3, 4].map((n) => (
                  <option key={n} value={n}>
                    {n}+
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              className="flex-1 rounded-lg bg-violet-600 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-violet-700"
            >
              Filtrar
            </button>
            <button
              type="button"
              onClick={handleLimpar}
              className="rounded-lg border border-slate-300 px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Limpar
            </button>
          </div>
        </form>

        <div>
          {carregando && (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-72 animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800"
                />
              ))}
            </div>
          )}

          {!carregando && erro && (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
              {erro}
            </div>
          )}

          {!carregando && !erro && imoveis.length === 0 && (
            <div className="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-700">
              <p className="font-medium text-slate-700 dark:text-slate-200">
                Nenhum imóvel encontrado com esses critérios.
              </p>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Tente ajustar os filtros, ou peça ajuda à Bia.
              </p>
              <button
                type="button"
                onClick={() => abrirChat()}
                className="mt-4 flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-700"
              >
                <IconChat className="h-4 w-4" />
                Falar com a Bia
              </button>
            </div>
          )}

          {!carregando && !erro && imoveis.length > 0 && (
            <>
              <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
                {imoveis.length} imóvel(is) encontrado(s)
              </p>
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {imoveis.map((imovel) => (
                  <PropertyCard key={imovel.id} imovel={imovel} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
