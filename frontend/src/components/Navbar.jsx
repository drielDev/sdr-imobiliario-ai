import { NavLink } from "react-router-dom";
import { useChatWidget } from "../context/ChatContext";
import { IconChat, IconHouse } from "./icons";

const LINKS = [
  { to: "/", label: "Início", fim: true },
  { to: "/imoveis", label: "Imóveis" },
  { to: "/dashboard", label: "Painel do corretor" },
];

export default function Navbar() {
  const { abrirChat } = useChatWidget();

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <NavLink to="/" className="flex items-center gap-2 font-semibold">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-violet-700 text-white">
            <IconHouse className="h-5 w-5" />
          </span>
          <span className="text-slate-900 dark:text-white">NovaCasa</span>
        </NavLink>

        <nav className="hidden items-center gap-1 sm:flex">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.fim}
              className={({ isActive }) =>
                `rounded-lg px-3.5 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-violet-50 text-violet-700 dark:bg-violet-500/10 dark:text-violet-300"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          onClick={() => abrirChat()}
          className="flex items-center gap-2 rounded-lg bg-violet-600 px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-violet-700"
        >
          <IconChat className="h-4 w-4" />
          <span className="hidden sm:inline">Falar com a Bia</span>
        </button>
      </div>
    </header>
  );
}
