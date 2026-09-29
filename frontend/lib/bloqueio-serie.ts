export type BloqueioDia = {
  id: number;
  professional: number | null;
  motivo: string;
  data_inicio: string;
  data_fim: string;
};

export type BloqueioSelecionado = {
  id: number;
  motivo: string;
  professional_name: string;
  diaInteiro: boolean;
  idsSerie: number[];
  de: string;
  ate: string;
};

function ymdLocal(iso: string): string | null {
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return null;
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function diaSeguinte(ymd: string): string {
  const [ano, mes, dia] = ymd.split("-").map(Number);
  const data = new Date(ano, (mes || 1) - 1, dia || 1);
  data.setDate(data.getDate() + 1);
  const m = String(data.getMonth() + 1).padStart(2, "0");
  const d = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${m}-${d}`;
}

export function formatarDiaBloqueio(iso: string): string {
  const ymd = ymdLocal(iso);
  if (!ymd) return "";
  const [ano, mes, dia] = ymd.split("-");
  return `${dia}/${mes}/${ano}`;
}

/** Dia gravado de 00:00 até o fim do expediente, não um horário curto. */
export function ehBloqueioDiaInteiro(inicio: string, fim: string): boolean {
  const start = new Date(inicio);
  const end = new Date(fim);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return false;
  const mesmoDia =
    start.getFullYear() === end.getFullYear() &&
    start.getMonth() === end.getMonth() &&
    start.getDate() === end.getDate();
  if (!mesmoDia) return false;
  return (end.getTime() - start.getTime()) / 60000 >= 20 * 60;
}

/** Dias seguidos, do mesmo profissional e do mesmo motivo, em volta do bloqueio clicado. */
export function serieBloqueioDiaInteiro(bloqueios: BloqueioDia[], id: number): BloqueioDia[] {
  const atual = bloqueios.find((b) => b.id === id);
  if (!atual || !ehBloqueioDiaInteiro(atual.data_inicio, atual.data_fim)) {
    return atual ? [atual] : [];
  }
  const porDia = new Map<string, BloqueioDia>();
  for (const bloqueio of bloqueios) {
    if (bloqueio.professional !== atual.professional || bloqueio.motivo !== atual.motivo) continue;
    if (!ehBloqueioDiaInteiro(bloqueio.data_inicio, bloqueio.data_fim)) continue;
    const dia = ymdLocal(bloqueio.data_inicio);
    if (dia) porDia.set(dia, bloqueio);
  }
  const dias = [...porDia.keys()].sort();
  const diaAtual = ymdLocal(atual.data_inicio);
  const indice = diaAtual ? dias.indexOf(diaAtual) : -1;
  if (indice < 0) return [atual];
  let inicio = indice;
  let fim = indice;
  while (inicio > 0 && diaSeguinte(dias[inicio - 1]) === dias[inicio]) inicio -= 1;
  while (fim < dias.length - 1 && diaSeguinte(dias[fim]) === dias[fim + 1]) fim += 1;
  return dias.slice(inicio, fim + 1).map((dia) => porDia.get(dia)!);
}
