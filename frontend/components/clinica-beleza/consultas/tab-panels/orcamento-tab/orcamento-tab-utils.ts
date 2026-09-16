export const STATUS_LABEL: Record<string, string> = {
  RASCUNHO: "Rascunho",
  ENVIADO: "Enviado",
  ACEITO: "Aceito",
  RECUSADO: "Recusado",
};

export function statusBadgeClass(status: string): string {
  if (status === "ACEITO") {
    return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300";
  }
  if (status === "RECUSADO") {
    return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";
  }
  if (status === "ENVIADO") {
    return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
  }
  return "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300";
}

export function formatarObservacoesOrcamento(texto: string): string {
  const t = (texto || "").trim();
  if (!t) return "";
  if (t.includes("\n")) return t;
  return t
    .replace(/\s+(?=Dados do Cliente:)/gi, "\n")
    .replace(/\s+(?=Empresa:)/gi, "\n")
    .replace(/\s+(?=CPF\/CNPJ:)/gi, "\n")
    .replace(/\s+(?=E-mails?:)/gi, "\n")
    .replace(/\s+(?=Telefone:)/gi, "\n")
    .replace(/\s+(?=Endere[cç]o:)/gi, "\n")
    .replace(/\s+(?=LGPD)/g, "\n")
    .trim();
}
