import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";

export type VerificarDisponibilidadeInput = {
  professionalId: number;
  date: Date;
  durationMinutes: number;
  procedureIds?: number[];
  localAtendimentoId?: number | "";
};

export type VerificarDisponibilidadeResult = {
  disponivel: boolean;
  error?: string;
};

/** Confere conflitos/bloqueios/expediente na janela completa (duração prevista). */
export async function verificarDisponibilidadeAgendamento(
  input: VerificarDisponibilidadeInput,
): Promise<VerificarDisponibilidadeResult> {
  const res = await clinicaBelezaFetch("/agenda/verificar-disponibilidade/", {
    method: "POST",
    body: JSON.stringify({
      professional: input.professionalId,
      date: input.date.toISOString(),
      duration_minutes: input.durationMinutes,
      procedure_ids: input.procedureIds ?? [],
      local_atendimento: input.localAtendimentoId || undefined,
    }),
  });
  const data = (await res.json().catch(() => ({}))) as {
    disponivel?: boolean;
    error?: string;
  };
  if (!res.ok) {
    return {
      disponivel: false,
      error: data.error || "Não foi possível verificar a disponibilidade.",
    };
  }
  if (data.disponivel === false) {
    return { disponivel: false, error: data.error || "Horário indisponível." };
  }
  return { disponivel: true };
}
