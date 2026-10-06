import { IconBuilding, IconHouse } from "../components/icons";

const TIPOS = {
  apartamento: {
    label: "Apartamento",
    icone: IconBuilding,
    gradiente: "from-violet-500 to-indigo-600",
  },
  casa: {
    label: "Casa",
    icone: IconHouse,
    gradiente: "from-emerald-500 to-teal-600",
  },
  sobrado: {
    label: "Sobrado",
    icone: IconHouse,
    gradiente: "from-amber-500 to-orange-600",
  },
  cobertura: {
    label: "Cobertura",
    icone: IconBuilding,
    gradiente: "from-sky-500 to-blue-700",
  },
  studio: {
    label: "Studio",
    icone: IconBuilding,
    gradiente: "from-pink-500 to-rose-600",
  },
  loft: {
    label: "Loft",
    icone: IconBuilding,
    gradiente: "from-slate-500 to-slate-700",
  },
};

const TIPO_PADRAO = {
  label: "Imóvel",
  icone: IconHouse,
  gradiente: "from-violet-500 to-violet-700",
};

export function infoTipo(tipo) {
  return TIPOS[tipo] ?? { ...TIPO_PADRAO, label: tipo || TIPO_PADRAO.label };
}

export const LABEL_FINALIDADE = {
  compra: "Venda",
  aluguel: "Aluguel",
};

// --- Leads (dashboard) -------------------------------------------------

export const LABEL_INTENCAO = {
  compra: "Compra",
  aluguel: "Aluguel",
  investimento: "Investimento",
  indefinida: "Indefinida",
};

export const LABEL_STATUS_LEAD = {
  novo: "Novo",
  em_qualificacao: "Em qualificação",
  qualificado: "Qualificado",
  em_followup: "Em follow-up",
  agendado: "Agendado",
  inativo: "Inativo",
  perdido: "Perdido",
};

export const LABEL_TIPO_AGENDAMENTO = {
  visita_imovel: "Visita ao imóvel",
  reuniao_corretor: "Reunião com corretor",
  reuniao_especialista: "Reunião com especialista",
};

export const LABEL_CAMPO_LEAD = {
  intencao: "Intenção",
  regiao: "Região",
  preco_max: "Orçamento",
  quartos_min: "Quartos",
  urgencia: "Urgência",
  perfil_cliente: "Perfil",
  ticket_investimento: "Ticket",
  expectativa_retorno: "Retorno esperado",
};

// Ordem fixa quente → morno → frio. Cores = slots 2, 3 e 1 da paleta
// categórica de referência (os três primeiros slots passam na validação
// de daltonismo entre todos os pares), em passos próprios para o modo escuro.
export const TEMPERATURAS = [
  {
    chave: "quente",
    label: "Quente",
    cor: "bg-[#eb6834] dark:bg-[#d95926]",
  },
  {
    chave: "morno",
    label: "Morno",
    cor: "bg-[#1baf7a] dark:bg-[#199e70]",
  },
  {
    chave: "frio",
    label: "Frio",
    cor: "bg-[#2a78d6] dark:bg-[#3987e5]",
  },
];
