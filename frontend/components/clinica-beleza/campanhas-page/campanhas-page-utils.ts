import { formatClinicaDataCurta, formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import type { Campanha, CampanhaFormState } from "./campanhas-page-types";

export function campanhaToForm(c: Campanha): CampanhaFormState {
  return {
    titulo: c.titulo,
    mensagem: c.mensagem,
    data_inicio: c.data_inicio ? c.data_inicio.slice(0, 10) : "",
    data_fim: c.data_fim ? c.data_fim.slice(0, 10) : "",
    ativa: c.ativa,
  };
}

export function validateCampanhaForm(form: CampanhaFormState): string | null {
  if (!form.titulo.trim() || !form.mensagem.trim()) {
    return "Título e mensagem são obrigatórios.";
  }
  return null;
}

export function buildCampanhaSaveBody(form: CampanhaFormState): Record<string, unknown> {
  return {
    titulo: form.titulo.trim(),
    mensagem: form.mensagem.trim(),
    data_inicio: form.data_inicio || null,
    data_fim: form.data_fim || null,
    ativa: form.ativa,
  };
}

export function extractCampanhaSaveError(e: unknown, fallback: string): string {
  if (e instanceof Error && e.message === "SESSION_ENDED") return "SESSION_ENDED";
  if (e && typeof e === "object" && "error" in e && typeof (e as { error?: string }).error === "string") {
    return (e as { error: string }).error;
  }
  return e instanceof Error ? e.message : fallback;
}

export function formatCampanhaVigencia(c: Campanha): string {
  const inicio = c.data_inicio ? formatClinicaDataCurta(new Date(c.data_inicio)) : "—";
  const fim = c.data_fim ? ` → ${formatClinicaDataCurta(new Date(c.data_fim))}` : "";
  return `${inicio}${fim}`;
}

export function formatCampanhaEnvio(c: Campanha): string {
  if (!c.enviada_em) return "Não enviada";
  return `${formatClinicaDateTime(new Date(c.enviada_em))} · ${c.total_enviados} pac.`;
}

export function campanhaFoiEnviada(c: Campanha): boolean {
  return !!c.enviada_em;
}
