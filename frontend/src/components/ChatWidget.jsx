import { useEffect, useRef, useState } from "react";
import { useChatWidget } from "../context/ChatContext";
import { enviarMensagem } from "../lib/api";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import { IconChat, IconClose, IconExpand, IconShrink } from "./icons";
import TypingIndicator from "./TypingIndicator";

const MENSAGEM_BOAS_VINDAS = {
  id: "boas-vindas",
  role: "assistant",
  content:
    "Olá! Eu sou a **Bia**, assistente virtual de imóveis. 🏠\n\nMe conta o que você procura: quer **comprar**, **alugar** ou está pensando em **investir**?",
};

function criarId() {
  return crypto.randomUUID();
}

export default function ChatWidget() {
  const { aberto, abrirChat, fecharChat, rascunho, consumirRascunho } =
    useChatWidget();

  const [sessaoId] = useState(criarId);
  const [mensagens, setMensagens] = useState([MENSAGEM_BOAS_VINDAS]);
  const [texto, setTexto] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [expandido, setExpandido] = useState(false);
  const fimDaListaRef = useRef(null);

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
      </button>
    </>
  );
}
