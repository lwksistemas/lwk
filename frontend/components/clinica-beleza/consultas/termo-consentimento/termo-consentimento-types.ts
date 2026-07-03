export type TermoProcedimento = {
  id: number;
  procedure_id: number;
  procedure_nome: string;
  status: string;
  status_display: string;
  tem_conteudo: boolean;
};

export type TermoConsentimentoCanal = "email" | "whatsapp";

export const TERMO_STATUS_BADGE: Record<string, string> = {
  rascunho: "bg-gray-100 text-gray-600 dark:bg-neutral-700 dark:text-gray-300",
  aguardando_paciente: "bg-amber-50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200",
  aguardando_profissional: "bg-blue-50 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200",
  concluido: "bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-200",
};

export function snapshotTermoStatus(lista: TermoProcedimento[]): string {
  return lista.map((t) => `${t.procedure_id}:${t.status}`).join("|");
}

export function extrairErroTermo(e: unknown, fallback = "Erro ao enviar."): string {
  if (e && typeof e === "object" && "detail" in e) {
    return String((e as { detail: string }).detail);
  }
  if (e instanceof Error) return e.message;
  return fallback;
}

export function labelCanalTermo(canal: TermoConsentimentoCanal): string {
  return canal === "whatsapp" ? "WhatsApp" : "e-mail";
}
