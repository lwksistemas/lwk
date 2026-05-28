/**
 * Acesso a campos bilíngues (PT/EN) da API Clínica da Beleza.
 * A API pode retornar name ou nome, phone ou telefone, etc.
 */

type BilingualName = { name?: string; nome?: string };
type BilingualPhone = { phone?: string; telefone?: string | null };
type BilingualActive = { active?: boolean; is_active?: boolean };
type BilingualBirthDate = { birth_date?: string | null; data_nascimento?: string | null };
type BilingualAddress = { address?: string | null; endereco?: string | null };
type BilingualNotes = { notes?: string | null; observacoes?: string | null };
type BilingualSpecialty = { specialty?: string; especialidade?: string };
type BilingualDescription = { description?: string | null; descricao?: string | null };
type BilingualPrice = { price?: string; preco?: string };
type BilingualDuration = { duration?: number; duracao_minutos?: number };

export function entityName(e: BilingualName): string {
  return e.name || e.nome || '';
}

export function entityPhone(e: BilingualPhone): string {
  return e.phone || e.telefone || '';
}

export function entityEmail(e: { email?: string | null }): string | null {
  return e.email ?? null;
}

export function entityActive(e: BilingualActive): boolean {
  return e.active ?? e.is_active ?? true;
}

export function patientCpf(e: { cpf?: string | null }): string | null {
  return e.cpf ?? null;
}

export function patientBirthDate(e: BilingualBirthDate): string | null {
  return e.birth_date ?? e.data_nascimento ?? null;
}

export function patientAddress(e: BilingualAddress): string | null {
  return e.address ?? e.endereco ?? null;
}

export function patientNotes(e: BilingualNotes): string | null {
  return e.notes ?? e.observacoes ?? null;
}

export function professionalSpecialty(e: BilingualSpecialty): string {
  return e.specialty || e.especialidade || '';
}

export function procedureDescription(e: BilingualDescription): string | null {
  return e.description ?? e.descricao ?? null;
}

export function procedurePrice(e: BilingualPrice): string {
  return e.price || e.preco || '0';
}

export function procedureDuration(e: BilingualDuration): number {
  return e.duration ?? e.duracao_minutos ?? 30;
}

export function procedureCategoria(e: { categoria?: string }): string {
  return e.categoria || '';
}
