import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  IconArrowRight,
  IconBath,
  IconBed,
  IconCar,
  IconChat,
  IconMapPin,
  IconRuler,
} from "../components/icons";
import { useChatWidget } from "../context/ChatContext";
import { buscarImovelPorId } from "../lib/api";
import { formatarArea, formatarPreco } from "../lib/format";
import { infoTipo, LABEL_FINALIDADE } from "../lib/tipos";

export default function ImovelDetalhePage() {
  const { id } = useParams();
  const { abrirChat } = useChatWidget();

  const [imovel, setImovel] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    setCarregando(true);
    setErro(null);

    buscarImovelPorId(id)
      .then(setImovel)
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false));
  }, [id]);

  if (carregando) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
        <div className="h-64 animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
      </div>
    );
  }

  if (erro || !imovel) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6">
        <p className="text-lg font-semibold text-slate-800 dark:text-slate-100">
          Imóvel não encontrado.
        </p>
        <p className="mt-1 text-slate-500 dark:text-slate-400">
          {erro || "Verifique o link ou volte para a lista de imóveis."}
        </p>
        <Link
          to="/imoveis"
          className="mt-6 inline-flex items-center gap-1 font-medium text-violet-600 dark:text-violet-400"
        >
          ← Voltar para imóveis
        </Link>
      </div>
    );
  }

  const tipo = infoTipo(imovel.tipo);
  const Icone = tipo.icone;

  function falarSobreEsseImovel() {
    abrirChat(
      `Olá! Tenho interesse no imóvel "${imovel.titulo}" (ID ${imovel.id}), no bairro ${imovel.bairro}. Pode me contar mais e como faço para avançar?`,
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <Link
        to="/imoveis"
        className="mb-6 inline-flex items-center gap-1 text-sm font-medium text-slate-500 hover:text-violet-600 dark:text-slate-400 dark:hover:text-violet-400"
      >
        ← Voltar para imóveis
      </Link>

      <div
        className={`relative flex h-56 items-center justify-center rounded-2xl bg-gradient-to-br ${tipo.gradiente} sm:h-72`}
      >
        <Icone className="h-16 w-16 text-white/90" />
        <span className="absolute left-4 top-4 rounded-full bg-black/25 px-3 py-1 text-sm font-medium text-white backdrop-blur-sm">
          {tipo.label}
        </span>
        <span className="absolute right-4 top-4 rounded-full bg-white/90 px-3 py-1 text-sm font-semibold text-slate-800">
          {LABEL_FINALIDADE[imovel.finalidade] ?? imovel.finalidade}
        </span>
        {!imovel.disponivel && (
          <span className="absolute inset-0 flex items-center justify-center rounded-2xl bg-slate-900/60 text-lg font-semibold text-white">
            Indisponível no momento
          </span>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">
            {imovel.titulo}
          </h1>
          <p className="mt-1.5 flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
            <IconMapPin className="h-4 w-4" />
            {imovel.bairro}, {imovel.cidade}
          </p>

          <div className="mt-6 grid grid-cols-2 gap-4 rounded-2xl border border-slate-200 p-5 sm:grid-cols-4 dark:border-slate-800">
            {[
              [IconBed, imovel.quartos, "quarto(s)"],
              [IconBath, imovel.banheiros, "banheiro(s)"],
              [IconCar, imovel.vagas, "vaga(s)"],
              [IconRuler, formatarArea(imovel.area_m2), ""],
            ].map(([Icon, valor, label], i) => (
              <div key={i} className="flex flex-col items-center text-center">
                <Icon className="h-5 w-5 text-violet-600 dark:text-violet-400" />
                <p className="mt-1.5 font-semibold text-slate-900 dark:text-white">
                  {valor}
                </p>
                {label && (
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {label}
                  </p>
                )}
              </div>
            ))}
          </div>

          <div className="mt-8">
            <h2 className="font-semibold text-slate-900 dark:text-white">
              Descrição
            </h2>
            <p className="mt-2 leading-relaxed text-slate-600 dark:text-slate-300">
              {imovel.descricao}
            </p>
          </div>
        </div>

        <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {LABEL_FINALIDADE[imovel.finalidade] ?? imovel.finalidade}
          </p>
          <p className="text-3xl font-bold text-slate-900 dark:text-white">
            {formatarPreco(imovel.preco)}
          </p>

          <button
            type="button"
            onClick={falarSobreEsseImovel}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 font-semibold text-white transition hover:bg-violet-700"
          >
            <IconChat className="h-4 w-4" />
            Falar com a Bia sobre esse imóvel
          </button>

          <Link
            to="/imoveis"
            className="mt-3 flex w-full items-center justify-center gap-1 rounded-xl border border-slate-300 px-4 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Ver imóveis parecidos
            <IconArrowRight className="h-4 w-4" />
          </Link>
        </aside>
      </div>
    </div>
  );
}
