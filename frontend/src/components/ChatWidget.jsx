import { useEffect, useRef, useState } from "react";
import { useChatWidget } from "../context/ChatContext";
import {
  buscarMensagensPendentes,
  enviarMensagem,
  obterHistorico,
  reiniciarConversa,
} from "../lib/api";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import {
  IconChat,
  IconClose,
  IconExpand,
  IconRefresh,
  IconShrink,
} from "./icons";
import TypingIndicator from "./TypingIndicator";

const MENSAGEM_BOAS_VINDAS = {
  id: "boas-vindas",
  role: "assistant",
  content:
    "Olá! Eu sou a **Bia**, assistente virtual de imóveis. 🏠\n\nMe conta o que você procura: quer **comprar**, **alugar** ou está pensando em **investir**?",
};

const CHAVE_SESSAO = "sdr-imobiliario:sessao-id";
const INTERVALO_PENDENTES_MS = 15000;

function criarId() {
  return crypto.randomUUID();
}

// A sessão fica no navegador para a conversa continuar depois de recarregar
// a página (o histórico em si mora no backend).
function sessaoSalva() {
  try {
    const existente = localStorage.getItem(CHAVE_SESSAO);
    if (existente) return existente;
    const nova = criarId();
    localStorage.setItem(CHAVE_SESSAO, nova);
    return nova;
  } catch {
    return criarId();
  }
}

function novaSessao() {
  const nova = criarId();
  try {
    localStorage.setItem(CHAVE_SESSAO, nova);
  } catch {
    // sem localStorage: a sessão vale só enquanto a página estiver aberta
  }
  return nova;
}

export default function ChatWidget() {
  const { aberto, abrirChat, fecharChat, rascunho, consumirRascunho } =
    useChatWidget();

  const [sessaoId, setSessaoId] = useState(sessaoSalva);
  const [mensagens, setMensagens] = useState([MENSAGEM_BOAS_VINDAS]);
  const [texto, setTexto] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [expandido, setExpandido] = useState(false);
  const [naoLidas, setNaoLidas] = useState(0);
  const fimDaListaRef = useRef(null);
  const abertoRef = useRef(aberto);

  useEffect(() => {
    abertoRef.current = aberto;
    if (aberto) setNaoLidas(0);
  }, [aberto]);

  useEffect(() => {
    let cancelado = false;

    obterHistorico(sessaoId)
      .then((historico) => {
        if (cancelado || historico.length === 0) return;
        setMensagens([
          MENSAGEM_BOAS_VINDAS,
          ...historico.map((m) => ({
            id: criarId(),
            role: m.papel === "user" ? "user" : "assistant",
            content: m.texto,
          })),
        ]);
      })
      .catch(() => {
        // sem histórico (API fora do ar ou sessão nova): segue com as boas-vindas
      });

    return () => {
      cancelado = true;
    };
  }, [sessaoId]);

  // Follow-up: mensagens que a Bia manda sozinha quando o cliente some.
  useEffect(() => {
    const intervalo = setInterval(async () => {
      try {
        const pendentes = await buscarMensagensPendentes(sessaoId);
        if (pendentes.length === 0) return;
        setMensagens((atual) => [
          ...atual,
          ...pendentes.map((p) => ({
            id: criarId(),
            role: "assistant",
            content: p.texto,
          })),
        ]);
        if (!abertoRef.current) {
          setNaoLidas((n) => n + pendentes.length);
        }
      } catch {
        // tenta de novo no próximo ciclo
      }
    }, INTERVALO_PENDENTES_MS);

    return () => clearInterval(intervalo);
  }, [sessaoId]);

  useEffect(() => {
    if (aberto && rascunho) {
      setTexto(consumirRascunho());
    }
  }, [aberto, rascunho, consumirRascunho]);

  useEffect(() => {
    if (aberto) {
      fimDaListaRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [mensagens, carregando, aberto]);

  function handleNovaConversa() {
    reiniciarConversa(sessaoId).catch(() => {});
    setSessaoId(novaSessao());
    setMensagens([MENSAGEM_BOAS_VINDAS]);
    setTexto("");
  }

  async function handleEnviar() {
    const mensagemUsuario = texto.trim();
    if (!mensagemUsuario) return;

    setMensagens((atual) => [
      ...atual,
      { id: criarId(), role: "user", content: mensagemUsuario },
    ]);
    setTexto("");
    setCarregando(true);

    try {
      const resposta = await enviarMensagem(sessaoId, mensagemUsuario);
      setMensagens((atual) => [
        ...atual,
        { id: criarId(), role: "assistant", content: resposta },
      ]);
    } catch (erro) {
      setMensagens((atual) => [
        ...atual,
        { id: criarId(), role: "error", content: erro.message },
      ]);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <>
      {aberto && (
        <div
          className={
            expandido
              ? "fixed inset-4 z-40 flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-2xl dark:border-slate-800 dark:bg-slate-900 sm:inset-8"
              : "fixed inset-x-4 bottom-24 top-auto z-40 flex h-[70vh] max-h-[600px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-2xl dark:border-slate-800 dark:bg-slate-900 sm:inset-auto sm:bottom-24 sm:right-6 sm:h-[600px] sm:w-96"
          }
        >
          <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3.5 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-violet-700 text-sm font-semibold text-white">
              B
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate font-semibold text-slate-900 dark:text-white">
                Bia · Assistente
              </p>
              <p className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Online agora
              </p>
            </div>
            <button
              type="button"
              onClick={handleNovaConversa}
              disabled={carregando}
              aria-label="Nova conversa"
              title="Nova conversa"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 disabled:opacity-40 dark:hover:bg-slate-800 dark:hover:text-slate-300"
            >
              <IconRefresh className="h-[18px] w-[18px]" />
            </button>
            <button
              type="button"
              onClick={() => setExpandido((v) => !v)}
              aria-label={expandido ? "Reduzir chat" : "Expandir chat"}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
            >
              {expandido ? (
                <IconShrink className="h-5 w-5" />
              ) : (
                <IconExpand className="h-5 w-5" />
              )}
            </button>
            <button
              type="button"
              onClick={fecharChat}
              aria-label="Fechar chat"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
            >
              <IconClose className="h-5 w-5" />
            </button>
          </header>

          <main className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
            {mensagens.map((m) => (
              <ChatMessage key={m.id} role={m.role} content={m.content} />
            ))}
            {carregando && <TypingIndicator />}
            <div ref={fimDaListaRef} />
          </main>

          <ChatInput
            value={texto}
            onChange={setTexto}
            onSend={handleEnviar}
            disabled={carregando}
          />
        </div>
      )}

      <button
        type="button"
        onClick={() => (aberto ? fecharChat() : abrirChat())}
        aria-label={aberto ? "Fechar chat" : "Falar com a Bia"}
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-violet-700 text-white shadow-lg shadow-violet-600/30 transition hover:scale-105 active:scale-95"
      >
        {aberto ? (
          <IconClose className="h-6 w-6" />
        ) : (
          <IconChat className="h-6 w-6" />
        )}
        {!aberto && naoLidas > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-xs font-bold text-white ring-2 ring-white dark:ring-slate-950">
            {naoLidas}
          </span>
        )}
      </button>
    </>
  );
}
