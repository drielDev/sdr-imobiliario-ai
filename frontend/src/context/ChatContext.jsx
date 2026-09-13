import { createContext, useContext, useState } from "react";

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [aberto, setAberto] = useState(false);
  const [rascunho, setRascunho] = useState(null);

  function abrirChat(mensagemInicial) {
    if (mensagemInicial) {
      setRascunho(mensagemInicial);
    }
    setAberto(true);
  }

  function fecharChat() {
    setAberto(false);
  }

  function consumirRascunho() {
    const valor = rascunho;
    setRascunho(null);
    return valor;
  }

  return (
    <ChatContext.Provider
      value={{ aberto, abrirChat, fecharChat, rascunho, consumirRascunho }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChatWidget() {
  const contexto = useContext(ChatContext);

  if (!contexto) {
    throw new Error("useChatWidget precisa estar dentro de <ChatProvider>");
  }

  return contexto;
}
