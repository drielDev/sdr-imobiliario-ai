import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center px-4 py-24 text-center sm:px-6">
      <p className="text-6xl font-bold text-violet-600 dark:text-violet-400">
        404
      </p>
      <p className="mt-3 text-lg font-semibold text-slate-800 dark:text-slate-100">
        Página não encontrada
      </p>
      <Link
        to="/"
        className="mt-6 rounded-lg bg-violet-600 px-5 py-2.5 font-semibold text-white transition hover:bg-violet-700"
      >
        Voltar para o início
      </Link>
    </div>
  );
}
