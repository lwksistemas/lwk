export const DIAS_SEMANA = [
  { value: 0, label: "Segunda-feira" },
  { value: 1, label: "Terça-feira" },
  { value: 2, label: "Quarta-feira" },
  { value: 3, label: "Quinta-feira" },
  { value: 4, label: "Sexta-feira" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
] as const;

export interface HorarioTrabalhoItem {
  id?: number;
  dia_semana: number;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio: string | null;
  intervalo_fim: string | null;
  ativo: boolean;
}

export function createDefaultHorarioRows(): Record<number, HorarioTrabalhoItem> {
  const initial: Record<number, HorarioTrabalhoItem> = {};
  DIAS_SEMANA.forEach((d) => {
    initial[d.value] = {
      dia_semana: d.value,
      hora_entrada: "08:00",
      hora_saida: "18:00",
      intervalo_inicio: "12:00",
      intervalo_fim: "13:00",
      ativo: d.value < 5,
    };
  });
  return initial;
}

export function mergeHorariosFromApi(data: HorarioTrabalhoItem[]): Record<number, HorarioTrabalhoItem> {
  const byDay = createDefaultHorarioRows();
  DIAS_SEMANA.forEach((d) => {
    byDay[d.value].ativo = false;
  });
  (Array.isArray(data) ? data : []).forEach((h) => {
    const day = Number(h.dia_semana);
    if (day in byDay) {
      byDay[day] = {
        id: h.id,
        dia_semana: day,
        hora_entrada: typeof h.hora_entrada === "string" ? h.hora_entrada.slice(0, 5) : "08:00",
        hora_saida: typeof h.hora_saida === "string" ? h.hora_saida.slice(0, 5) : "18:00",
        intervalo_inicio: h.intervalo_inicio ? String(h.intervalo_inicio).slice(0, 5) : null,
        intervalo_fim: h.intervalo_fim ? String(h.intervalo_fim).slice(0, 5) : null,
        ativo: h.ativo !== false,
      };
    }
  });
  return byDay;
}

export function buildHorariosSavePayload(rows: Record<number, HorarioTrabalhoItem>) {
  return DIAS_SEMANA.filter((d) => rows[d.value].ativo).map((d) => {
    const r = rows[d.value];
    return {
      dia_semana: r.dia_semana,
      hora_entrada: r.hora_entrada,
      hora_saida: r.hora_saida,
      intervalo_inicio: r.intervalo_inicio || null,
      intervalo_fim: r.intervalo_fim || null,
      ativo: true,
    };
  });
}
