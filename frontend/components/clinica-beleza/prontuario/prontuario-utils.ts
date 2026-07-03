import type {
  ProntuarioAnamneseItem,
  ProntuarioData,
  ProntuarioDocItem,
  ProntuarioEvolucaoItem,
} from "@/lib/clinica-beleza-api";
import { ANAMNESE_DISPLAY_FIELDS } from "./prontuario-types";
import type { ProntuarioDocTabId, ProntuarioTabId } from "./prontuario-types";

export function isProntuarioDocTab(tab: ProntuarioTabId): tab is ProntuarioDocTabId {
  return tab !== "anamnese" && tab !== "evolucao";
}

export function getProntuarioDocsForTab(
  data: ProntuarioData,
  tab: ProntuarioDocTabId,
): ProntuarioDocItem[] {
  return data[tab] || [];
}

export function formatProntuarioDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export function prontuarioTipoLabel(tipo: string): string {
  const labels: Record<string, string> = {
    receituario: "Receituário",
    pedido_exame: "Pedido de Exame",
    atestado: "Atestado",
    documento_personalizado: "Documento",
  };
  return labels[tipo] || tipo;
}

export function resolvePatientDisplayName(patient: { name?: string; nome?: string }): string {
  return patient.name || patient.nome || "Paciente";
}

export function extractAnamneseDisplayFields(anamnese: ProntuarioAnamneseItem | null | undefined) {
  if (!anamnese) return [];
  return ANAMNESE_DISPLAY_FIELDS.map(({ key, label }) => ({
    label,
    value: anamnese[key],
  })).filter((f) => f.value);
}

export function extractEvolucaoDisplayFields(evo: ProntuarioEvolucaoItem) {
  return [
    { label: "Descrição", value: evo.descricao },
    { label: "Procedimento Realizado", value: evo.procedimento_realizado },
    { label: "Produtos Utilizados", value: evo.produtos_utilizados },
    { label: "Orientações", value: evo.orientacoes },
  ].filter((f) => f.value);
}

export function documentoCardKey(doc: ProntuarioDocItem): string {
  return `${doc.source}-${doc.id}`;
}
