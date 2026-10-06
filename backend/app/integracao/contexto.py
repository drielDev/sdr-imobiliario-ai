from contextvars import ContextVar

# Sessão de chat que está sendo atendida no momento. O Gemini chama as
# ferramentas só com os argumentos que ele mesmo preenche, então é por
# aqui que as ferramentas de lead/agenda descobrem de qual cliente se trata.
sessao_atual: ContextVar[str | None] = ContextVar("sessao_atual", default=None)
