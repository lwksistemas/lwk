import { formatApiErrorBody } from "@/lib/api-errors";

export function mapSubmitValidationError(message: string): string {
  return message.replace("cliente", "paciente");
}

export function buildQuickPatientBody(data: {
  nome: string;
  telefone: string;
  cpf: string;
}): Record<string, string> {
  const body: Record<string, string> = { nome: data.nome };
  if (data.telefone) body.telefone = data.telefone.replace(/\D/g, "");
  if (data.cpf) body.cpf = data.cpf.replace(/\D/g, "");
  return body;
}

export function extractCriarAgendamentoSubmitError(err: unknown, isConsulta: boolean): string {
  const apiMsg =
    err && typeof err === "object" && "error" in err && typeof (err as { error?: unknown }).error === "string"
      ? (err as { error: string }).error
      : null;
  return (
    apiMsg ||
    (err instanceof Error ? err.message : null) ||
    (isConsulta ? "Erro ao abrir consulta" : "Erro ao criar agendamento")
  );
}

export function extractQuickPatientError(err: unknown): string {
  if (err && typeof err === "object") {
    return formatApiErrorBody(err) || "Erro ao cadastrar paciente";
  }
  if (err instanceof Error) return err.message;
  return "Erro ao cadastrar paciente";
}

export const CRIAR_AGENDAMENTO_DEFAULT_TIME = "09:00";

export const CRIAR_AGENDAMENTO_OFFLINE_SAVE_ERROR = "Sem conexão. Não foi possível salvar offline.";
