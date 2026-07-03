export interface CampanhaResumo {
  id: number;
  titulo: string;
}

export interface PacienteCampanha {
  id: number;
  name?: string;
  nome?: string;
  phone?: string;
  telefone?: string;
  allow_whatsapp?: boolean;
  is_active?: boolean;
}

export type ModoEnvioCampanha = "todos" | "segmentacao";

export function pacienteCampanhaTelefone(p: PacienteCampanha): string {
  return (p.telefone || p.phone || "").trim();
}

export function pacienteCampanhaElegivel(p: PacienteCampanha): boolean {
  if (p.is_active === false) return false;
  if (p.allow_whatsapp === false) return false;
  return !!pacienteCampanhaTelefone(p);
}

export function buildCampanhaDestinoLabel(modo: ModoEnvioCampanha, elegiveisCount: number, selectedCount: number): string {
  return modo === "todos"
    ? `${elegiveisCount} paciente(s) com WhatsApp ativo`
    : `${selectedCount} selecionado(s)`;
}
