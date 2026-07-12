/**
 * Acesso a campos bilíngues (PT/EN) da API Clínica da Beleza.
 * A API pode retornar name ou nome, phone ou telefone, etc.
 */

type BilingualName = { name?: string; nome?: string };
type BilingualPhone = { phone?: string | null; telefone?: string | null };
type BilingualActive = { active?: boolean; is_active?: boolean };
type BilingualBirthDate = { birth_date?: string | null; data_nascimento?: string | null };
type BilingualAddress = { address?: string | null; endereco?: string | null };
type BilingualNotes = { notes?: string | null; observacoes?: string | null };
type BilingualSpecialty = { specialty?: string; especialidade?: string };
type BilingualDescription = { description?: string | null; descricao?: string | null };
type BilingualPrice = { price?: string | number; preco?: string | number };
type BilingualDuration = { duration?: number; duracao_minutos?: number };

export function entityName(e: BilingualName): string {
  return e.name || e.nome || '';
}

/** Filtra pacientes por prefixo do nome, telefone, CPF ou e-mail conforme o usuário digita. */
export function matchesPatientSearchQuery(
  p: BilingualName & BilingualPhone & { cpf?: string | null; email?: string | null },
  rawQuery: string,
): boolean {
  const q = rawQuery.trim().toLowerCase();
  if (!q) return false;
  const nome = (entityName(p) || '').toLowerCase();
  const email = (p.email || '').toLowerCase();
  const qDigits = q.replace(/\D/g, '');
  const tel = (p.phone || p.telefone || '').replace(/\D/g, '');
  const cpf = (p.cpf || '').replace(/\D/g, '');
  if (q.includes('@')) return email.includes(q);
  const onlyDigits = qDigits.length > 0 && qDigits === q.replace(/\s/g, '');
  if (onlyDigits) {
    if (qDigits.length >= 3 && (tel.includes(qDigits) || cpf.includes(qDigits))) return true;
    return false;
  }
  if (nome.startsWith(q)) return true;
  if (qDigits.length >= 3 && (tel.includes(qDigits) || cpf.includes(qDigits))) return true;
  if (q.length >= 3 && email.includes(q)) return true;
  return false;
}

export function dedupePatientsById<T extends { id: number }>(rows: T[]): T[] {
  const seen = new Set<number>();
  const out: T[] = [];
  for (const row of rows) {
    if (seen.has(row.id)) continue;
    seen.add(row.id);
    out.push(row);
  }
  return out;
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
  return String(e.price ?? e.preco ?? '0');
}

export function procedureDuration(e: BilingualDuration): number {
  return e.duration ?? e.duracao_minutos ?? 30;
}

export function procedureCategoria(e: { categoria?: string }): string {
  return e.categoria || '';
}

/** Tipos compartilhados da API Clínica da Beleza (campos bilíngues PT/EN). */
export interface ClinicaProfessional {
  id: number;
  name?: string;
  nome?: string;
  specialty?: string;
  especialidade?: string;
  phone?: string | null;
  telefone?: string | null;
  email?: string | null;
  registro_profissional?: string | null;
  conselho?: string | null;
  conselho_uf?: string | null;
  cpf?: string | null;
  data_nascimento?: string | null;
  sexo?: string | null;
  active?: boolean;
  is_active?: boolean;
  is_administrador_vinculado?: boolean;
  is_owner?: boolean;
  is_profissional?: boolean;
  tempo_consulta_minutos?: number | null;
}

export interface ClinicaPatient {
  id: number;
  name?: string;
  nome?: string;
  phone?: string;
  telefone?: string;
  cpf?: string | null;
  convenio?: number | null;
  foto_url?: string | null;
}

export interface ClinicaProcedure {
  id: number;
  name?: string;
  nome?: string;
  duration?: number;
  duracao_minutos?: number;
  price?: string;
  preco?: string | number;
}

export interface HorarioTrabalhoRow {
  id: number;
  dia_semana: number;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio: string | null;
  intervalo_fim: string | null;
  ativo: boolean;
}

export interface BloqueioHorario {
  id: number;
  professional: number | null;
  professional_name: string | null;
  data_inicio: string;
  data_fim: string;
  motivo: string;
  observacoes: string | null;
  criado_em: string;
}
