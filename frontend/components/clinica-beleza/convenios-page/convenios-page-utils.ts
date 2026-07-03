export function buildConveniosBasePath(slug: string): string {
  return `/loja/${slug}/clinica-beleza/convenios`;
}

export function isNovaConvenioQuery(searchParams: URLSearchParams): boolean {
  return searchParams.get("novo") === "1";
}

export function extractConvenioSaveError(e: unknown): string {
  return e instanceof Error ? e.message : "Erro ao criar convênio.";
}
