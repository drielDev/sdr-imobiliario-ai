import { TEMPERATURAS } from "../../lib/tipos";

export default function BadgeTemperatura({ temperatura }) {
  const info = TEMPERATURAS.find((t) => t.chave === temperatura);

  if (!info) return <span>{temperatura}</span>;

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200">
      <span className={`h-2 w-2 rounded-full ${info.cor}`} />
      {info.label}
    </span>
  );
}
