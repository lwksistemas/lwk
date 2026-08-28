/** Rotas do hub e da ficha de prontuário — Clínica da Beleza. */

export function buildProntuarioHubPath(slug: string): string {
  return `/loja/${slug}/clinica-beleza/prontuario`;
}

export function buildProntuarioPacientePath(slug: string, patientId: number): string {
  return `/loja/${slug}/clinica-beleza/pacientes/${patientId}/prontuario`;
}

export function isProntuarioPacientePath(pathname: string, slug: string): boolean {
  return new RegExp(`^/loja/${slug}/clinica-beleza/pacientes/\\d+/prontuario$`).test(
    pathname.replace(/\/$/, ""),
  );
}
