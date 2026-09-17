/** Rotas do hub e da ficha de prontuário — Clínica da Beleza. */

export function buildProntuarioHubPath(slug: string): string {
  return `/loja/${slug}/clinica-beleza/prontuario`;
}

export function buildProntuarioPacientePath(slug: string, patientId: number): string {
  return `/loja/${slug}/clinica-beleza/pacientes/${patientId}/prontuario`;
}

/** Link da ficha a partir do id do paciente no evento da agenda; null se não der para abrir. */
export function buildProntuarioAgendamentoPath(
  slug: string | undefined | null,
  patientId: unknown,
): string | null {
  const id = Number(patientId);
  if (!slug || !Number.isFinite(id) || id <= 0) return null;
  return buildProntuarioPacientePath(slug, id);
}

export function isProntuarioPacientePath(pathname: string, slug: string): boolean {
  return new RegExp(`^/loja/${slug}/clinica-beleza/pacientes/\\d+/prontuario$`).test(
    pathname.replace(/\/$/, ""),
  );
}
