export function patientSearchRank(nome: string, search: string): number {
  const n = (nome || "").toLocaleLowerCase("pt-BR");
  const s = (search || "").trim().toLocaleLowerCase("pt-BR");
  if (!s) return 99;
  if (n.startsWith(s)) return 0;
  if (n.includes(` ${s}`)) return 1;
  return 2;
}

export function sortPatientSearchResults<T extends { nome?: string; name?: string }>(
  rows: T[],
  search: string,
): T[] {
  const q = search.trim();
  return [...rows].sort((a, b) => {
    const na = a.nome || a.name || "";
    const nb = b.nome || b.name || "";
    const ra = patientSearchRank(na, q);
    const rb = patientSearchRank(nb, q);
    if (ra !== rb) return ra - rb;
    return na.localeCompare(nb, "pt-BR");
  });
}

export function splitPatientMatch(text: string, query: string): { text: string; hit: boolean }[] {
  const q = query.trim();
  if (!q || !text) return [{ text, hit: false }];
  const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp(`(${escaped})`, "ig");
  const parts = text.split(re).filter((p) => p.length > 0);
  const needle = q.toLocaleLowerCase("pt-BR");
  return parts.map((part) => ({
    text: part,
    hit: part.toLocaleLowerCase("pt-BR") === needle,
  }));
}

export function isLocalizarPainelExpandido(query: string): boolean {
  return query.trim().length >= 1;
}
