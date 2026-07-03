import { procedureCategoria } from "@/lib/clinica-beleza-entities";
import { procedureMatchesModule } from "@/lib/clinica-beleza-categories";
import type {
  Protocol,
  ProtocoloFormState,
  ProtocoloProcedureOption,
} from "./protocolos-page-types";

export function buildProtocolosListPath(defaultCategoria: string): string {
  return defaultCategoria
    ? `/protocolos?categoria=${encodeURIComponent(defaultCategoria)}`
    : "/protocolos";
}

export function filterProceduresByModule(
  procedures: ProtocoloProcedureOption[],
  defaultCategoria: string,
): ProtocoloProcedureOption[] {
  if (!defaultCategoria) return procedures;
  return procedures.filter((p) =>
    procedureMatchesModule(procedureCategoria(p), defaultCategoria),
  );
}

export function protocolToForm(p: Protocol): ProtocoloFormState {
  return {
    nome: p.nome || "",
    procedure: String(p.procedure),
    descricao: p.descricao || "",
    tempo_estimado: String(p.tempo_estimado || 30),
    materiais_necessarios: p.materiais_necessarios || "",
    preparacao: p.preparacao || "",
    execucao: p.execucao || "",
    pos_procedimento: p.pos_procedimento || "",
    contraindicacoes: p.contraindicacoes || "",
    cuidados_especiais: p.cuidados_especiais || "",
  };
}

export function validateProtocoloForm(form: ProtocoloFormState): string | null {
  if (!form.nome.trim() || !form.procedure) {
    return "Nome e procedimento são obrigatórios.";
  }
  return null;
}

export function buildProtocoloSaveBody(form: ProtocoloFormState): Record<string, unknown> {
  return {
    nome: form.nome.trim(),
    procedure: Number(form.procedure),
    descricao: form.descricao.trim(),
    tempo_estimado: Number(form.tempo_estimado) || 30,
    materiais_necessarios: form.materiais_necessarios.trim(),
    preparacao: form.preparacao.trim(),
    execucao: form.execucao.trim(),
    pos_procedimento: form.pos_procedimento.trim(),
    contraindicacoes: form.contraindicacoes.trim(),
    cuidados_especiais: form.cuidados_especiais.trim(),
  };
}

export function extractProtocoloSaveError(e: unknown, fallback = "Erro ao salvar protocolo."): string {
  if (e instanceof Error && e.message === "SESSION_ENDED") return "SESSION_ENDED";
  if (e && typeof e === "object" && "error" in e && typeof (e as { error?: string }).error === "string") {
    return (e as { error: string }).error;
  }
  return fallback;
}
