export const TEMPLATE_FILTER_TIPO_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Todos os tipos" },
  { value: "receituario", label: "Receituário" },
  { value: "pedido_exame", label: "Pedido de Exame" },
  { value: "atestado", label: "Atestado" },
  { value: "documento_personalizado", label: "Documento Personalizado" },
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
