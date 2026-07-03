export function buildProfissionaisBasePath(slug: string): string {
  return `/loja/${slug}/clinica-beleza/profissionais`;
}

export function extractProfissionalToggleError(err: unknown): string {
  const e = err as { error?: string; detail?: string };
  return e?.error || e?.detail || "Erro ao alterar status.";
}
