export default function StatTile({ titulo, valor, detalhe, destaque = false }) {
  return (
    <div
      className={`rounded-2xl border p-4 ${
        destaque
          ? "border-violet-200 bg-violet-50 dark:border-violet-500/30 dark:bg-violet-500/10"
          : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
      }`}
    >
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
        {titulo}
      </p>
      <p className="mt-1 text-3xl font-bold tabular-nums text-slate-900 dark:text-white">
        {valor}
      </p>
      {detalhe && (
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          {detalhe}
        </p>
      )}
    </div>
  );
}
