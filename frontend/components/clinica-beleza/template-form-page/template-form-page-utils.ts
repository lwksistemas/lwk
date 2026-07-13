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

export function extractTemplateSaveError(e: unknown): string {
  const obj = e && typeof e === "object" ? (e as Record<string, unknown>) : {};
  const msg =
    (Array.isArray(obj?.nome) ? obj.nome[0] : null) ||
    (Array.isArray(obj?.tipo) ? obj.tipo[0] : null) ||
    (Array.isArray(obj?.conteudo) ? obj.conteudo[0] : null) ||
    (typeof obj?.detail === "string" ? obj.detail : null) ||
    (typeof obj?.message === "string" ? obj.message : null) ||
    "Erro ao salvar template.";
  return typeof msg === "string" ? msg : JSON.stringify(msg);
}

export function extractTemplateLoadError(e: { detail?: string; message?: string }): string {
  const msg = e?.detail || e?.message || "Erro ao carregar template para edição.";
  return typeof msg === "string" ? msg : JSON.stringify(msg);
}
