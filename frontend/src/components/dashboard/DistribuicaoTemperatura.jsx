import { TEMPERATURAS } from "../../lib/tipos";

function percentual(parte, total) {
  return total === 0 ? 0 : Math.round((parte / total) * 100);
}

// Barra empilhada única (parte de um todo) + legenda com contagem e %:
// a identidade de cada faixa nunca depende só da cor.
export default function DistribuicaoTemperatura({ porTemperatura, total }) {
  const faixas = TEMPERATURAS.map((t) => ({
    ...t,
    quantidade: porTemperatura?.[t.chave] ?? 0,
  }));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="font-semibold text-slate-900 dark:text-white">
        Temperatura dos leads
      </h2>
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Classificação automática pela qualificação
      </p>

      {total === 0 ? (
        <div className="mt-4 h-3 rounded bg-slate-100 dark:bg-slate-800" />
      ) : (
        <div
          className="mt-4 flex h-3 gap-0.5"
          role="img"
          aria-label={faixas
            .map((f) => `${f.label}: ${f.quantidade}`)
            .join(", ")}
        >
          {faixas
            .filter((f) => f.quantidade > 0)
            .map((f) => (
              <div
                key={f.chave}
                title={`${f.label}: ${f.quantidade} (${percentual(f.quantidade, total)}%)`}
                className={`${f.cor} h-full first:rounded-l last:rounded-r`}
                style={{ flexGrow: f.quantidade }}
              />
            ))}
        </div>
      )}

      <ul className="mt-4 grid grid-cols-3 gap-2">
        {faixas.map((f) => (
          <li key={f.chave}>
            <p className="flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-300">
              <span className={`h-2.5 w-2.5 rounded-sm ${f.cor}`} />
              {f.label}
            </p>
            <p className="text-lg font-semibold tabular-nums text-slate-900 dark:text-white">
              {f.quantidade}
              <span className="ml-1 text-xs font-normal text-slate-500 dark:text-slate-400">
                {percentual(f.quantidade, total)}%
              </span>
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
