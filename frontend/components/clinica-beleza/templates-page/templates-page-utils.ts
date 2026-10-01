import { DOCUMENTO_TIPO_LABEL, type DocumentoTipo } from "../consultas/documentos/documentos-types";

export const TEMPLATE_TIPO_OPTIONS = (
  Object.entries(DOCUMENTO_TIPO_LABEL) as [DocumentoTipo, string][]
).map(([value, label]) => ({ value, label }));

export const TEMPLATE_FILTER_TIPO_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Todos os tipos" },
  ...TEMPLATE_TIPO_OPTIONS,
];

export function buildTemplateNovoPath(slug: string, templateId?: number): string {
  const base = `/loja/${slug}/clinica-beleza/templates/novo`;
  return templateId ? `${base}?id=${templateId}` : base;
}

export function templateTipoLabel(tipo: string): string {
  const found = TEMPLATE_FILTER_TIPO_OPTIONS.find((o) => o.value === tipo);
  return found?.label ?? tipo;
}

export function formatTemplateUpdatedAt(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch {
    return dateStr;
  }
}
