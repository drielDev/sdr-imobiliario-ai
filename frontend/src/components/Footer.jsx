import { IconHouse } from "./icons";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col items-start justify-between gap-6 sm:flex-row">
          <div>
            <div className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 text-white">
                <IconHouse className="h-4 w-4" />
              </span>
              NovaCasa
            </div>
            <p className="mt-2 max-w-xs text-sm text-slate-500 dark:text-slate-400">
              Encontre o imóvel ideal para comprar, alugar ou investir, com a
              ajuda da Bia, nossa assistente virtual.
            </p>
          </div>

          <div className="text-sm text-slate-500 dark:text-slate-400">
            <p className="font-medium text-slate-700 dark:text-slate-200">
              Navegação
            </p>
            <ul className="mt-2 space-y-1.5">
              <li>
                <a href="/" className="hover:text-violet-600">
                  Início
                </a>
              </li>
              <li>
                <a href="/imoveis" className="hover:text-violet-600">
                  Imóveis
                </a>
              </li>
            </ul>
          </div>
        </div>

        <p className="mt-8 border-t border-slate-100 pt-6 text-xs text-slate-400 dark:border-slate-800">
          NovaCasa é um projeto acadêmico de demonstração — imóveis e dados
          fictícios.
        </p>
      </div>
    </footer>
  );
}
