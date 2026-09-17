/** Recusa de negócio (validação) não deve ir ao painel de erro do suporte. */
const STATUS_REJEICAO_NEGOCIO = new Set([400, 422]);

export function deveReportarErroApiParaSuporte(status: number, path: string): boolean {
  if (status < 400) return false;
  if (status === 401 || status === 429) return false;
  if (STATUS_REJEICAO_NEGOCIO.has(status)) return false;

  const pathNorm = path.startsWith("/") ? path : `/${path}`;
  const memedTokenEstadoEsperado =
    (status === 404 || status === 409) && pathNorm.startsWith("/memed/token");
  if (memedTokenEstadoEsperado) return false;

  return true;
}
