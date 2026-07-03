import type { TemplateFormState } from "./template-form-page-types";

export function buildTemplatesListPath(slug: string): string {
  return `/loja/${slug}/clinica-beleza/templates`;
}

export function parseTemplateEditId(editId: string | null): number | null {
  if (!editId) return null;
  const id = Number(editId);
  return Number.isNaN(id) ? null : id;
}

export function validateTemplateForm(form: TemplateFormState): string | null {
  if (!form.nome.trim()) return "Nome é obrigatório.";
  if (!form.conteudo.trim()) return "Conteúdo é obrigatório.";
  return null;
}

export function extractTemplateSaveError(e: Record<string, unknown>): string {
  const msg =
    (Array.isArray(e?.nome) ? e.nome[0] : null) ||
    (Array.isArray(e?.tipo) ? e.tipo[0] : null) ||
    (Array.isArray(e?.conteudo) ? e.conteudo[0] : null) ||
    (typeof e?.detail === "string" ? e.detail : null) ||
    (typeof e?.message === "string" ? e.message : null) ||
    "Erro ao salvar template.";
  return typeof msg === "string" ? msg : JSON.stringify(msg);
}

export function extractTemplateLoadError(e: { detail?: string; message?: string }): string {
  const msg = e?.detail || e?.message || "Erro ao carregar template para edição.";
  return typeof msg === "string" ? msg : JSON.stringify(msg);
}
