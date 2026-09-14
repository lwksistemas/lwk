import type { NomeAgendaItem } from "@/lib/clinica-beleza-api";

export const TIPO_AGENDA_CONSULTA = "CONSULTA";
export const TIPO_AGENDA_RETORNO = "RETORNO";

export function normalizarTipoAgendaNome(nome: string): string {
  return (nome || "").trim().toUpperCase();
}

export function isTipoAgendaSistema(nome: string): boolean {
  const n = normalizarTipoAgendaNome(nome);
  return n === TIPO_AGENDA_CONSULTA || n === TIPO_AGENDA_RETORNO;
}

export function findNomeAgendaByTipo(
  items: NomeAgendaItem[],
  tipo: string,
): NomeAgendaItem | undefined {
  const wanted = normalizarTipoAgendaNome(tipo);
  return items.find((n) => normalizarTipoAgendaNome(n.nome) === wanted);
}

export function sortTiposAgenda(items: NomeAgendaItem[]): NomeAgendaItem[] {
  const rank = (nome: string) => {
    const n = normalizarTipoAgendaNome(nome);
    if (n === TIPO_AGENDA_CONSULTA) return 0;
    if (n === TIPO_AGENDA_RETORNO) return 1;
    return 2;
  };
  return [...items].sort(
    (a, b) => rank(a.nome) - rank(b.nome) || a.nome.localeCompare(b.nome, "pt-BR"),
  );
}
