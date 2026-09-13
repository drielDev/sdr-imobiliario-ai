import { Link } from "react-router-dom";
import { formatarPreco } from "../lib/format";
import { infoTipo, LABEL_FINALIDADE } from "../lib/tipos";
import { IconBath, IconBed, IconCar, IconMapPin, IconRuler } from "./icons";

export default function PropertyCard({ imovel }) {
  const tipo = infoTipo(imovel.tipo);
  const Icone = tipo.icone;

  return (
    <Link
      to={`/imoveis/${imovel.id}`}
      className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg dark:border-slate-800 dark:bg-slate-900"
    >
      <div
        className={`relative flex h-36 items-center justify-center bg-gradient-to-br ${tipo.gradiente}`}
      >
        <Icone className="h-12 w-12 text-white/90" />

        <span className="absolute left-3 top-3 rounded-full bg-black/25 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm">
          {tipo.label}
        </span>

        <span className="absolute right-3 top-3 rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold text-slate-800">
          {LABEL_FINALIDADE[imovel.finalidade] ?? imovel.finalidade}
        </span>

        {!imovel.disponivel && (
          <span className="absolute inset-0 flex items-center justify-center bg-slate-900/60 text-sm font-semibold text-white">
            Indisponível
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div>
          <h3 className="line-clamp-1 font-semibold text-slate-900 dark:text-white">
            {imovel.titulo}
          </h3>
          <p className="mt-0.5 flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
            <IconMapPin className="h-3.5 w-3.5 shrink-0" />
            <span className="line-clamp-1">
              {imovel.bairro}, {imovel.cidade}
            </span>
          </p>
        </div>

        <div className="flex items-center gap-3.5 text-sm text-slate-600 dark:text-slate-300">
          <span className="flex items-center gap-1">
            <IconBed className="h-4 w-4" /> {imovel.quartos}
          </span>
          <span className="flex items-center gap-1">
            <IconBath className="h-4 w-4" /> {imovel.banheiros}
          </span>
          <span className="flex items-center gap-1">
            <IconCar className="h-4 w-4" /> {imovel.vagas}
          </span>
          <span className="flex items-center gap-1">
            <IconRuler className="h-4 w-4" /> {imovel.area_m2}m²
          </span>
        </div>

        <div className="mt-auto flex items-center justify-between border-t border-slate-100 pt-3 dark:border-slate-800">
          <span className="text-lg font-bold text-slate-900 dark:text-white">
            {formatarPreco(imovel.preco)}
          </span>
          <span className="text-sm font-medium text-violet-600 transition group-hover:translate-x-0.5 dark:text-violet-400">
            Ver detalhes →
          </span>
        </div>
      </div>
    </Link>
  );
}
