import ReactMarkdown from "react-markdown";

const ESTILOS_MARKDOWN = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => (
    <ul className="mb-2 ml-4 list-disc space-y-1 last:mb-0">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-2 ml-4 list-decimal space-y-1 last:mb-0">{children}</ol>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold">{children}</strong>
  ),
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="underline underline-offset-2"
    >
      {children}
    </a>
  ),
};

export default function ChatMessage({ role, content }) {
  const isUsuario = role === "user";
  const isErro = role === "error";

  return (
    <div className={`flex ${isUsuario ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed shadow-sm sm:max-w-[70%] ${
          isUsuario
            ? "rounded-br-sm bg-violet-600 text-white"
            : isErro
              ? "rounded-bl-sm border border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300"
              : "rounded-bl-sm bg-white text-slate-800 shadow-slate-200/60 dark:bg-slate-800 dark:text-slate-100 dark:shadow-none"
        }`}
      >
        {isUsuario ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <ReactMarkdown components={ESTILOS_MARKDOWN}>
            {content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}
