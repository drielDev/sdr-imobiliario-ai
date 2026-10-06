const FORMATO_PRECO = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});

const FORMATO_DATA_HORA = new Intl.DateTimeFormat("pt-BR", {
  weekday: "short",
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatarPreco(valor) {
  if (valor === null || valor === undefined) return "—";
  return FORMATO_PRECO.format(valor);
}

export function formatarArea(areaM2) {
  if (areaM2 === null || areaM2 === undefined) return "—";
  return `${Number(areaM2).toLocaleString("pt-BR")} m²`;
}

export function formatarDataHora(iso) {
  if (!iso) return "—";
  return FORMATO_DATA_HORA.format(new Date(iso));
}

export function formatarTempoRelativo(iso) {
  if (!iso) return "—";

  const minutos = Math.round((Date.now() - new Date(iso).getTime()) / 60000);

  if (minutos < 1) return "agora";
  if (minutos < 60) return `há ${minutos} min`;

  const horas = Math.round(minutos / 60);
  if (horas < 24) return `há ${horas} h`;

  const dias = Math.round(horas / 24);
  return `há ${dias} dia${dias > 1 ? "s" : ""}`;
}
