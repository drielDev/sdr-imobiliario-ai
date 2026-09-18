# SDR Imobiliário AI

## Visão Geral

Projeto de POC para um Agente SDR Imobiliário com IA Generativa. A solução cobre catálogo de imóveis, busca estruturada, busca semântica com RAG, um agente de chat (Bia) com LLM via Gemini, e exposição via API FastAPI + interface web em React.

## Arquitetura da Solução

```mermaid
flowchart LR
    A[data/imoveis.json] --> B[ImovelRepository]
    B --> C[CatalogoService]
    B --> D[ImovelRAG]
    D --> E[Chroma / chroma_db]
    C --> T1[buscar_imoveis_estruturado]
    D --> T2[buscar_imoveis_semantico]
    T1 --> AG[AgenteSDR / Gemini]
    T2 --> AG
    AG --> CH[Endpoint /chat]
    D --> F[Endpoints /imoveis/rag]
    C --> G[Endpoints /imoveis/buscar]
    G --> H[FastAPI / docs]
    F --> H
    CH --> H
    H --> FE[Frontend React]
```

### Componentes

- [backend/data/imoveis.json](backend/data/imoveis.json): base simulada de imóveis.
- [backend/app/catalogo/models.py](backend/app/catalogo/models.py): modelos de domínio e payloads de busca.
- [backend/app/catalogo/repository.py](backend/app/catalogo/repository.py): leitura da base de dados.
- [backend/app/catalogo/service.py](backend/app/catalogo/service.py): filtros estruturados e regras de negócio.
- [backend/app/catalogo/rag.py](backend/app/catalogo/rag.py): geração de documentos, embeddings, indexação e reranking.
- [backend/app/catalogo/instancias.py](backend/app/catalogo/instancias.py): instâncias únicas do serviço de catálogo e do RAG, compartilhadas entre API e agente.
- [backend/app/api/imoveis.py](backend/app/api/imoveis.py): endpoints do catálogo.
- [backend/app/agente/agente.py](backend/app/agente/agente.py): `AgenteSDR`, sessão de chat por cliente usando o SDK do Gemini (`google-genai`).
- [backend/app/agente/prompts.py](backend/app/agente/prompts.py): system prompt da Bia (persona, tom de voz, regras de negócio).
- [backend/app/agente/tools.py](backend/app/agente/tools.py): ferramentas (function calling) que o Gemini pode acionar para consultar o catálogo, estruturado ou semântico.
- [backend/app/api/chat.py](backend/app/api/chat.py): endpoints do chat.
- [backend/app/qualificacao/](backend/app/qualificacao/): qualificação de leads, classificação, agendamento, follow-up e resumo para o corretor (ver seção própria abaixo).
- [backend/app/api/leads.py](backend/app/api/leads.py): endpoints de leads, agendamento e follow-up.
- [frontend/src/components/ChatWidget.jsx](frontend/src/components/ChatWidget.jsx): widget de chat flutuante que conversa com a Bia.

## Agente de Chat (LLM)

A Bia é o agente conversacional do projeto: um SDR virtual que atende pelo chat, entende o que o cliente procura e busca imóveis reais do catálogo para responder.

- **Modelo**: Google Gemini (`gemini-2.5-flash` por padrão), via SDK `google-genai`.
- **Contexto**: cada `sessao_id` mantém sua própria sessão de chat em memória (`AgenteSDR._sessoes`), preservando o histórico da conversa entre mensagens.
- **Function calling**: o modelo decide sozinho quando chamar `buscar_imoveis_estruturado` (critérios exatos: finalidade, tipo, cidade, bairro, preço, quartos, vagas) ou `buscar_imoveis_semantico` (pedidos vagos/descritivos, usa o pipeline de RAG).
- **Regras de negócio**: o prompt (`prompts.py`) proíbe o modelo de inventar imóveis, preços ou características — só pode descrever o que as ferramentas retornaram na conversa.

### Configuração

Crie um arquivo `.env` em `backend/` com:

```
GEMINI_API_KEY=sua_chave_da_api_do_gemini
GEMINI_MODEL=gemini-2.5-flash
```

Sem `GEMINI_API_KEY`, os endpoints de chat respondem `503`.

### Endpoints do chat

- `POST /chat/`: envia uma mensagem (`sessao_id`, `mensagem`) e recebe a resposta da Bia.
- `GET /chat/{sessao_id}/historico`: retorna o histórico da sessão.
- `POST /chat/{sessao_id}/reiniciar`: descarta o contexto da sessão.

Também é possível conversar com a Bia direto pelo terminal:

```
cd backend
python scripts/chat_cli.py
```

## Fluxo do Pipeline RAG

1. Carrega os imóveis do JSON.
2. Monta documentos ricos com título, bairro, preço, finalidade, quartos e descrição.
3. Gera embeddings com `BAAI/bge-m3`.
4. Armazena os vetores no Chroma (`chroma_db`).
5. Executa busca vetorial, filtros estruturados e reranking.
6. Retorna a resposta em JSON.

## Executando o projeto

Backend e frontend ficam em pastas separadas: `backend/` e `frontend/`.

### Backend

### 1. Entrar na pasta

cd backend

### 2. Criar ambiente virtual

python -m venv .venv

### 3. Ativar

Windows:

.venv\Scripts\activate

### 4. Instalar dependências

pip install -r requirements.txt

### 5. Rodar API

uvicorn app.main:app --reload

### 6. Documentação

http://localhost:8000/docs

### 7. Indexar a base de imóveis

python scripts/indexar_imoveis.py

Para reindexar do zero:

python scripts/indexar_imoveis.py --reindexar

Para indexar sem a validação final:

python scripts/indexar_imoveis.py --sem-validacao

### Frontend

cd frontend
npm install
npm run dev


# Catálogo de imóveis

## Listar imóveis

GET /imoveis/

Resposta: lista de imóveis disponíveis na base.

## Buscar imóvel

GET /imoveis/{imovel_id}

Retorna um imóvel específico pelo ID ou 404 se não existir.

## Buscar imóveis com filtros

POST /imoveis/buscar

Exemplo:

```json
{
    "finalidade": "compra",
    "tipo": "apartamento",
    "bairro": "Moema",
    "preco_max": 800000,
    "quartos_min": 2
}
```

## Busca semântica / RAG

POST /imoveis/rag

Exemplo:

```json
{
        "consulta": "imóvel moderno para investimento",
        "limite": 3
}
```

Exemplo com filtros estruturados:

```json
{
        "consulta": "imóvel para família com muitos quartos",
        "limite": 3,
        "filtros": {
                "quartos_min": 3,
                "finalidade": "compra"
        }
}
```

### Resposta do RAG

```json
{
    "consulta": "imóvel moderno para investimento",
    "quantidade": 3,
    "resultados": [
        {
            "imovel_id": 4,
            "titulo": "Casa residencial no Morumbi",
            "finalidade": "compra",
            "quartos": 4,
            "preco": 1200000,
            "conteudo": "..."
        }
    ]
}
```

## Pipeline de Dados

- A base de imóveis fica em `backend/data/imoveis.json`.
- O repositório carrega os dados e transforma cada item em um modelo `Imovel`.
- O RAG converte imóveis em documentos de contexto para a busca semântica.
- O Chroma persiste os embeddings localmente em `chroma_db`.

## Qualidade da Busca

- Busca estruturada por finalidade, tipo, cidade, bairro, preço, quartos e vagas.
- Busca semântica com embeddings.
- Reranking para melhorar a relevância dos resultados.
- Dedução de intenção em consultas como "família com muitos quartos".

## Demonstração

Para validar a busca semântica fora da API, execute:

cd backend
python teste_rag.py

O script imprime a resposta em JSON.

# Qualificação de Leads (Qualificação + Automação)

Módulo responsável pela lógica comercial do SDR: o que perguntar a seguir,
como classificar o lead (quente/morno/frio), agendamento de reuniões/visitas,
follow-up de leads inativos e o resumo estruturado para o corretor.

Fica isolado em [backend/app/qualificacao/](backend/app/qualificacao/) e é
consumido pelos outros módulos via funções/serviços — sem acoplamento com
prompt/LLM (Pessoa 1), catálogo/RAG (Pessoa 2) ou interface (Pessoa 4).

## Responsabilidades

- **Modelo do lead e qualificação** ([models.py](backend/app/qualificacao/models.py), [campos.py](backend/app/qualificacao/campos.py), [qualificacao.py](backend/app/qualificacao/qualificacao.py)): entidade `Lead`, campos obrigatórios por intenção (declarados em [config.py](backend/app/qualificacao/config.py)), cálculo do próximo campo a perguntar e merge de dados extraídos sem apagar histórico.
- **Classificação** ([classificacao.py](backend/app/qualificacao/classificacao.py)): pontuação explicável (urgência, completude dos dados, faixa de valor definida, intenção clara, engajamento recente, penalidade por follow-up sem resposta) que resulta em quente/morno/frio + motivos.
- **Agendamento** ([agendamento.py](backend/app/qualificacao/agendamento.py)): agenda simulada de slots (corretor/especialista), sem conflito de horário, com roteamento automático (lead de investimento → especialista; lead com imóvel de interesse → visita; demais → corretor).
- **Follow-up** ([followup.py](backend/app/qualificacao/followup.py)): identifica leads elegíveis para a próxima tentativa (intervalos e número máximo configuráveis), templates de mensagem por tentativa, e encerra (inativa) o lead ao esgotar as tentativas.
- **Resumo para o corretor** ([resumo.py](backend/app/qualificacao/resumo.py)): resumo estruturado determinístico (sem depender de LLM), com ponto de extensão opcional para enriquecer com um cliente LLM injetado.

## Interfaces públicas (o que outros módulos chamam)

**Pessoa 1 (Agente/LLM)** — depois de extrair dados da conversa, envia um
`DadosExtraidosLead` (todos os campos opcionais) para atualizar o lead, e usa
`campos_faltantes`/`proximo_campo_prioritario` para saber o que perguntar a
seguir (a frase da pergunta é responsabilidade dela, não deste módulo):

```python
from app.qualificacao.qualificacao import criar_lead, atualizar_lead
from app.qualificacao.campos import proximo_campo_prioritario
from app.qualificacao.models import DadosExtraidosLead
from app.qualificacao.instancias import lead_repository, relogio

lead = criar_lead(lead_repository, lead_id, canal="whatsapp", contato="+55...", relogio=relogio)

lead = atualizar_lead(
    lead_repository,
    lead_id,
    DadosExtraidosLead(intencao="compra", regiao="Moema"),
    relogio=relogio,
)

proximo_campo_prioritario(lead)  # -> "preco_max", por exemplo, ou None se já está tudo
```

**Pessoa 2 (Imóveis + RAG)** — nenhuma dependência direta. O lead só guarda
`imovel_interesse_id` (um `int`), sem validar contra o catálogo.

**Pessoa 4 (Interface + integração)** — pode chamar os serviços Python
diretamente (mesmo processo) ou usar a API REST em `/leads` (registrada em
`main.py`, mesmo padrão de `/imoveis` e `/chat`):

- `POST /leads/` — cria lead (`canal`, `contato`, `id` opcional).
- `GET /leads/` — lista leads. `GET /leads/{id}` — obtém um lead.
- `PATCH /leads/{id}` — atualiza com `DadosExtraidosLead`.
- `GET /leads/{id}/proximo-campo` — próximo campo a perguntar + campos faltantes.
- `GET /leads/{id}/classificacao` — reclassifica e retorna temperatura + motivos.
- `GET /leads/{id}/resumo` — resumo estruturado para o corretor.
- `GET /leads/agendamentos/slots?tipo=` — slots disponíveis.
- `POST /leads/{id}/agendamentos` — agenda (`slot_id`, `tipo` opcional, `imovel_id` opcional).
- `PATCH /leads/agendamentos/{id}/reagendar` — reagenda (`novo_slot_id`).
- `DELETE /leads/agendamentos/{id}` — cancela.
- `GET /leads/followup/elegiveis` — leads elegíveis agora + estratégia sugerida.
- `POST /leads/{id}/followup/tentativa` — registra que uma tentativa foi enviada.

Para o **follow-up** especificamente, este módulo **não envia mensagem nem
tem cron/job**: só decide quem e o quê. A Pessoa 4 implementa o Protocol
`CanalNotificacao` (método `enviar(lead, mensagem)`) e decide de onde e com
que frequência chamar `FollowUpService.leads_elegiveis_agora()` /
`executar_followup(...)`:

```python
from app.qualificacao.instancias import followup_service

class MeuCanalWhatsApp:
    def enviar(self, lead, mensagem: str) -> None:
        ...  # integração real da Pessoa 4

for estrategia in followup_service.leads_elegiveis_agora():
    followup_service.executar_followup(estrategia.lead_id, MeuCanalWhatsApp())
```

## Pontos de extensão opcionais

- `GeradorTextoFollowUp` (em `followup.py`): plugar geração de texto via LLM no lugar do template padrão.
- `EnriquecedorLLM` (em `resumo.py`): plugar um cliente LLM para preencher `pontos_relevantes` no resumo.
- `Relogio` (em `tempo.py`): fonte de tempo injetável, usada em todo o módulo para permitir testar follow-up/agendamento sem esperar tempo real.
- `LeadRepository` / `AgendaRepository`: Protocols de persistência — a implementação padrão é em memória (`InMemoryLeadRepository`, `InMemoryAgendaRepository`); podem ser trocadas por um repositório real sem mudar a lógica de negócio.

## Configuração

Toda a configuração é declarativa em
[backend/app/qualificacao/config.py](backend/app/qualificacao/config.py):
campos obrigatórios por intenção, pesos de classificação, intervalos e número
máximo de tentativas de follow-up, templates de mensagem, e parâmetros da
agenda simulada (duração do slot, dias úteis gerados, horário comercial). Não
depende de nenhuma variável de ambiente nova.

## Rodando os testes

cd backend
python -m pytest tests/test_qualificacao.py tests/test_classificacao.py tests/test_agendamento.py tests/test_followup.py tests/test_resumo.py -v

Os testes cobrem os três cenários da proposta (compra, investimento,
follow-up) e casos de borda: dado contraditório, lead que volta a responder,
conflito de agenda e tentativas de follow-up esgotadas. Usam um relógio falso
injetado (sem depender de `sleep`/tempo real).